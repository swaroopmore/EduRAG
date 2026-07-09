from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import settings


class GeminiService:

    def __init__(self):

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.2,
        )

    # ----------------------------------------
    # Normal Generation
    # ----------------------------------------

    def generate(
        self,
        prompt,
    ):

        response = self.llm.invoke(prompt)

        return response.content

    # ----------------------------------------
    # Streaming Generation
    # ----------------------------------------

    def stream(
        self,
        prompt,
    ):

        for chunk in self.llm.stream(prompt):

            if chunk.content:

                yield chunk.content