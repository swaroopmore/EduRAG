QUIZ_PROMPT = """
You are an expert teacher.

Using ONLY the context below, generate 10 multiple-choice questions.

Each question must contain:

- question
- option_a
- option_b
- option_c
- option_d
- correct_answer
- explanation

Return ONLY valid JSON.

Format:

[
    {{
        "question": "...",
        "option_a": "...",
        "option_b": "...",
        "option_c": "...",
        "option_d": "...",
        "correct_answer": "A",
        "explanation": "..."
    }}
]

Context:

{context}
"""