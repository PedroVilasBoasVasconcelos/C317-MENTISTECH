from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.database import SessionLocal
from app.services.trend_ai_service import TrendAIService


def main() -> None:
    db = SessionLocal()
    try:
        model_path = TrendAIService(db).train_and_save_model()
        print(f"Modelo de IA/ML treinado e salvo em: {model_path}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
