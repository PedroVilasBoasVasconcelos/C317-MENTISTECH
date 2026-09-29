from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.database import SessionLocal
from app.db.models import Team, User


def main() -> None:
    db = SessionLocal()
    try:
        updated = 0
        users = db.query(User).filter(User.team_id.is_(None)).all()
        teams_by_company: dict[int, Team] = {}

        for user in users:
            if user.company_id not in teams_by_company:
                teams_by_company[user.company_id] = _get_or_create_team(
                    db,
                    user.company_id,
                    "Sem time",
                )

            user.team_id = teams_by_company[user.company_id].id
            updated += 1

        db.commit()
        print(f"Backfill de times finalizado. Usuarios atualizados: {updated}")
    finally:
        db.close()


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
