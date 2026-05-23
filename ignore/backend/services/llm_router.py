from __future__ import annotations

import os
import re
import time
from collections import Counter, defaultdict
from typing import Any, Dict, List, Tuple
from urllib.parse import urlparse

import httpx

from .groq_service import GroqService

VALID_DOMAINS = ["study", "shopping", "travel", "code", "entertainment", "generic"]
STOPWORDS = {
    "the", "and", "for", "with", "from", "that", "this", "your", "you", "are", "how", "what", "when",
    "under", "into", "about", "have", "has", "was", "will", "can", "all", "open", "tabs", "best", "new",
    "www", "com", "org", "net", "in", "on", "at", "to", "of", "a", "an", "is", "it", "by", "vs",
}
INTENT_HINTS = {
    "shopping": ["buy", "price", "deal", "review", "compare", "cart", "discount", "amazon", "flipkart"],
    "study": ["paper", "course", "lecture", "notes", "research", "study", "pdf", "arxiv"],
    "travel": ["flight", "hotel", "trip", "itinerary", "booking", "visa", "train", "tour"],
    "code": ["github", "stack", "bug", "debug", "api", "framework", "repo", "programming", "code"],
    "entertainment": ["movie", "music", "netflix", "spotify", "stream", "game", "trailer", "youtube"],
}


def _tokenize(text: str) -> List[str]:
    words = re.findall(r"[a-zA-Z0-9][a-zA-Z0-9\-\+#]{1,}", (text or "").lower())
    return [w for w in words if w not in STOPWORDS and len(w) > 2]


def _infer_domain(text: str) -> str:
    t = text.lower()
    if any(k in t for k in ["amazon", "flipkart", "buy", "price", "cart", "product", "deal"]):
        return "shopping"
    if any(k in t for k in ["arxiv", "paper", "learn", "course", "study", "lecture", "pdf", "journal"]):
        return "study"
    if any(k in t for k in ["flight", "hotel", "booking", "trip", "travel", "itinerary", "visa"]):
        return "travel"
    if any(k in t for k in ["github", "stack overflow", "code", "bug", "debug", "api docs", "programming"]):
        return "code"
    if any(k in t for k in ["youtube", "movie", "netflix", "spotify", "music", "game", "stream"]):
        return "entertainment"
    return "generic"


def _infer_intent(domain: str, tokens: List[str]) -> str:
    if domain == "shopping":
        return "shopping"
    if domain == "study":
        return "research"
    if domain == "travel":
        return "travel planning"
    if domain == "code":
        return "coding"
    if domain == "entertainment":
        return "entertainment"
    counts = Counter(tokens)
    for d, hints in INTENT_HINTS.items():
        if any(h in counts for h in hints):
            return "research" if d == "study" else ("travel planning" if d == "travel" else d)
    return "productivity"


def _extract_keywords(tabs: List[Dict[str, Any]], limit: int = 6) -> List[str]:
    score = Counter()
    for t in tabs:
        title_tokens = _tokenize(t.get("title", ""))
        content_tokens = _tokenize((t.get("content", "") or "")[:600])
        url = t.get("url", "")
        parsed = urlparse(url)
        host_parts = [p for p in parsed.netloc.lower().split(".") if p and p not in {"www", "com", "org", "net", "co", "in"}]
        path_parts = _tokenize(parsed.path.replace("/", " "))

        for w in title_tokens:
            score[w] += 4
        for w in content_tokens[:40]:
            score[w] += 1
        for w in host_parts:
            score[w] += 2
        for w in path_parts:
            score[w] += 2

    keywords = [w for w, _ in score.most_common(limit * 2)]
    deduped = []
    for w in keywords:
        if not any(w in d or d in w for d in deduped):
            deduped.append(w)
        if len(deduped) >= limit:
            break
    return deduped or ["browsing", "research"]


def _representative_tabs(tabs: List[Dict[str, Any]], keywords: List[str], limit: int = 3) -> List[str]:
    if not tabs:
        return []
    keyset = set(keywords)
    scored = []
    for t in tabs:
        title = t.get("title", "Untitled")
        toks = set(_tokenize(title))
        score = len(toks.intersection(keyset))
        if any(k in title.lower() for k in ["review", "compare", "guide", "tutorial", "official"]):
            score += 1
        scored.append((score, title))
    scored.sort(key=lambda x: x[0], reverse=True)
    picks = []
    for _, title in scored:
        if title not in picks:
            picks.append(title)
        if len(picks) >= limit:
            break
    return picks


def _semantic_title(domain: str, keywords: List[str], reps: List[str]) -> str:
    if reps:
        top = reps[0]
        if len(top) <= 60:
            return top
    base = " ".join(k.replace("-", " ") for k in keywords[:3]).strip()
    if not base:
        base = "Browsing Focus"
    if domain == "shopping":
        return f"Comparing {base.title()}"
    if domain == "study":
        return f"Researching {base.title()}"
    if domain == "travel":
        return f"Planning {base.title()} Trip"
    if domain == "code":
        return f"Working on {base.title()}"
    if domain == "entertainment":
        return f"Exploring {base.title()}"
    return f"Focused on {base.title()}"


def _semantic_summary(domain: str, intent: str, keywords: List[str], reps: List[str], tab_count: int) -> str:
    ktxt = ", ".join(keywords[:4])
    rtxt = "; ".join(reps[:2]) if reps else "multiple related pages"
    if domain == "shopping":
        return f"You are {intent} across {tab_count} tabs, comparing {ktxt}. Representative pages include {rtxt}."
    if domain == "study":
        return f"These {tab_count} tabs focus on {ktxt}, likely for {intent}. Key references: {rtxt}."
    if domain == "travel":
        return f"This cluster captures {intent} activity around {ktxt} across {tab_count} tabs. Core pages: {rtxt}."
    if domain == "code":
        return f"You are in a {intent} workflow around {ktxt} using {tab_count} tabs, including {rtxt}."
    if domain == "entertainment":
        return f"These tabs indicate {intent} around {ktxt} with {tab_count} active pages like {rtxt}."
    return f"This cluster groups {tab_count} related tabs around {ktxt}, suggesting {intent}. Representative pages: {rtxt}."


def _build_semantic_cluster(cluster_id: int, domain: str, tabs: List[Dict[str, Any]]) -> Dict[str, Any]:
    all_tokens = []
    for t in tabs:
        all_tokens.extend(_tokenize(t.get("title", "")))
        all_tokens.extend(_tokenize((t.get("content", "") or "")[:300]))
    keywords = _extract_keywords(tabs)
    reps = _representative_tabs(tabs, keywords)
    intent = _infer_intent(domain, all_tokens)
    title = _semantic_title(domain, keywords, reps)
    summary = _semantic_summary(domain, intent, keywords, reps, len(tabs))

    confidence = min(0.98, 0.45 + min(0.4, len(tabs) * 0.05) + min(0.13, len(keywords) * 0.02))

    result = {
        "cluster_id": cluster_id,
        "domain": domain,
        "title": title,
        "summary": summary,
        "intent": intent,
        "keywords": keywords,
        "representative_tabs": reps,
        "tab_count": len(tabs),
        "tabs": tabs,
        "confidence": round(confidence, 2),
    }
    return result


def deterministic_cluster_tabs(tabs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    buckets: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for tab in tabs:
        text = f"{tab.get('title','')} {tab.get('url','')} {tab.get('content','')[:500]}"
        domain = _infer_domain(text)
        buckets[domain].append(tab)

    clusters: List[Dict[str, Any]] = []
    cid = 0
    for domain, grouped_tabs in sorted(buckets.items(), key=lambda x: len(x[1]), reverse=True):
        clusters.append(_build_semantic_cluster(cid, domain if domain in VALID_DOMAINS else "generic", grouped_tabs))
        clusters[-1]["fallback_mode"] = True
        print(
            f"[cluster-quality] id={cid} domain={clusters[-1]['domain']} intent={clusters[-1]['intent']} "
            f"confidence={clusters[-1]['confidence']} keywords={clusters[-1]['keywords'][:4]} fallback=True"
        )
        cid += 1

    if not clusters:
        clusters.append(_build_semantic_cluster(0, "generic", tabs))
        clusters[0]["fallback_mode"] = True

    return clusters


def deterministic_select_domain(tabs: List[Dict[str, Any]], user_prompt: str = "") -> Dict[str, str]:
    text = (user_prompt or "") + " " + " ".join(f"{t.get('title','')} {t.get('url','')}" for t in tabs[:20])
    domain = _infer_domain(text)
    return {"domain": domain, "reason": f"Detected {domain} intent from tab context"}


class LLMRouter:
    def __init__(self) -> None:
        self.groq = GroqService()
        self.gemini_key = os.getenv("GEMINI_API_KEY")

    def health(self) -> Dict[str, Any]:
        return {
            "groq_configured": bool(self.groq.api_key),
            "gemini_configured": bool(self.gemini_key),
        }

    async def _gemini_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        if not self.gemini_key:
            raise RuntimeError("GEMINI_API_KEY missing")

        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            "gemini-1.5-flash:generateContent?key=" + self.gemini_key
        )
        prompt = f"{system_prompt}\n\n{user_prompt}\n\nReturn only valid JSON."
        payload = {"contents": [{"parts": [{"text": prompt}]}]}

        start = time.perf_counter()
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload)
        elapsed = (time.perf_counter() - start) * 1000

        if resp.status_code >= 400:
            raise RuntimeError(f"Gemini HTTP {resp.status_code}: {resp.text[:300]}")

        data = resp.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        import json
        parsed = json.loads(text)
        parsed["_meta"] = {"provider": "gemini", "latency_ms": round(elapsed, 2)}
        return parsed

    async def cluster_tabs(self, tabs: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        system = (
            "Cluster tabs into 1-5 clusters. Return JSON with key `clusters` where each item has: "
            "cluster_id, tab_numbers (1-based), domain, title, summary, intent, keywords (array), representative_tabs (array). "
            "Domains must be one of: study/shopping/travel/code/entertainment/generic. "
            "Titles and summaries must be specific and contextual, never generic placeholders."
        )
        tab_list = "\n".join(
            f"{i+1}. {t.get('title','Untitled')} | {t.get('url','')} | {(t.get('content','') or '')[:180]}"
            for i, t in enumerate(tabs)
        )
        user = f"Tabs to cluster:\n{tab_list}"

        for provider in ["groq", "gemini"]:
            try:
                start = time.perf_counter()
                parsed = await (self.groq.chat_json(system, user, 1400) if provider == "groq" else self._gemini_json(system, user))
                latency = round((time.perf_counter() - start) * 1000, 2)
                raw = parsed.get("clusters", parsed)
                arr = raw if isinstance(raw, list) else [raw]

                clusters = []
                for idx, c in enumerate(arr):
                    nums = [n for n in c.get("tab_numbers", []) if isinstance(n, int) and 1 <= n <= len(tabs)]
                    selected_tabs = [tabs[n - 1] for n in nums]
                    if not selected_tabs:
                        continue
                    domain = c.get("domain", "generic")
                    if domain not in VALID_DOMAINS:
                        domain = "generic"

                    heur = _build_semantic_cluster(idx, domain, selected_tabs)
                    title = c.get("title") or heur["title"]
                    summary = c.get("summary") or heur["summary"]
                    intent = c.get("intent") or heur["intent"]
                    keywords = c.get("keywords") if isinstance(c.get("keywords"), list) else heur["keywords"]
                    reps = c.get("representative_tabs") if isinstance(c.get("representative_tabs"), list) else heur["representative_tabs"]

                    cluster = {
                        "cluster_id": idx,
                        "domain": domain,
                        "title": title,
                        "summary": summary,
                        "intent": intent,
                        "keywords": [str(k) for k in keywords][:6],
                        "representative_tabs": [str(x) for x in reps][:3],
                        "tab_count": len(selected_tabs),
                        "tabs": selected_tabs,
                        "confidence": heur["confidence"],
                        "fallback_mode": False,
                    }
                    print(
                        f"[cluster-quality] provider={provider} id={idx} intent={cluster['intent']} "
                        f"confidence={cluster['confidence']} keywords={cluster['keywords'][:4]} fallback=False"
                    )
                    clusters.append(cluster)

                if clusters:
                    return clusters, {"provider": provider, "fallback_mode": False, "latency_ms": latency}
            except Exception as e:
                print(f"[cluster-quality] provider={provider} failed: {e}")

        fallback_clusters = deterministic_cluster_tabs(tabs)
        return fallback_clusters, {"provider": "deterministic", "fallback_mode": True}

    async def select_domain(self, tabs: List[Dict[str, Any]], user_prompt: str) -> Tuple[Dict[str, str], Dict[str, Any]]:
        system = "Pick best domain from study/shopping/travel/code/entertainment/generic and return JSON {domain, reason}."
        tab_text = "\n".join(f"- {t.get('title','Untitled')}" for t in tabs[:20])
        user = f"User prompt: {user_prompt}\nTabs:\n{tab_text}"

        for provider in ["groq", "gemini"]:
            try:
                parsed = await (self.groq.chat_json(system, user, 300) if provider == "groq" else self._gemini_json(system, user))
                domain = parsed.get("domain", "generic")
                if domain not in VALID_DOMAINS:
                    domain = "generic"
                return {"domain": domain, "reason": parsed.get("reason", "")}, {"provider": provider, "fallback_mode": False}
            except Exception:
                pass

        return deterministic_select_domain(tabs, user_prompt), {"provider": "deterministic", "fallback_mode": True}

    async def summarize(self, text: str) -> Tuple[str, Dict[str, Any]]:
        system = "Summarize in 5 concise bullets. Return JSON {summary}."
        user = text[:7000]

        for provider in ["groq", "gemini"]:
            try:
                parsed = await (self.groq.chat_json(system, user, 800) if provider == "groq" else self._gemini_json(system, user))
                return parsed.get("summary", ""), {"provider": provider, "fallback_mode": False}
            except Exception:
                pass

        summary = "\n".join([f"- {line.strip()}" for line in text.splitlines()[:5] if line.strip()])
        return (summary or "- No content available."), {"provider": "deterministic", "fallback_mode": True}
