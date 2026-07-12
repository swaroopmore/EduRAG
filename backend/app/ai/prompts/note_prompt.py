NOTES_PROMPT = """
You are an expert teacher.

Your task is to generate well-structured study notes from the context below.

Rules:

- Use ONLY the provided context.
- Divide the notes into meaningful topics.
- Each topic should have:
    - title
    - content
- Content should be concise, easy to understand, and suitable for revision.
- Use paragraphs instead of one-line answers.
- Do not invent information.
- Return ONLY valid JSON.

Format:

[
    {{
        "title": "...",
        "content": "..."
    }},
    {{
        "title": "...",
        "content": "..."
    }}
]

Context:

{context}
"""