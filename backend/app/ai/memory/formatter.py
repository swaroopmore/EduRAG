from app.ai.guardrails.sanitize import clean_text, neutralize_delimiters, truncate


class ConversationFormatter:
    @staticmethod
    def format(history) -> str:
        if not history:
            return "No previous conversation."

        lines = []
        for chat in history:
            question = truncate(neutralize_delimiters(clean_text(chat.question)), 400)
            answer = truncate(neutralize_delimiters(clean_text(chat.answer)), 600)
            lines.append(f"User: {question}")
            lines.append(f"Assistant: {answer}")
        return "\n".join(lines)
