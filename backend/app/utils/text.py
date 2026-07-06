import re


def normalize_question(question: str) -> str:
    question = question.lower().strip()

    question = re.sub(r"\s+", " ", question)

    return question