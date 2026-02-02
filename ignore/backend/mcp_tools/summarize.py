import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def summarize_text(text):
    prompt = f"""
    You are an academic assistant.

    Summarize the following academic content clearly and concisely.
    Focus on:
    - Key concepts
    - Important definitions
    - Main results or conclusions

    Content:
    {text}
    """

    print("Calling Gemini...")
    response = client.models.generate_content(
                model = "gemini-flash-latest",
                contents=prompt)
    print("Gemini response received")

    return response.text
