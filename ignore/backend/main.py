import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

current_dir = Path(__file__).resolve().parent
load_dotenv(current_dir / ".env")

if str(current_dir) not in sys.path:
    sys.path.append(str(current_dir))

from langraph.api_endpoint import router  # noqa: E402


def validate_env() -> None:
    optional_keys = ["GROQ_API_KEY", "GEMINI_API_KEY", "TAVILY_API_KEY", "RAPIDAPI_KEY"]
    print("[startup] validating environment...")
    configured = [k for k in optional_keys if os.getenv(k)]
    for key in optional_keys:
        if os.getenv(key):
            print(f"[startup] {key}: configured")
        else:
            print(f"[startup] {key}: missing")

    if not configured:
        print("[startup] warning: no LLM provider key configured. Deterministic fallback mode only.")


validate_env()

app = FastAPI(title="Disco Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
async def root():
    return {"status": "online", "message": "Disco Dashboard Backend is running", "version": "3.0.0"}


if __name__ == "__main__":
    import uvicorn

    print("Starting Disco Dashboard Server on http://127.0.0.1:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
