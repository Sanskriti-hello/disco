# Disco Development Setup

## Architecture
Chrome Extension -> FastAPI backend (`http://127.0.0.1:8000`) -> LLM providers (Groq/Gemini) with deterministic fallback.

## 1) Backend setup
1. `cd ignore/backend`
2. Copy `.env.example` to `.env`
3. Fill API keys as needed (`GROQ_API_KEY`, `GEMINI_API_KEY`)
4. Install deps (example): `pip install fastapi uvicorn python-dotenv httpx langgraph`
5. Run backend: `python main.py`
6. Check health: `GET http://127.0.0.1:8000/health`

## 2) Extension setup
1. `cd ignore/extension`
2. Install deps: `npm install`
3. Build: `npm run build`
4. Load unpacked extension from `ignore/extension/dist` in `chrome://extensions`

## 3) Debugging flow
- Extension service worker logs: Chrome extensions inspector.
- Backend logs: terminal running `python main.py`.
- Health status appears in cluster selector popup.
- If Groq/Gemini unavailable, backend falls back to deterministic mode.

## 4) API endpoints
- `GET /health`
- `POST /api/cluster-tabs`
- `POST /api/select-domain`
- `POST /api/generate-dashboard`
- `POST /api/summarize`

## 5) Tests
From `ignore/backend` run:
- `python -m unittest discover -s tests -p "test_*.py"`
