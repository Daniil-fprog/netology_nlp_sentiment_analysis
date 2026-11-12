"""Binary sentiment classification using the project's trained model."""

import re
from functools import lru_cache

import joblib

from app.core.config import SENTIMENT_MODEL_PATH


def clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"@\w+", "", text)
    text = re.sub(r"[^a-z\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


@lru_cache(maxsize=1)
def get_sentiment_model():
    if not SENTIMENT_MODEL_PATH.is_file():
        raise RuntimeError(
            f"Модель тональности не найдена: {SENTIMENT_MODEL_PATH}"
        )
    return joblib.load(SENTIMENT_MODEL_PATH)


def _positive_class(classes: list[object]) -> object:
    for candidate in (1, 4, "1", "4", "positive", "pos"):
        if candidate in classes:
            return candidate
    if len(classes) == 2:
        return classes[-1]
    raise RuntimeError(f"Модель должна иметь два класса, получено: {classes}")


def predict_sentiment(text: str) -> tuple[str, float, float]:
    """Return label, positive score (0..100), and confidence (0..100)."""
    cleaned = clean_text(text)
    if not cleaned:
        raise ValueError("После подготовки текст для анализа пуст")

    model = get_sentiment_model()
    probabilities = model.predict_proba([cleaned])[0]
    classes = list(model.classes_)
    positive_index = classes.index(_positive_class(classes))
    positive_probability = float(probabilities[positive_index])
    label = "positive" if positive_probability >= 0.5 else "negative"
    confidence = max(positive_probability, 1 - positive_probability)
    return label, round(positive_probability * 100, 2), round(confidence * 100, 2)


predict_sentimental = predict_sentiment
