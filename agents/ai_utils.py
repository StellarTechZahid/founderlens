"""Shared helpers for both agents: AI call + JSON extraction + one automatic retry."""
import asyncio
import json
import os
import re


# --------------------------- response parsing -----------------------------
def _find_content(obj, depth=0):
    """Recursively find the first non-empty 'content' (or 'text') string in a response."""
    if depth > 6 or obj is None:
        return None
    if isinstance(obj, str):
        return obj if obj.strip() else None
    if isinstance(obj, dict):
        for key in ("content", "text", "answer", "message"):
            val = obj.get(key)
            if isinstance(val, str) and val.strip():
                return val
        for key in ("data", "response", "result", "choices", "output"):
            if key in obj:
                found = _find_content(obj[key], depth + 1)
                if found:
                    return found
        for val in obj.values():
            found = _find_content(val, depth + 1)
            if found:
                return found
    if isinstance(obj, list):
        for item in obj:
            found = _find_content(item, depth + 1)
            if found:
                return found
    return None


def extract_ai_text(resp) -> str:
    """Pull plain text out of a ctx.send_ai(...) response."""
    if resp is None:
        raise RuntimeError(
            "DNotifier send_ai returned nothing. Check the error printed just above "
            "('error in send_ai: ...') - usually: no OpenAI key added in the DNotifier "
            "dashboard, AI not enabled on your plan, or the monthly AI limit is reached."
        )
    text = _find_content(resp)
    if not text:
        raise RuntimeError(f"Could not find any text in the AI response: {str(resp)[:500]}")
    return text


def extract_json(text: str):
    """Parse the JSON object out of a model reply (handles ```json fences and extra prose).
    Returns None if nothing parses."""
    if not text:
        return None
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    candidate = fenced.group(1) if fenced else text
    brace = re.search(r"\{.*\}", candidate, re.DOTALL)
    candidate = brace.group(0) if brace else candidate
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return None


def ai_kwargs() -> dict:
    """Provider/model sent with every AI call. Defaults match DNotifier's documented
    OpenAI integration (provider "open_ai", model "gpt-4o"). Override in .env with
    DNOTIFIER_AI_PROVIDER / DNOTIFIER_AI_MODEL if you use a different one."""
    provider = os.environ.get("DNOTIFIER_AI_PROVIDER", "").strip() or "open_ai"
    model = os.environ.get("DNOTIFIER_AI_MODEL", "").strip() or "gpt-4o"
    return {"provider": provider, "model": model}


# ------------------------------ the AI call --------------------------------
async def ask_json(ctx, system_prompt: str, user_prompt: str, label: str, attempts: int = 2):
    """
    Ask the model for a JSON object and return it as a dict.
    Retries once (with a firmer reminder) if the call fails or the reply is not valid JSON,
    because a single truncated reply should not ruin a whole report.
    """
    last_error = None
    for attempt in range(1, attempts + 1):
        reminder = "" if attempt == 1 else (
            "\n\nIMPORTANT: your previous reply could not be parsed. Reply with ONE complete, "
            "valid JSON object only - no markdown, no commentary - and keep every text field short."
        )
        try:
            response = await ctx.send_ai(
                message={
                    "useKnowledgeBase": False,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt + reminder},
                    ],
                },
                save_history=False,
                label=label if attempt == 1 else f"{label} (retry)",
                **ai_kwargs(),
            )
            data = extract_json(extract_ai_text(response))
            if isinstance(data, dict):
                return data
            last_error = RuntimeError("The AI reply was not valid JSON.")
        except Exception as exc:  # noqa: BLE001 - we re-raise after the last attempt
            last_error = exc
        if attempt < attempts:
            await asyncio.sleep(2)
    raise RuntimeError(f"{label} failed after {attempts} attempts: {last_error}")
