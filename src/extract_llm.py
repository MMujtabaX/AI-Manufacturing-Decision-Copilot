"""LLM-based normalization layer.

Used ONLY where structured fields don't already answer the question (e.g.
free-text supplier notes mentioning an extra certification, a caveat on a
quotation, ambiguous MOQ language). This is where the brief's "AI is
necessary rather than decorative" criterion actually gets earned -- the
rule engine and ranker don't need AI, this extraction step does.

Defaults to Groq's free tier (fast, generous limits for a hackathon demo).
Falls back to a deterministic keyword extractor with abstention if no API
key is set or a call fails, so the demo never breaks without internet or
if you hit a rate limit mid-pitch.
"""
import os
import json
from typing import Optional
from .schema import ExtractedFact

SYSTEM_PROMPT = """You extract structured facts from short supplier/quotation
notes for a manufacturing sourcing tool. Rules:
- Only report a fact if it is explicitly supported by the text.
- If the text does not support an answer, set abstained=true and leave value empty.
- Quote the exact supporting snippet in source_snippet.
- Give a confidence score between 0 and 1.
- Respond ONLY with JSON matching this schema:
{"value": "...", "source_snippet": "...", "confidence": 0.0, "abstained": false}
"""


def _fallback_extract(field: str, text: str) -> dict:
    """No-API deterministic fallback: simple keyword presence check."""
    if not text:
        return {"value": "", "source_snippet": "", "confidence": 0.0, "abstained": True}
    lowered = text.lower()
    if field.lower() in lowered:
        idx = lowered.find(field.lower())
        snippet = text[max(0, idx - 20): idx + 40]
        return {"value": snippet.strip(), "source_snippet": snippet.strip(),
                "confidence": 0.4, "abstained": False}
    return {"value": "", "source_snippet": "", "confidence": 0.0, "abstained": True}


def extract_fact(supplier_id: str, field: str, text: Optional[str]) -> ExtractedFact:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or not text:
        result = _fallback_extract(field, text or "")
        return ExtractedFact(supplier_id=supplier_id, field=field, **result)

    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        resp = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Field to extract: {field}\n\nText:\n{text}"},
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )
        parsed = json.loads(resp.choices[0].message.content)
        return ExtractedFact(supplier_id=supplier_id, field=field, **parsed)
    except Exception as e:
        # Never let an API hiccup break the demo -- degrade to fallback and
        # say so, rather than crashing or silently returning nothing.
        result = _fallback_extract(field, text)
        result["source_snippet"] = (result["source_snippet"] + f" [LLM error, used fallback: {e}]").strip()
        return ExtractedFact(supplier_id=supplier_id, field=field, **result)
