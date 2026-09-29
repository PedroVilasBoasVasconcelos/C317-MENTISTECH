from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.database import SessionLocal
from app.db.models import CheckIn
from app.services.trend_ai_service import (
    TrendAIService,
    calculate_wellbeing_score,
    mood_from_score,
)


def main() -> None:
    db = SessionLocal()
    try:
        service = TrendAIService(db)
        history_by_user: dict[int, list[float]] = defaultdict(list)
        updated = 0

        checkins = (
            db.query(CheckIn)
            .order_by(
                CheckIn.user_id.asc(),
                CheckIn.submitted_at.asc(),
                CheckIn.created_at.asc(),
            )
            .all()
        )

        for checkin in checkins:
            score = calculate_wellbeing_score(checkin.answers_json)
            if score <= 0:
                continue

            user_history = history_by_user[checkin.user_id]
            prediction = service.predict_with_history(
                current_answers=checkin.answers_json,
                historical_scores=user_history,
            )
            checkin.overall_mood = mood_from_score(prediction.wellbeing_score)
            checkin.stress_level = prediction.wellbeing_score
            checkin.ai_insights = prediction.summary
            user_history.append(score)
            updated += 1

        db.commit()
        print(f"Backfill finalizado. Check-ins atualizados: {updated}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
