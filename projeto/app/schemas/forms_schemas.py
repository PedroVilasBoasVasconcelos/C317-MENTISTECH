from datetime import datetime
from typing import List, Union

from pydantic import BaseModel

class Answer(BaseModel):
    question_id: int
    value: Union[int, str]

class AnswerRequest(BaseModel):
    user_id: int
    answers: List[Answer]
    created_at: datetime | None = None