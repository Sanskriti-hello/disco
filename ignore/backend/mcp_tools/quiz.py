import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
import json
import re

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def generate_quiz(text: str, n_questions: int = 5):
    prompt = f"""
SYSTEM INSTRUCTIONS (MANDATORY):
You are an intelligent quiz-generation engine.

Analyze the provided text and generate exactly {n_questions}
multiple-choice questions.

CORE BEHAVIOR RULES:
1. If the text is EDUCATIONAL CONTENT:
   - Ask conceptual and understanding-based questions.
2. If the text is STRUCTURED DATA (ranklist, scoreboard, table, etc.):
   - Ask data-analysis questions
     (e.g., "Which team secured Rank 1?",
            "What is the score of Team X?").
3. If the text is INSUFFICIENT, RANDOM, or MEANINGLESS:
   - Return an empty JSON array [].

OUTPUT FORMAT RULES (CRITICAL):
- Output ONLY valid JSON
- No markdown
- No explanations
- No comments
- No trailing text
- Strictly follow the schema below

JSON SCHEMA:
[
  {{
    "question": "string",
    "options": {{
      "A": "string",
      "B": "string",
      "C": "string",
      "D": "string"
    }},
    "answer": "A" | "B" | "C" | "D"
  }}
]

TEXT TO ANALYZE:
{text}
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