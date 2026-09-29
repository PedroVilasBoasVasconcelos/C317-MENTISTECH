from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.company import Company
from app.repositories.base_repository import BaseRepository


class CompanyRepository(BaseRepository[Company]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Company)

    def create(self, *, trade_name: str, cnpj: str) -> Company:
        company = Company(trade_name=trade_name, cnpj=cnpj)
        return self.add(company)

    def get_by_cnpj(self, cnpj: str) -> Company | None:
        stmt = select(Company).where(Company.cnpj == cnpj)
        return self.db.scalar(stmt)

    def update_company(
        self,
        company: Company,
        *,
        trade_name: str | None = None,
        cnpj: str | None = None,
    ) -> Company:
        return self.update(company, trade_name=trade_name, cnpj=cnpj)
