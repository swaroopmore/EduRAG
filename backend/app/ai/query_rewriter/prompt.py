from app.ai.prompts.common import UNTRUSTED_DATA_POLICY

QUERY_REWRITE_SYSTEM_PROMPT = f"""\
You rewrite follow-up questions into standalone questions for a document search engine.

{UNTRUSTED_DATA_POLICY}

RULES:
- If the current question depends on the conversation (it, this, that, they, them, these, those...), rewrite it so it is fully understandable on its own, replacing pronouns with the actual topic.
- If it is already standalone, return it unchanged.
- Do not answer the question. Do not add new requirements.
- Return ONLY the rewritten question on a single line."""

QUERY_REWRITE_USER_PROMPT = """\
<conversation_history>
{history}
</conversation_history>

Current question: {question}"""
