def llm_summarize_text(payload: str) -> dict:
    """LLM adapter: Summarize text. Payload: {"text": str}"""
    import json
    try:
        args = json.loads(payload)
        result = summarize_text(args["text"])
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}
"""
Text Summarization MCP Tool
============================
Summarizes long text content using Google Gemini AI.

Use this tool to condense long articles, research papers, documentation,
or any lengthy text into a concise, readable summary.

Required .env variables:
    GEMINI_API_KEY=your_gemini_api_key
"""

import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configure the Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')


def summarize_text(text: str) -> str:
    """
    Summarize long text content into a concise summary using Gemini AI.
    
    Use this tool when you have lengthy content that needs to be condensed
    while preserving the key information. Ideal for:
    - Academic papers and research articles
    - Long documentation pages
    - News articles and blog posts
    - Technical specifications
    
    Args:
        text: The text content to summarize. Can be any length, but longer
              texts benefit more from summarization.
    
    Returns:
        str: A concise summary focusing on:
            - Key concepts and main ideas
            - Important definitions
            - Main results, conclusions, or takeaways
    
    Example:
        summary = summarize_text(long_article_text)
        # Returns: "This article discusses the impact of..."
    """
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
    response = model.generate_content(prompt)
    print("Gemini response received")

    return response.text
