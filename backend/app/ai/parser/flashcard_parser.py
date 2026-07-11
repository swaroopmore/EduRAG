import json


class FlashcardParser:

    @staticmethod
    def parse(text: str):

        text = text.strip()

        if "```json" in text:

            text = text.replace("```json", "")
            text = text.replace("```", "")

        return json.loads(text)