from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash, verify_password
from app.db.models.user import User
from app.repositories.company_repository import CompanyRepository
from app.repositories.team_repository import TeamRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth_schemas import RegisterRequest

DEFAULT_COMPANY_CNPJ = "00.000.000/0000-00"
DEFAULT_COMPANY_TRADE_NAME = "Empresa MVP"
DEFAULT_USER_ROLE = "Colaborador"


class EmailAlreadyRegisteredError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class AuthService:
    def __init__(self, db: Session) -> None:
        self.company_repository = CompanyRepository(db)
        self.team_repository = TeamRepository(db)
        self.user_repository = UserRepository(db)

    def register(self, request: RegisterRequest) -> User:
        email = request.email.lower()

        if self.user_repository.get_by_email(email) is not None:
            raise EmailAlreadyRegisteredError

        company = self.company_repository.get_by_cnpj(DEFAULT_COMPANY_CNPJ)
        if company is None:
            company = self.company_repository.create(
                trade_name=DEFAULT_COMPANY_TRADE_NAME,
                cnpj=DEFAULT_COMPANY_CNPJ,
            )

        team = self.team_repository.get_or_create(
            company_id=company.id,
            name=request.team.strip() or "Sem time",
        )

        return self.user_repository.create(
            company_id=company.id,
            team_id=team.id,
            full_name=request.name.strip(),
            corporate_email=email,
            role=request.role.strip(),
            password_hash=get_password_hash(request.password),
        )

    def login(self, email: str, password: str) -> tuple[str, int]:
        user = self.user_repository.get_by_email(email.lower())

        if user is None or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError

        return create_access_token(
            subject=str(user.id),
            email=user.corporate_email,
        )
