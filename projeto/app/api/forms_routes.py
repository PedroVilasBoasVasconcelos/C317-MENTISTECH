import json
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.db.models.checkin import CheckIn
from app.schemas.forms_schemas import AnswerRequest
from app.services.trend_ai_service import TrendAIService, mood_from_score

forms_router = APIRouter(prefix="/forms", tags=["forms"])


@forms_router.get("/questions")
def get_questions():
    with open("app/db/questions.json", "r", encoding="utf-8") as file:
        return json.load(file)


@forms_router.post("/submit", status_code=status.HTTP_201_CREATED)
def submit_form(data: AnswerRequest, db: Session = Depends(get_db)):
    try:
        trend_prediction = TrendAIService(db).predict(
            user_id=data.user_id,
            current_answers=data.answers,
        )

        checkin = CheckIn(
            user_id=data.user_id,
            overall_mood=mood_from_score(trend_prediction.wellbeing_score),
            answers_json=[answer.model_dump() for answer in data.answers],
            stress_level=trend_prediction.wellbeing_score,
            ai_insights=trend_prediction.summary,
            submitted_at=data.created_at or datetime.utcnow(),
        )

        db.add(checkin)
        db.commit()
        db.refresh(checkin)

        return {"message": "Formulario enviado com sucesso", "data": checkin}

    except SQLAlchemyError as e:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}",
        )

    except Exception as e:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}",
        )


@forms_router.get("/history/{user_id}")
def history_by_user(user_id: int, db: Session = Depends(get_db)):
    try:
        checkins = (
            db.query(CheckIn)
            .filter(CheckIn.user_id == user_id)
            .order_by(CheckIn.created_at.desc())
            .all()
        )

        return [
            {
                "id": checkin.id,
                "created_at": checkin.created_at,
                "overall_mood": checkin.overall_mood,
                "stress_level": checkin.stress_level,
                "ai_insights": checkin.ai_insights,
                "answers": checkin.answers_json,
            }
            for checkin in checkins
        ]

    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@forms_router.get("/next-checkin/{user_id}")
def next_checkin(user_id: int, db: Session = Depends(get_db)):
    try:
        last_checkin = (
            db.query(CheckIn)
            .filter(CheckIn.user_id == user_id)
            .order_by(CheckIn.created_at.desc())
            .first()
        )

        if not last_checkin:
            return {
                "available": True,
                "message": "Usuario pode realizar o primeiro check-in.",
            }

        next_checkin_date = last_checkin.created_at + timedelta(days=30)
        now = datetime.utcnow()
        days_remaining = (next_checkin_date - now).days

        return {
            "last_checkin": last_checkin.created_at,
            "next_checkin": next_checkin_date,
            "days_remaining": max(days_remaining, 0),
        }

    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
