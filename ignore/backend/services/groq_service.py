from __future__ import annotations

import os
import json
import time
from typing import Any, Dict, Optional

import httpx


class GroqService:
    def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.3-70b-versatile"):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.model = model
        self.url = "https://api.groq.com/openai/v1/chat/completions"

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    async def chat_json(self, system_prompt: str, user_prompt: str, max_tokens: int = 1024) -> Dict[str, Any]:
        if not self.available:
            raise RuntimeError("GROQ_API_KEY missing")

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
            "max_completion_tokens": max_tokens,
            "response_format": {"type": "json_object"},
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        start = time.perf_counter()
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(self.url, headers=headers, json=payload)
        elapsed = (time.perf_counter() - start) * 1000

        if resp.status_code >= 400:
            raise RuntimeError(f"Groq HTTP {resp.status_code}: {resp.text[:300]}")

        raw = resp.json()
        if not raw.get("choices"):
            raise RuntimeError("Groq response missing choices")

        content = raw["choices"][0]["message"]["content"]
        try:
            parsed = json.loads(content)
        except Exception as e:
            raise RuntimeError(f"Groq returned non-JSON content: {e}")

        parsed["_meta"] = {"provider": "groq", "latency_ms": round(elapsed, 2)}
        return parsed
