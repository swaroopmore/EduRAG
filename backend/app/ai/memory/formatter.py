class ConversationFormatter:

    @staticmethod
    def format(history):

        if not history:
            return "No previous conversation."

        lines = []

        for chat in history:

            lines.append(f"User: {chat.question}")
            lines.append(f"Assistant: {chat.answer}")

        return "\n".join(lines)