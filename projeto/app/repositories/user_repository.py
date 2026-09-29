from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.user import User
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, User)

    def create(
        self,
        *,
        company_id: int,
        team_id: int | None,
        full_name: str,
        corporate_email: str,
        role: str,
        password_hash: str,
    ) -> User:
        user = User(
            company_id=company_id,
            team_id=team_id,
            full_name=full_name,
            corporate_email=corporate_email,
            role=role,
            password_hash=password_hash,
        )
        return self.add(user)

    def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.corporate_email == email)
        return self.db.scalar(stmt)

    def list_by_company(
        self,
        company_id: int,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> list[User]:
        stmt = (
            select(User)
            .where(User.company_id == company_id)
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def update_user(
        self,
        user: User,
        *,
        full_name: str | None = None,
        role: str | None = None,
        password_hash: str | None = None,
    ) -> User:
        return self.update(
            user,
            full_name=full_name,
            role=role,
            password_hash=password_hash,
        )
