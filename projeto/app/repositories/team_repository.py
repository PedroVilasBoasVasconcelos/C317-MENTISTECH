from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.team import Team
from app.repositories.base_repository import BaseRepository


class TeamRepository(BaseRepository[Team]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Team)

    def create(self, *, company_id: int, name: str) -> Team:
        team = Team(company_id=company_id, name=name)
        return self.add(team)

    def get_by_company_and_name(self, company_id: int, name: str) -> Team | None:
        normalized_name = name.strip()
        stmt = select(Team).where(
            Team.company_id == company_id,
            Team.name == normalized_name,
        )
        return self.db.scalar(stmt)

    def get_or_create(self, *, company_id: int, name: str) -> Team:
        normalized_name = name.strip() or "Sem time"
        team = self.get_by_company_and_name(company_id, normalized_name)

        if team is not None:
            return team

        return self.create(company_id=company_id, name=normalized_name)
