import json
import unicodedata
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Security, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user_bearer, get_db
from app.db.models.checkin import CheckIn
from app.db.models.team import Team
from app.db.models.user import User
from app.services.trend_ai_service import mood_from_score

analytics_router = APIRouter(prefix="/analytics", tags=["analytics"])


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    without_accents = "".join(
        char for char in normalized if not unicodedata.combining(char)
    )
    return without_accents.lower().strip()


def is_psychologist(user: User) -> bool:
    role = normalize_text(user.role)
    return "psicolog" in role or "pscolog" in role or "psicoloc" in role


def classify_team_trend(delta: float | None) -> tuple[str, float]:
    if delta is None or abs(delta) <= 3:
        return "estabilidade", 0.72 if delta is not None else 0.55

    confidence = min(0.94, 0.62 + abs(delta) / 50)
    if delta > 0:
        return "melhora", confidence

    return "piora", confidence


def build_team_trend_summary(
    *,
    team: str,
    users_count: int,
    checkins: list[CheckIn],
) -> dict[str, object]:
    if not checkins:
        return {
            "overall_mood": "Sem dados",
            "stress_level": None,
            "ai_insights": f"Sem check-ins suficientes para analisar o time {team}.",
        }

    monthly_scores: dict[str, list[int]] = defaultdict(list)
    for checkin in checkins:
        reference_date = checkin.submitted_at or checkin.created_at
        month_key = reference_date.strftime("%Y-%m")
        monthly_scores[month_key].append(checkin.stress_level)

    monthly_averages = [
        {
            "month": month,
            "score": sum(scores) / len(scores),
            "checkins": len(scores),
        }
        for month, scores in sorted(monthly_scores.items())
    ]
    latest_period = monthly_averages[-1]
    previous_period = monthly_averages[-2] if len(monthly_averages) >= 2 else None
    latest_score = round(latest_period["score"])
    previous_score = round(previous_period["score"]) if previous_period else None
    delta = latest_score - previous_score if previous_score is not None else None
    trend, confidence = classify_team_trend(delta)
    signal = "+" if delta is not None and delta > 0 else ""

    parts = [
        f"Tendencia de {trend} do time detectada pela IA "
        f"(confianca {round(confidence * 100)}%).",
        f"Pontuacao media atual do time: {latest_score}/100.",
    ]

    if delta is None:
        parts.append(
            "Ainda nao ha periodo anterior suficiente para comparar a evolucao do time."
        )
    else:
        parts.append(
            f"Variacao em relacao ao periodo anterior: {signal}{delta} pontos "
            f"(anterior: {previous_score}/100)."
        )

    parts.append(
        f"Analise baseada em {len(checkins)} check-ins de {users_count} pessoa(s)."
    )

    return {
        "overall_mood": mood_from_score(latest_score),
        "stress_level": latest_score,
        "ai_insights": " ".join(parts),
    }


@analytics_router.get("/stress-level-by-user-monthly/{user_id}")
def stress_level_by_user_monthly(user_id: int, db: Session = Depends(get_db)):
    result = (
        db.query(
            func.strftime("%Y-%m", CheckIn.created_at).label("month"),
            func.avg(CheckIn.stress_level).label("average_stress"),
        )
        .filter(CheckIn.user_id == user_id)
        .group_by("month")
        .all()
    )

    return [
        {"month": checkin.month, "average_stress": checkin.average_stress}
        for checkin in result
    ]


@analytics_router.get("/stress-level/user/{user_id}")
def stress_level_by_user(user_id: int, db: Session = Depends(get_db)):
    result = db.query(CheckIn).filter(CheckIn.user_id == user_id).all()

    return [checkin.stress_level for checkin in result]


@analytics_router.get("/stress-level/role/{role}")
def stress_level_by_role(role: str, db: Session = Depends(get_db)):
    result = (
        db.query(func.avg(CheckIn.stress_level))
        .join(User, CheckIn.user_id == User.id)
        .filter(User.role == role)
        .scalar()
    )

    return {"role": role, "average_stress": result}


@analytics_router.get("/stress-level/team/{team}")
def stress_level_by_team(team: str, db: Session = Depends(get_db)):
    result = (
        db.query(func.avg(CheckIn.stress_level))
        .join(User, CheckIn.user_id == User.id)
        .join(Team, User.team_id == Team.id)
        .filter(Team.name == team)
        .scalar()
    )

    return {"team": team, "average_stress": result}


@analytics_router.get("/mood-by-team/{team}")
def mood_by_team(team: str, db: Session = Depends(get_db)):
    result = (
        db.query(CheckIn.overall_mood, func.count(CheckIn.id).label("count"))
        .join(User, CheckIn.user_id == User.id)
        .join(Team, User.team_id == Team.id)
        .filter(Team.name == team)
        .group_by(CheckIn.overall_mood)
        .all()
    )

    return [{"mood": row.overall_mood, "count": row.count} for row in result]


@analytics_router.get("/mood-by-role/{role}")
def mood_by_role(role: str, db: Session = Depends(get_db)):
    result = (
        db.query(CheckIn.overall_mood, func.count(CheckIn.id).label("count"))
        .join(User, CheckIn.user_id == User.id)
        .filter(User.role == role)
        .group_by(CheckIn.overall_mood)
        .all()
    )

    return [{"mood": row.overall_mood, "count": row.count} for row in result]


@analytics_router.get("/company-overview")
def company_overview(
    db: Session = Depends(get_db),
    current_user: User = Security(get_current_user_bearer, scopes=[]),
):
    if not is_psychologist(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Dashboard geral disponivel apenas para psicologos.",
        )

    users = (
        db.query(User)
        .filter(User.company_id == current_user.company_id)
        .order_by(User.full_name.asc())
        .all()
    )
    user_ids = [user.id for user in users]

    if not user_ids:
        return {
            "total_users": 0,
            "total_checkins": 0,
            "average_stress": None,
            "mood_distribution": [],
            "groups": [],
            "users": [],
        }

    checkins = (
        db.query(CheckIn)
        .filter(CheckIn.user_id.in_(user_ids))
        .order_by(CheckIn.created_at.desc())
        .all()
    )

    checkins_by_user: dict[int, list[CheckIn]] = defaultdict(list)
    mood_counts: dict[str, int] = defaultdict(int)
    group_stats: dict[str, dict[str, object]] = {}
    total_stress = 0

    users_by_id = {user.id: user for user in users}

    for checkin in checkins:
        user = users_by_id.get(checkin.user_id)

        if user is None:
            continue

        team = user.team
        group = team.name if team else "Sem time"
        group_stats.setdefault(
            group,
            {
                "team_id": team.id if team else None,
                "group": group,
                "users": set(),
                "checkins": 0,
                "stress_total": 0,
            },
        )

        checkins_by_user[checkin.user_id].append(checkin)
        mood_counts[checkin.overall_mood] += 1
        total_stress += checkin.stress_level
        group_stats[group]["users"].add(user.id)
        group_stats[group]["checkins"] += 1
        group_stats[group]["stress_total"] += checkin.stress_level

    groups = []
    for stats in group_stats.values():
        checkin_count = int(stats["checkins"])
        stress_total = int(stats["stress_total"])
        groups.append(
            {
                "team_id": stats["team_id"],
                "group": stats["group"],
                "users": len(stats["users"]),
                "checkins": checkin_count,
                "average_stress": round(stress_total / checkin_count, 2)
                if checkin_count
                else None,
            }
        )

    user_rows = []
    for user in users:
        user_checkins = checkins_by_user.get(user.id, [])
        latest_checkin = user_checkins[0] if user_checkins else None
        user_rows.append(
            {
                "id": user.id,
                "name": user.full_name,
                "role": user.role,
                "team_id": user.team_id,
                "team": user.team.name if user.team else None,
                "checkins": len(user_checkins),
                "last_mood": latest_checkin.overall_mood if latest_checkin else None,
                "last_stress": latest_checkin.stress_level if latest_checkin else None,
            }
        )

    return {
        "total_users": len(users),
        "total_checkins": len(checkins),
        "average_stress": round(total_stress / len(checkins), 2)
        if checkins
        else None,
        "mood_distribution": [
            {"mood": mood, "count": count}
            for mood, count in sorted(
                mood_counts.items(),
                key=lambda item: item[1],
                reverse=True,
            )
        ],
        "groups": sorted(groups, key=lambda item: item["group"]),
        "users": user_rows,
    }


@analytics_router.get("/team-history/{team_id}")
def team_history(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Security(get_current_user_bearer, scopes=[]),
):
    if not is_psychologist(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Dashboard por time disponivel apenas para psicologos.",
        )

    team = (
        db.query(Team)
        .filter(
            Team.id == team_id,
            Team.company_id == current_user.company_id,
        )
        .one_or_none()
    )

    if team is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Time nao encontrado nesta empresa.",
        )

    team_users = (
        db.query(User)
        .filter(
            User.company_id == current_user.company_id,
            User.team_id == team.id,
        )
        .order_by(User.full_name.asc())
        .all()
    )
    user_ids = [user.id for user in team_users]
    checkins = (
        db.query(CheckIn)
        .filter(CheckIn.user_id.in_(user_ids))
        .order_by(CheckIn.submitted_at.asc(), CheckIn.created_at.asc())
        .all()
    )
    users_by_id = {user.id: user for user in team_users}
    trend = build_team_trend_summary(
        team=team.name,
        users_count=len(team_users),
        checkins=checkins,
    )

    return {
        "team_id": team.id,
        "team": team.name,
        "users_count": len(team_users),
        "checkins_count": len(checkins),
        "trend": trend,
        "checkins": [
            {
                "id": checkin.id,
                "created_at": checkin.submitted_at or checkin.created_at,
                "overall_mood": checkin.overall_mood,
                "stress_level": checkin.stress_level,
                "ai_insights": checkin.ai_insights,
                "answers": checkin.answers_json,
                "user_id": checkin.user_id,
                "user_name": users_by_id[checkin.user_id].full_name,
            }
            for checkin in checkins
        ],
    }


@analytics_router.get("/questions-average")
def questions_average(db: Session = Depends(get_db)):
    with open("app/db/questions.json", "r", encoding="utf-8") as file:
        questions_data = json.load(file)

    questions_map = {
        question["id"]: question["question"] for question in questions_data
    }

    checkins = db.query(CheckIn.answers_json).all()
    questions = defaultdict(list)

    for checkin in checkins:
        for answer in checkin.answers_json:
            questions[answer["question_id"]].append(answer["value"])

    return [
        {
            "question_id": question_id,
            "question": questions_map.get(question_id),
            "average": round(sum(values) / len(values), 2),
        }
        for question_id, values in questions.items()
    ]
