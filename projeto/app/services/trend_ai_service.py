from __future__ import annotations

import hashlib
from collections import defaultdict
from dataclasses import dataclass
from math import sqrt
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from sqlalchemy.orm import Session

from app.db.models.checkin import CheckIn

try:
    import joblib
    from sklearn.ensemble import RandomForestClassifier
except ImportError:
    joblib = None
    RandomForestClassifier = None

NEGATIVE_QUESTION_IDS = {1, 3}

QUESTION_LABELS = {
    1: "sobrecarga no trabalho",
    2: "apoio nas demandas",
    3: "interferencia da vida pessoal",
    4: "cultura inclusiva",
    5: "relacao com lideranca",
    6: "trabalho em equipe",
    7: "avaliacao do proprio trabalho",
    8: "reconhecimento",
    9: "crescimento profissional",
    10: "sentimento geral sobre a empresa",
}

TREND_TITLES = {
    "improving": "melhora",
    "worsening": "piora",
    "stable": "estabilidade",
}

FEATURE_SCALES = (100.0, 50.0, 50.0, 100.0, 100.0, 40.0, 100.0)
ML_MODEL_PATH = Path("app/ml/trend_model.joblib")
ML_MODEL_VERSION = 1
_MODEL_CACHE: dict[str, Any] = {}


@dataclass(frozen=True)
class TrendPrediction:
    trend: str
    confidence: float
    wellbeing_score: int
    previous_score: int | None
    score_delta: int | None
    summary: str


def normalize_answers(answers: Iterable[Any] | Mapping[str, Any] | None) -> dict[int, int]:
    if answers is None:
        return {}

    if isinstance(answers, Mapping):
        if "question_id" in answers and "value" in answers:
            raw_answers = [answers]
        else:
            normalized: dict[int, int] = {}
            for question_id, value in answers.items():
                try:
                    question_id_int = int(question_id)
                except (TypeError, ValueError):
                    continue

                numeric_value = _normalize_scale_value(value)
                if numeric_value is not None:
                    normalized[question_id_int] = numeric_value

            return normalized
    else:
        raw_answers = answers

    normalized: dict[int, int] = {}
    for answer in raw_answers:
        question_id = _read_answer_field(answer, "question_id")
        value = _read_answer_field(answer, "value")

        try:
            question_id_int = int(question_id)
        except (TypeError, ValueError):
            continue

        numeric_value = _normalize_scale_value(value)
        if numeric_value is None:
            continue

        normalized[question_id_int] = numeric_value

    return normalized


def calculate_raw_average(answers: Iterable[Any] | Mapping[str, Any] | None) -> float:
    answer_map = normalize_answers(answers)
    if not answer_map:
        return 0.0

    return sum(answer_map.values()) / len(answer_map)


def calculate_wellbeing_score(answers: Iterable[Any] | Mapping[str, Any] | None) -> float:
    answer_map = normalize_answers(answers)
    if not answer_map:
        return 0.0

    scores = [
        _scale_value_to_score(_adjusted_scale_value(question_id, value))
        for question_id, value in answer_map.items()
    ]
    return sum(scores) / len(scores)


def mood_from_score(score: float) -> str:
    if score < 35:
        return "Risco"
    if score < 50:
        return "Atencao"
    if score < 65:
        return "Satisfatorio"
    if score < 80:
        return "Bom"
    return "Otimo"


class TrendAIService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def predict(
        self,
        *,
        user_id: int,
        current_answers: Iterable[Any] | Mapping[str, Any] | None,
    ) -> TrendPrediction:
        historical_scores = self._get_historical_scores(user_id)
        return self.predict_with_history(
            current_answers=current_answers,
            historical_scores=historical_scores,
        )

    def predict_with_history(
        self,
        *,
        current_answers: Iterable[Any] | Mapping[str, Any] | None,
        historical_scores: Sequence[float],
    ) -> TrendPrediction:
        current_score = calculate_wellbeing_score(current_answers)
        features = self._build_features(current_answers, historical_scores)
        training_samples = self._build_training_samples()
        trend, confidence = self._predict_with_ml_model(features, training_samples)

        previous_score = round(historical_scores[-1]) if historical_scores else None
        rounded_score = round(current_score)
        score_delta = (
            rounded_score - previous_score if previous_score is not None else None
        )
        summary = self._build_summary(
            trend=trend,
            confidence=confidence,
            current_answers=current_answers,
            wellbeing_score=rounded_score,
            previous_score=previous_score,
            score_delta=score_delta,
            history_size=len(historical_scores),
        )

        return TrendPrediction(
            trend=trend,
            confidence=confidence,
            wellbeing_score=rounded_score,
            previous_score=previous_score,
            score_delta=score_delta,
            summary=summary,
        )

    def train_and_save_model(self) -> Path:
        training_samples = self._build_training_samples()
        self._load_or_train_model(training_samples, force_retrain=True)
        return ML_MODEL_PATH

    def _get_historical_scores(self, user_id: int) -> list[float]:
        checkins = (
            self.db.query(CheckIn)
            .filter(CheckIn.user_id == user_id)
            .order_by(CheckIn.submitted_at.asc(), CheckIn.created_at.asc())
            .all()
        )

        scores = []
        for checkin in checkins:
            score = calculate_wellbeing_score(checkin.answers_json)
            if score > 0:
                scores.append(score)

        return scores

    def _build_training_samples(self) -> list[tuple[tuple[float, ...], str]]:
        return [
            *self._synthetic_training_samples(),
            *self._historical_training_samples(),
        ]

    def _synthetic_training_samples(self) -> list[tuple[tuple[float, ...], str]]:
        samples: list[tuple[tuple[float, ...], str]] = []

        for current_score in range(20, 96, 5):
            for latest_delta in range(-30, 31, 10):
                for rolling_delta in (-24, -12, 0, 12, 24):
                    for pressure in (20, 45, 70, 90):
                        for support in (25, 55, 85):
                            features = (
                                float(current_score),
                                float(latest_delta),
                                float(rolling_delta),
                                float(pressure),
                                float(support),
                                10.0,
                                100.0,
                            )
                            samples.append((features, self._label_from_features(features)))

        return samples

    def _historical_training_samples(self) -> list[tuple[tuple[float, ...], str]]:
        checkins = (
            self.db.query(CheckIn)
            .order_by(
                CheckIn.user_id.asc(),
                CheckIn.submitted_at.asc(),
                CheckIn.created_at.asc(),
            )
            .all()
        )

        checkins_by_user: dict[int, list[CheckIn]] = defaultdict(list)
        for checkin in checkins:
            checkins_by_user[checkin.user_id].append(checkin)

        samples: list[tuple[tuple[float, ...], str]] = []
        for user_checkins in checkins_by_user.values():
            history: list[float] = []
            for checkin in user_checkins:
                score = calculate_wellbeing_score(checkin.answers_json)
                if score <= 0:
                    continue

                if history:
                    features = self._build_features(checkin.answers_json, history)
                    samples.append((features, self._label_from_outcome(score, history)))

                history.append(score)

        return samples

    def _build_features(
        self,
        answers: Iterable[Any] | Mapping[str, Any] | None,
        historical_scores: Sequence[float],
    ) -> tuple[float, ...]:
        answer_map = normalize_answers(answers)
        current_score = calculate_wellbeing_score(answer_map)
        latest_delta = (
            current_score - historical_scores[-1] if historical_scores else 0.0
        )
        recent_scores = list(historical_scores[-3:])
        rolling_average = (
            sum(recent_scores) / len(recent_scores) if recent_scores else current_score
        )
        rolling_delta = current_score - rolling_average
        negative_pressure = self._negative_pressure(answer_map)
        support_score = self._support_score(answer_map, current_score)
        volatility = self._volatility([*historical_scores[-5:], current_score])
        history_strength = min(len(historical_scores), 6) / 6 * 100

        return (
            current_score,
            latest_delta,
            rolling_delta,
            negative_pressure,
            support_score,
            volatility,
            history_strength,
        )

    def _negative_pressure(self, answer_map: Mapping[int, int]) -> float:
        values = [
            _scale_value_to_score(value)
            for question_id, value in answer_map.items()
            if question_id in NEGATIVE_QUESTION_IDS
        ]
        if not values:
            return 50.0

        return sum(values) / len(values)

    def _support_score(
        self,
        answer_map: Mapping[int, int],
        fallback_score: float,
    ) -> float:
        values = [
            _scale_value_to_score(value)
            for question_id, value in answer_map.items()
            if question_id not in NEGATIVE_QUESTION_IDS
        ]
        if not values:
            return fallback_score

        return sum(values) / len(values)

    def _volatility(self, scores: Sequence[float]) -> float:
        if len(scores) < 2:
            return 0.0

        movements = [
            abs(scores[index] - scores[index - 1])
            for index in range(1, len(scores))
        ]
        return sum(movements) / len(movements)

    def _predict_with_ml_model(
        self,
        features: tuple[float, ...],
        samples: Sequence[tuple[tuple[float, ...], str]],
    ) -> tuple[str, float]:
        if joblib is None or RandomForestClassifier is None:
            return self._predict_knn(features, samples)

        model = self._load_or_train_model(samples)
        probabilities = model.predict_proba([features])[0]
        classes = list(model.classes_)
        best_index = max(range(len(probabilities)), key=lambda index: probabilities[index])

        trend = str(classes[best_index])
        confidence = max(0.55, min(0.97, float(probabilities[best_index])))

        return trend, confidence

    def _load_or_train_model(
        self,
        samples: Sequence[tuple[tuple[float, ...], str]],
        *,
        force_retrain: bool = False,
    ) -> Any:
        sample_signature = self._sample_signature(samples)

        if (
            not force_retrain
            and _MODEL_CACHE.get("sample_signature") == sample_signature
        ):
            return _MODEL_CACHE["model"]

        if not force_retrain and ML_MODEL_PATH.exists():
            payload = joblib.load(ML_MODEL_PATH)
            if (
                payload.get("version") == ML_MODEL_VERSION
                and payload.get("sample_signature") == sample_signature
            ):
                _MODEL_CACHE["sample_signature"] = sample_signature
                _MODEL_CACHE["model"] = payload["model"]
                return payload["model"]

        model = RandomForestClassifier(
            n_estimators=180,
            max_depth=8,
            min_samples_leaf=3,
            class_weight="balanced",
            random_state=42,
        )
        feature_rows = [sample_features for sample_features, _label in samples]
        labels = [label for _sample_features, label in samples]
        model.fit(feature_rows, labels)

        ML_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {
                "version": ML_MODEL_VERSION,
                "sample_signature": sample_signature,
                "model": model,
            },
            ML_MODEL_PATH,
        )
        _MODEL_CACHE["sample_signature"] = sample_signature
        _MODEL_CACHE["model"] = model

        return model

    def _sample_signature(
        self,
        samples: Sequence[tuple[tuple[float, ...], str]],
    ) -> str:
        digest = hashlib.sha256()
        digest.update(str(ML_MODEL_VERSION).encode("utf-8"))

        for features, label in samples:
            digest.update(label.encode("utf-8"))
            digest.update(b"|")
            digest.update(",".join(f"{value:.4f}" for value in features).encode("utf-8"))
            digest.update(b";")

        return digest.hexdigest()

    def _predict_knn(
        self,
        features: tuple[float, ...],
        samples: Sequence[tuple[tuple[float, ...], str]],
        *,
        k: int = 11,
    ) -> tuple[str, float]:
        nearest = sorted(
            (
                (self._distance(features, sample_features), label)
                for sample_features, label in samples
            ),
            key=lambda item: item[0],
        )[:k]

        votes: dict[str, float] = defaultdict(float)
        for distance, label in nearest:
            votes[label] += 1 / (distance + 0.02)

        trend, winning_vote = max(votes.items(), key=lambda item: item[1])
        total_vote = sum(votes.values()) or 1
        confidence = max(0.55, min(0.95, winning_vote / total_vote))

        return trend, confidence

    def _distance(
        self,
        left: tuple[float, ...],
        right: tuple[float, ...],
    ) -> float:
        return sqrt(
            sum(
                ((left_value - right_value) / scale) ** 2
                for left_value, right_value, scale in zip(left, right, FEATURE_SCALES)
            )
        )

    def _label_from_outcome(
        self,
        current_score: float,
        history: Sequence[float],
    ) -> str:
        latest_delta = current_score - history[-1]
        rolling_average = sum(history[-3:]) / min(len(history), 3)
        rolling_delta = current_score - rolling_average

        if latest_delta <= -7 or rolling_delta <= -8:
            return "worsening"
        if latest_delta >= 7 or rolling_delta >= 8:
            return "improving"
        return "stable"

    def _label_from_features(self, features: tuple[float, ...]) -> str:
        (
            current_score,
            latest_delta,
            rolling_delta,
            negative_pressure,
            support_score,
            _volatility,
            _history_strength,
        ) = features

        if latest_delta <= -7 or rolling_delta <= -8:
            return "worsening"
        if latest_delta >= 7 or rolling_delta >= 8:
            return "improving"
        if current_score <= 42 and negative_pressure >= 65 and support_score <= 50:
            return "worsening"
        if current_score >= 72 and negative_pressure <= 45 and support_score >= 65:
            return "improving"
        return "stable"

    def _build_summary(
        self,
        *,
        trend: str,
        confidence: float,
        current_answers: Iterable[Any] | Mapping[str, Any] | None,
        wellbeing_score: int,
        previous_score: int | None,
        score_delta: int | None,
        history_size: int,
    ) -> str:
        trend_title = TREND_TITLES[trend]
        parts = [
            f"Tendencia de {trend_title} detectada pela IA "
            f"(confianca {round(confidence * 100)}%).",
            f"Pontuacao atual: {wellbeing_score}/100.",
        ]

        if score_delta is not None and previous_score is not None:
            signal = "+" if score_delta > 0 else ""
            parts.append(
                f"Variacao em relacao ao ultimo check-in: {signal}{score_delta} pontos "
                f"(anterior: {previous_score}/100)."
            )
        elif history_size == 0:
            parts.append(
                "Sem historico anterior suficiente; a IA usou os sinais do check-in "
                "atual e exemplos sinteticos de treino."
            )

        factor_scores = self._factor_scores(current_answers)
        attention_points = [
            label for label, score in sorted(factor_scores, key=lambda item: item[1])[:2]
            if score < 55
        ]
        strong_points = [
            label
            for label, score in sorted(
                factor_scores,
                key=lambda item: item[1],
                reverse=True,
            )[:2]
            if score >= 70
        ]

        if attention_points:
            parts.append(f"Pontos de atencao: {', '.join(attention_points)}.")
        if strong_points:
            parts.append(f"Sinais positivos: {', '.join(strong_points)}.")

        return " ".join(parts)

    def _factor_scores(
        self,
        answers: Iterable[Any] | Mapping[str, Any] | None,
    ) -> list[tuple[str, float]]:
        answer_map = normalize_answers(answers)
        factors = []
        for question_id, value in answer_map.items():
            adjusted_value = _adjusted_scale_value(question_id, value)
            label = QUESTION_LABELS.get(question_id, f"pergunta {question_id}")
            if question_id in NEGATIVE_QUESTION_IDS and adjusted_value >= 4:
                label = f"baixa {label}"
            factors.append((label, _scale_value_to_score(adjusted_value)))

        return factors


def _read_answer_field(answer: Any, field: str) -> Any:
    if isinstance(answer, Mapping):
        return answer.get(field)

    return getattr(answer, field, None)


def _normalize_scale_value(value: Any) -> int | None:
    try:
        numeric_value = int(value)
    except (TypeError, ValueError):
        return None

    return max(1, min(5, numeric_value))


def _adjusted_scale_value(question_id: int, value: int) -> int:
    if question_id in NEGATIVE_QUESTION_IDS:
        return 6 - value

    return value


def _scale_value_to_score(value: int) -> float:
    return (value - 1) / 4 * 100
