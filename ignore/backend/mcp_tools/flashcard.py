import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
import json
import re

load_dotenv()
API_KEY='AIzaSyClQjunTyvCSDvSnJSJRMu6F5HVf8dnM7g'
# client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
client = genai.Client(api_key=API_KEY)

def generate_flashcards(notes: str, n_cards: int = 10):
    prompt = f"""
    You are an academic assistant.

    Generate exactly {n_cards} flashcards from the notes.

    Rules:
    - Questions and answers must be plain text
    - DO NOT use LaTeX or symbols
    - Output ONLY valid JSON (no markdown)

    Format:
    [
      {{
        "question": "...",
        "answer": "..."
      }}
    ]

    Notes:
    {notes}
    """

    response = client.models.generate_content(
                model = "gemini-flash-latest",
                contents=prompt)
    raw = response.text.strip()

    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    raw = raw.replace("\\", "").replace("$", "")

    try:
        return json.loads(raw)
    except Exception as e:
        print("JSON parse failed:", e)
        print("RAW OUTPUT:", raw)
        return []
