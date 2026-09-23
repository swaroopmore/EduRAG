"""Pydantic schemas that validate every AI-generated resource before it is stored."""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.ai.guardrails.sanitize import clean_text, truncate

_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def _text(value: Any, limit: int, *, multiline: bool = False) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        value = str(value)
    value = clean_text(value)
    if not multiline:
        value = " ".join(value.split())
    return truncate(value, limit)


class _Base(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)


class NoteSection(_Base):
    title: str
    content: str
    keywords: list[str] = Field(default_factory=list)

    @field_validator("title", mode="before")
    @classmethod
    def _title(cls, v):
        v = _text(v, 200)
        if not v:
            raise ValueError("title is empty")
        return v

    @field_validator("content", mode="before")
    @classmethod
    def _content(cls, v):
        v = _text(v, 12000, multiline=True)
        if len(v) < 10:
            raise ValueError("content too short")
        return v

    @field_validator("keywords", mode="before")
    @classmethod
    def _keywords(cls, v):
        if isinstance(v, str):
            v = [k for k in re.split(r"[,;\n]", v)]
        if not isinstance(v, list):
            return []
        seen: set[str] = set()
        out: list[str] = []
        for item in v:
            word = _text(item, 40)
            if word and word.lower() not in seen:
                seen.add(word.lower())
                out.append(word)
        return out[:8]


class FlashcardItem(_Base):
    question: str
    answer: str

    @field_validator("question", mode="before")
    @classmethod
    def _q(cls, v):
        v = _text(v, 500)
        if len(v) < 3:
            raise ValueError("question empty")
        return v

    @field_validator("answer", mode="before")
    @classmethod
    def _a(cls, v):
        v = _text(v, 1500, multiline=True)
        if not v:
            raise ValueError("answer empty")
        return v


class QuizItem(_Base):
    question: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_answer: str
    explanation: str = ""

    @model_validator(mode="before")
    @classmethod
    def _accept_options_list(cls, data):
        # Tolerate {"options": ["..", "..", "..", ".."]} or {"options": {"A": ".."}}
        if isinstance(data, dict) and "option_a" not in data and "options" in data:
            options = data["options"]
            data = dict(data)
            if isinstance(options, dict):
                for letter in "abcd":
                    data[f"option_{letter}"] = options.get(letter.upper(), options.get(letter))
            elif isinstance(options, list) and len(options) >= 4:
                for letter, value in zip("abcd", options):
                    data[f"option_{letter}"] = value
        return data

    @field_validator("question", "option_a", "option_b", "option_c", "option_d", "explanation", mode="before")
    @classmethod
    def _strings(cls, v, info):
        limit = 600 if info.field_name == "question" else 400
        if info.field_name == "explanation":
            limit = 800
        v = _text(v, limit)
        if not v and info.field_name != "explanation":
            raise ValueError(f"{info.field_name} is empty")
        # strip "A) " style prefixes from options
        if info.field_name.startswith("option_"):
            v = re.sub(r"^\(?[A-Da-d][\).:]\s+", "", v)
        return v

    @model_validator(mode="after")
    def _check(self):
        options = [self.option_a, self.option_b, self.option_c, self.option_d]
        if len({o.lower() for o in options}) != 4:
            raise ValueError("options must be distinct")

        raw = self.correct_answer.strip() if isinstance(self.correct_answer, str) else ""
        letter = None
        match = re.match(r"^\(?(?:option\s*)?([A-Da-d])\)?(?:[\).:\s]|$)", raw, re.IGNORECASE)
        if match:
            letter = match.group(1).upper()
        else:  # model returned the option text instead of the letter
            for candidate, option in zip("ABCD", options):
                if raw.lower() == option.lower():
                    letter = candidate
        if letter is None:
            raise ValueError("correct_answer is not A-D")
        self.correct_answer = letter
        return self


class StudyPlanItem(_Base):
    day: int = Field(ge=1, le=60)
    time: str = "09:00 AM"
    title: str
    description: str
    duration: str = "60 min"
    quote: str = ""

    @field_validator("day", mode="before")
    @classmethod
    def _day(cls, v):
        if isinstance(v, str):
            m = re.search(r"\d+", v)
            if not m:
                raise ValueError("day is not a number")
            return int(m.group())
        return v

    @field_validator("time", "duration", mode="before")
    @classmethod
    def _short(cls, v, info):
        if v is None or v == "":
            return "09:00 AM" if info.field_name == "time" else "60 min"
        if info.field_name == "duration" and isinstance(v, (int, float)):
            return f"{int(v)} min"
        return _text(v, 40)

    @field_validator("title", mode="before")
    @classmethod
    def _title(cls, v):
        v = _text(v, 200)
        if not v:
            raise ValueError("title empty")
        return v

    @field_validator("description", mode="before")
    @classmethod
    def _description(cls, v):
        v = _text(v, 600)
        if not v:
            raise ValueError("description empty")
        return v

    @field_validator("quote", mode="before")
    @classmethod
    def _quote(cls, v):
        return _text(v, 200)
