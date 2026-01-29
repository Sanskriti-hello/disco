from typing import Dict, List, Any, Optional
from .base import BaseDomain


class StudyDomain(BaseDomain):
    """
 You are a supportive and intelligent study assistant designed to help users learn effectively.

Your goals:
- Help users understand concepts clearly and accurately
- Summarize study material into concise, meaningful points
- Assist with revision, recall, and exam preparation
- Generate learning aids such as examples, step-by-step explanations, and flashcards when appropriate

Reasoning approach:
- Identify the users learning intent (explanation, summary, revision, or memorization)
- Adapt explanations to the users apparent level (beginner-friendly by default)
- Break complex ideas into simple, logical steps
- Use analogies or examples when they improve understanding

Rules:
- Do not assume prior subject knowledge unless stated
- Avoid unnecessary jargon
- If information is missing or unclear, state assumptions explicitly
- Do not hallucinate facts; rely on provided material or general knowledge

Learning style:
- Prefer structured outputs (headings, bullet points, steps)
- Highlight key ideas and definitions
- Emphasize understanding over rote memorization

Tone:
- Calm
- Encouraging
- Clear and patient

Example behavior:
- When explaining, focus on intuition first, then details
- When summarizing, focus on core ideas rather than copying text
- When creating flashcards, keep questions simple and answers precise
    """

    def get_required_mcps(self, user_prompt: str) -> List[str]:
        mcps = ["browser"]
        prompt = user_prompt.lower()

        # Concept explanation -> Search + Arxiv
        if any(word in prompt for word in ["explain", "what is", "how does", "research", "paper", "study"]):
            mcps.extend(["search", "arxiv"])

        # Notes & Summarization -> Google Workspace (Docs) + Browser
        if any(word in prompt for word in ["summarize", "summary", "notes", "write", "draft"]):
            mcps.append("google_workspace")
            
        # News and Current Events in field
        if any(word in prompt for word in ["news", "latest", "update", "recent"]):
            mcps.append("news")

        # Scheduling / Study Plan
        if any(word in prompt for word in ["schedule", "plan", "calendar", "exam", "test"]):
            mcps.append("google_workspace")

        # Fallback knowledge source
        mcps.append("search")

        return list(set(mcps))

    def get_system_prompt(self) -> str:
        return """
    You are a helpful study assistant.

    Your goals:
    - Help users understand concepts clearly
    - Summarize study material concisely
    - Assist with revision and memory
    - Adapt explanations to the user's level

    Guidelines:
    - Be clear and structured
    - Use examples when helpful
    - Avoid unnecessary jargon
    - If the task is unclear, explain options briefly

    Tone:
    - Calm
    - Supportive
    - Encouraging
"""

    def select_ui_template(self, mcp_data: Dict[str, Any]) -> str:
        if "flashcards" in mcp_data:
            return "FlashcardView"

        if "summarizer" in mcp_data:
            return "SummaryView"

        if "documents" in mcp_data:
            return "StudyNotesView"

        return "ExplanationView"

    def prepare_ui_props(
        self, mcp_data: Dict[str, Any], llm_response: str
    ) -> Dict[str, Any]:

        props={
            "userMessage": llm_response,
            "timestamp": mcp_data.get("timestamp","")
        }
        if "documents" in mcp_data:
            props["content"]=mcp_data["documents"]

        if "summary" in mcp_data:
            props["summary"] = mcp_data["summary"]
        if "flashcards" in mcp_data:
            props["flashcards"]=mcp_data["flashcards"]
        return props

    def validate_data(self, mcp_data: Dict[str, Any]) -> bool:
        if "browser" not in mcp_data:
            return False

        if "documents" not in mcp_data and "search" not in mcp_data:
            return False

        return True

    def get_follow_up_question(self, mcp_data: Dict[str, Any]) -> Optional[str]:
    # 1. Hard blocker: browser missing
        if "browser" not in mcp_data:
            return "Could you allow access to your study material or browser context?"

        # 2. Content source missing
        if "documents" not in mcp_data and "search" not in mcp_data:
            return "Do you have notes, text, a PDF, or a topic you want help with?"

        # 3. Generic fallback
        return (
            "How would you like me to help you study this? "
            "For example: explanation, summary, flashcards, or revision."
        )

        