from pydantic import BaseModel, EmailStr, field_validator

class EmailRequest(BaseModel):
    subject: str
    user_id: int
    user_name: str
    user_email: EmailStr
    email_to: EmailStr
    message: str

    @field_validator("subject", "user_name", "message")
    @classmethod
    def strip_text_fields(cls, value: str) -> str:
        return value.strip()
