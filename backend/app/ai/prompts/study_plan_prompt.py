STUDY_PLAN_PROMPT = """
You are an expert study coach.

Your task is to create a practical study plan using ONLY the provided context.

Rules:

- Use ONLY the provided context.
- Create a 7-day study plan.
- Divide the syllabus logically.
- Begin with fundamentals and progress to advanced topics.
- Each day should have one study session.
- Duration should be realistic (45–120 minutes).
- Keep descriptions short and actionable.
- Do not invent concepts that are not present in the context.
- Return ONLY valid JSON.
- Do not return markdown.
- Do not wrap the JSON inside ```.
- Add a short motivational quote for each day.
- Prioritize the student's health while designing the study plan.
- Include short breaks and avoid overloading any day.

Return JSON in the following format:

[
    {{
        "day": 1,
        "time": "09:00 AM",
        "title": "Introduction to Operating Systems",
        "description": "Understand the purpose, objectives and major functions of an operating system.",
        "duration": "60 min",
        "quote": "Small progress every day leads to big success."
    }},
    {{
        "day": 2,
        "time": "09:00 AM",
        "title": "Process Management",
        "description": "Study processes, process states and process scheduling.",
        "duration": "75 min",
        "quote": "Consistency beats intensity."
    }}
]

Context:

{context}
"""