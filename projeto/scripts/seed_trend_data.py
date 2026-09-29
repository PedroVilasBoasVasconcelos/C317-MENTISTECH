from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.database import SessionLocal, engine
from app.core.security import get_password_hash
from app.db.base import Base
from app.db.models import CheckIn, Company, Team, User
from app.services.trend_ai_service import TrendAIService, mood_from_score

SEED_COMPANY_CNPJ = "00.000.000/0000-00"
SEED_COMPANY_NAME = "Empresa MVP"
SEED_PASSWORD = "123456"

CHECKIN_DATES = [
    datetime(2025, 9, 24, 9, 0),
    datetime(2025, 10, 24, 9, 0),
    datetime(2025, 11, 24, 9, 0),
    datetime(2025, 12, 22, 9, 0),
    datetime(2026, 1, 26, 9, 0),
    datetime(2026, 2, 23, 9, 0),
    datetime(2026, 3, 23, 9, 0),
    datetime(2026, 4, 24, 9, 0),
]

PROFILES = [
    {
        "name": "Helena Rocha",
        "email": "helena.psicologa@mentistech.com.br",
        "old_email": "helena.psicologa@mentistech.local",
        "role": "Psicologa",
        "team": "Psicologia",
        "answers": [
            [1, 5, 1, 4, 4, 4, 4, 4, 4, 4],
            [1, 5, 1, 4, 4, 4, 4, 4, 4, 4],
            [2, 4, 1, 4, 4, 4, 4, 4, 4, 4],
            [1, 5, 1, 5, 4, 4, 5, 4, 4, 5],
            [1, 5, 1, 5, 5, 4, 5, 5, 4, 5],
            [1, 5, 1, 5, 5, 5, 5, 5, 4, 5],
            [1, 5, 1, 5, 5, 5, 5, 5, 5, 5],
            [1, 5, 1, 5, 5, 5, 5, 5, 5, 5],
        ],
    },
    {
        "name": "Ana Costa",
        "email": "ana.costa@mentistech.com.br",
        "old_email": "ana.costa@mentistech.local",
        "role": "Analista de Produto",
        "team": "Produto",
        "answers": [
            [5, 2, 4, 2, 2, 2, 2, 2, 2, 2],
            [4, 2, 4, 3, 2, 3, 3, 2, 2, 3],
            [3, 3, 3, 3, 3, 3, 3, 3, 3, 3],
            [2, 4, 2, 4, 4, 4, 4, 4, 4, 4],
            [1, 5, 1, 5, 5, 4, 5, 4, 5, 5],
            [2, 4, 2, 4, 4, 4, 4, 4, 5, 4],
            [2, 4, 2, 4, 4, 5, 4, 4, 4, 4],
            [1, 5, 1, 5, 4, 5, 5, 4, 5, 5],
        ],
    },
    {
        "name": "Bruno Silva",
        "email": "bruno.silva@mentistech.com.br",
        "old_email": "bruno.silva@mentistech.local",
        "role": "Executivo Comercial",
        "team": "Comercial",
        "answers": [
            [1, 5, 1, 5, 5, 4, 5, 5, 5, 5],
            [2, 4, 2, 4, 4, 4, 4, 4, 4, 4],
            [3, 3, 3, 3, 3, 3, 3, 3, 3, 3],
            [4, 2, 4, 2, 3, 2, 3, 2, 2, 3],
            [5, 1, 5, 2, 2, 2, 2, 1, 2, 2],
            [4, 2, 4, 2, 2, 2, 2, 2, 2, 2],
            [5, 1, 4, 2, 2, 1, 2, 1, 2, 2],
            [5, 1, 5, 1, 2, 1, 2, 1, 1, 2],
        ],
    },
    {
        "name": "Carla Mendes",
        "email": "carla.mendes@mentistech.com.br",
        "old_email": "carla.mendes@mentistech.local",
        "role": "Desenvolvedora",
        "team": "Engenharia",
        "answers": [
            [2, 4, 2, 4, 4, 4, 4, 3, 4, 4],
            [2, 4, 2, 4, 4, 4, 4, 4, 4, 4],
            [2, 4, 2, 4, 3, 4, 4, 4, 4, 4],
            [2, 4, 2, 4, 4, 3, 4, 4, 4, 4],
            [2, 4, 2, 4, 4, 4, 4, 4, 4, 4],
            [2, 4, 2, 4, 4, 4, 5, 4, 4, 4],
            [2, 5, 2, 5, 4, 4, 5, 4, 5, 5],
            [1, 5, 1, 5, 5, 5, 5, 5, 5, 5],
        ],
    },
    {
        "name": "Diego Almeida",
        "email": "diego.almeida@mentistech.com.br",
        "old_email": "diego.almeida@mentistech.local",
        "role": "Designer UX",
        "team": "Produto",
        "answers": [
            [3, 3, 3, 4, 3, 4, 4, 3, 4, 4],
            [2, 4, 2, 4, 4, 4, 4, 4, 4, 4],
            [2, 4, 2, 5, 4, 4, 5, 4, 4, 5],
            [3, 3, 3, 4, 3, 4, 4, 3, 4, 4],
            [4, 2, 3, 3, 3, 3, 3, 2, 3, 3],
            [3, 3, 3, 4, 3, 4, 4, 3, 4, 4],
            [2, 4, 2, 4, 4, 4, 4, 4, 4, 4],
            [2, 5, 2, 5, 4, 4, 5, 4, 5, 5],
        ],
    },
    {
        "name": "Fernanda Lima",
        "email": "fernanda.lima@mentistech.com.br",
        "old_email": "fernanda.lima@mentistech.local",
        "role": "People Partner",
        "team": "Pessoas",
        "answers": [
            [2, 4, 2, 4, 4, 5, 4, 4, 4, 4],
            [2, 4, 2, 4, 4, 4, 4, 4, 4, 4],
            [2, 5, 2, 5, 5, 5, 5, 4, 5, 5],
            [1, 5, 1, 5, 5, 5, 5, 5, 5, 5],
            [2, 4, 2, 4, 4, 4, 5, 4, 4, 5],
            [2, 4, 2, 4, 4, 4, 4, 4, 4, 4],
            [3, 3, 2, 4, 4, 4, 4, 3, 4, 4],
            [2, 4, 2, 5, 4, 5, 5, 4, 5, 5],
        ],
    },
    {
        "name": "Gabriel Torres",
        "email": "gabriel.torres@mentistech.com.br",
        "old_email": "gabriel.torres@mentistech.local",
        "role": "QA Engineer",
        "team": "Engenharia",
        "answers": [
            [4, 2, 4, 3, 3, 3, 3, 2, 3, 3],
            [4, 2, 4, 3, 2, 3, 3, 2, 3, 3],
            [5, 2, 4, 2, 2, 2, 2, 2, 2, 2],
            [5, 1, 5, 2, 2, 2, 2, 1, 2, 2],
            [4, 2, 4, 3, 3, 3, 3, 2, 3, 3],
            [3, 3, 3, 3, 3, 3, 3, 3, 3, 3],
            [2, 4, 2, 4, 4, 4, 4, 4, 4, 4],
            [2, 4, 2, 4, 4, 4, 5, 4, 4, 4],
        ],
    },
    {
        "name": "Isabela Nunes",
        "email": "isabela.nunes@mentistech.com.br",
        "old_email": "isabela.nunes@mentistech.local",
        "role": "Customer Success",
        "team": "Comercial",
        "answers": [
            [3, 3, 3, 3, 4, 3, 4, 3, 4, 4],
            [3, 4, 3, 4, 4, 4, 4, 3, 4, 4],
            [2, 4, 2, 4, 4, 4, 4, 4, 4, 4],
            [2, 5, 2, 5, 4, 5, 5, 4, 5, 5],
            [2, 4, 2, 4, 4, 4, 5, 4, 4, 4],
            [3, 3, 3, 3, 3, 3, 4, 3, 3, 4],
            [4, 2, 4, 3, 3, 3, 3, 2, 3, 3],
            [3, 3, 3, 4, 3, 4, 4, 3, 4, 4],
        ],
    },
]


def main() -> None:
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        company = (
            db.query(Company)
            .filter(Company.cnpj == SEED_COMPANY_CNPJ)
            .one_or_none()
        )
        if company is None:
            company = Company(
                trade_name=SEED_COMPANY_NAME,
                cnpj=SEED_COMPANY_CNPJ,
            )
            db.add(company)
            db.commit()
            db.refresh(company)

        users = []
        for profile in PROFILES:
            team = _get_or_create_team(db, company.id, profile["team"])
            email_candidates = [profile["email"], profile.get("old_email")]
            email_candidates = [email for email in email_candidates if email]
            user = (
                db.query(User)
                .filter(User.corporate_email.in_(email_candidates))
                .one_or_none()
            )
            if user is None:
                user = User(
                    company_id=company.id,
                    team_id=team.id,
                    full_name=profile["name"],
                    corporate_email=profile["email"],
                    role=profile["role"],
                    password_hash=get_password_hash(SEED_PASSWORD),
                )
                db.add(user)
            else:
                user.company_id = company.id
                user.team_id = team.id
                user.full_name = profile["name"]
                user.corporate_email = profile["email"]
                user.role = profile["role"]
                user.password_hash = get_password_hash(SEED_PASSWORD)

            users.append(user)

        db.commit()
        for user in users:
            db.refresh(user)

        seed_user_ids = [user.id for user in users]
        (
            db.query(CheckIn)
            .filter(CheckIn.user_id.in_(seed_user_ids))
            .delete(synchronize_session=False)
        )
        db.commit()

        users_by_email = {user.corporate_email: user for user in users}
        for profile in PROFILES:
            user = users_by_email[profile["email"]]
            for submitted_at, answer_values in zip(CHECKIN_DATES, profile["answers"]):
                answers = _answers_from_values(answer_values)
                prediction = TrendAIService(db).predict(
                    user_id=user.id,
                    current_answers=answers,
                )
                checkin = CheckIn(
                    user_id=user.id,
                    submitted_at=submitted_at,
                    overall_mood=mood_from_score(prediction.wellbeing_score),
                    answers_json=answers,
                    stress_level=prediction.wellbeing_score,
                    ai_insights=prediction.summary,
                    created_at=submitted_at,
                    updated_at=submitted_at,
                )
                db.add(checkin)
                db.commit()

        print("Seed finalizado.")
        print(f"Senha das contas demo: {SEED_PASSWORD}")
        for user in users:
            latest = (
                db.query(CheckIn)
                .filter(CheckIn.user_id == user.id)
                .order_by(CheckIn.created_at.desc())
                .first()
            )
            print(
                f"- {user.id}: {user.full_name} | {user.corporate_email} | "
                f"{user.role} | time {user.team.name if user.team else '-'} | "
                f"ultimo score {latest.stress_level if latest else '-'}"
            )

    finally:
        db.close()


def _answers_from_values(values: list[int]) -> list[dict[str, int]]:
    return [
        {"question_id": question_id, "value": value}
        for question_id, value in enumerate(values, start=1)
    ]


def _get_or_create_team(db, company_id: int, name: str) -> Team:
    team = (
        db.query(Team)
        .filter(
            Team.company_id == company_id,
            Team.name == name,
        )
        .one_or_none()
    )

    if team is not None:
        return team

    team = Team(company_id=company_id, name=name)
    db.add(team)
    db.commit()
    db.refresh(team)
    return team


if __name__ == "__main__":
    main()
