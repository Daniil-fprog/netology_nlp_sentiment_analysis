"""Lazy Russian-to-English translation for the English sentiment model."""

import re
from functools import lru_cache

from app.core.config import TRANSLATION_MODEL_NAME


def contains_cyrillic(text: str) -> bool:
    return bool(re.search(r"[Ѐ-ӿ]", text))


@lru_cache(maxsize=1)
def _get_translator():
    import torch
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(TRANSLATION_MODEL_NAME)
    model = AutoModelForSeq2SeqLM.from_pretrained(TRANSLATION_MODEL_NAME)
    model.to(torch.device("cpu"))
    model.eval()
    return tokenizer, model, torch


def translate_to_english(text: str) -> str:
    if not text.strip() or not contains_cyrillic(text):
        return text

    tokenizer, model, torch = _get_translator()
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        output = model.generate(**inputs, max_length=512, num_beams=4)
    return tokenizer.decode(output[0], skip_special_tokens=True)
