from app.ai.llm.gemini_service import GeminiService
from app.ai.query_rewriter.prompt import QUERY_REWRITE_PROMPT


class QueryRewriter:

    def __init__(self):

        self.llm = GeminiService()

    def rewrite(
        self,
        question: str,
        history: str,
    ) -> str:

        prompt = QUERY_REWRITE_PROMPT.format(
            history=history,
            question=question,
        )

        rewritten_question = self.llm.generate(prompt)

        rewritten_question = rewritten_question.strip()

        print("\n" + "=" * 60)
        print("QUERY REWRITER")
        print("=" * 60)
        print(f"Original Question : {question}")
        print(f"Rewritten Question: {rewritten_question}")
        print("=" * 60 + "\n")

        return rewritten_question