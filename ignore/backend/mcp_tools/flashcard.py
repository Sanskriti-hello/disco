def llm_generate_flashcards(payload: str) -> dict:
  """LLM adapter: Generate flashcards. Payload: {"notes": str, "n_cards": int}"""
  import json
  try:
    args = json.loads(payload)
    result = generate_flashcards(args["notes"], int(args.get("n_cards", 10)))
    return {"status": "success", "result": result}
  except Exception as e:
    return {"status": "error", "message": str(e)}
import os
import google.generativeai as genai
from dotenv import load_dotenv
import json
import re

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

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

    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(prompt)
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
