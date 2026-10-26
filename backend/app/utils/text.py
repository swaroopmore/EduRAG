import re


def normalize_question(question: str) -> str:
    question = question.lower().strip()
    return re.sub(r"\s+", " ", question)
