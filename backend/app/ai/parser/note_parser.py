import json


class NoteParser:

    @staticmethod
    def parse(text: str):

        if not text:
            raise ValueError("Gemini returned an empty response.")

        text = text.strip()

        if text.startswith("```json"):
            text = text.replace("```json", "", 1)

        if text.endswith("```"):
            text = text[:-3]

        text = text.strip()

        try:
            return json.loads(text)

        except json.JSONDecodeError:
            print("Gemini Response:")
            print(text)
            raise