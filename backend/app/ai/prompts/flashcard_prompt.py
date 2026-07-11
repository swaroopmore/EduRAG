FLASHCARD_PROMPT = """
You are an expert teacher.

Your task is to generate high-quality flashcards from the study material.

Instructions:

- Generate between 10 and 20 flashcards.
- Cover all important concepts.
- Questions should be concise.
- Answers should be clear and easy to remember.
- Do not generate duplicate flashcards.
- Do not include numbering.
- Do not include markdown.
- Return ONLY valid JSON.

JSON Format:

[
    {{
        "question": "...",
        "answer": "..."
    }}
]

Study Material:

{context}
"""