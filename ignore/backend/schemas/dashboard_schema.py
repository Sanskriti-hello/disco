from __future__ import annotations

from typing import Any, Dict, List


def _as_list(value: Any) -> List[Any]:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def normalize_dashboard_payload(payload: Dict[str, Any], domain: str) -> Dict[str, Any]:
    """Normalize domain agent payload to a dynamic section-based dashboard composition."""
    safe = payload or {}

    title = safe.get("title") or safe.get("header", {}).get("title") or f"{domain.title()} Dashboard"
    summary = safe.get("summary") or safe.get("description") or ""

    widgets = _as_list(safe.get("widgets"))
    cards = _as_list(safe.get("cards"))
    actions = _as_list(safe.get("actions"))
    links = _as_list(safe.get("links"))
    metadata = safe.get("metadata") if isinstance(safe.get("metadata"), dict) else {}

    sections = []

    # 1. Hero Section
    sections.append({
        "type": "hero",
        "priority": "high",
        "content": {
            "title": title,
            "subtitle": summary,
            "actions": actions[:4]
        }
    })

    # 2. Add existing typed widgets directly as sections
    for w in widgets:
        if isinstance(w, dict):
            w_type = w.get("type", "generic-widget")
            sections.append({
                "type": w_type,
                "priority": "high",
                "content": w
            })

    # 3. Media Carousel (if we have cards with images)
    media_cards = [c for c in cards if isinstance(c, dict) and (c.get("image") or c.get("image_url"))]
    if media_cards:
        sections.append({
            "type": "media-carousel",
            "priority": "high",
            "content": {
                "title": "Media Gallery",
                "items": media_cards
            }
        })

    # 4. Product/Content Grid
    if cards:
        sections.append({
            "type": "content-grid",
            "priority": "medium",
            "content": {
                "title": "Items",
                "items": cards
            }
        })

    # 5. Recommendations / Links
    if links:
        sections.append({
            "type": "recommendations",
            "priority": "medium",
            "content": {
                "title": "Related Resources",
                "items": links
            }
        })
        
    # 6. Remaining Actions
    if len(actions) > 4:
        sections.append({
            "type": "quick-actions",
            "priority": "low",
            "content": {
                "title": "More Actions",
                "items": actions[4:]
            }
        })

    return {
        "theme": domain,
        "layout": "adaptive-grid",
        "sections": sections,
        "metadata": {"template_payload": safe, **metadata}
    }


def template_payload_from_normalized(normalized: Dict[str, Any]) -> Dict[str, Any]:
    metadata = normalized.get("metadata") or {}
    template_payload = metadata.get("template_payload")
    if isinstance(template_payload, dict) and template_payload:
        return template_payload

    # Minimal fallback
    return {
        "title": normalized.get("theme", "Dashboard").title(),
        "sections": normalized.get("sections", [])
    }
