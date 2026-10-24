"""
Turns raw AI JSON into clean, complete structures.

Why this exists: the AI is good at judgement and writing, but unreliable at
arithmetic and at keeping a fixed list of 10 items in order. So the AI supplies
a 1-10 score + reasoning per criterion, and THIS file:
  * rebuilds the exact 10 criteria per market from framework.py (names/order
    always come from the framework, never from the AI),
  * clamps every score to 1-10,
  * computes market scores, the overall score and the verdict bands.
"""
import re
from decimal import Decimal, ROUND_HALF_UP

from framework import EVAL_PARAMS, RESEARCH_PARAMS, MARKETS, RECOMMENDATIONS

MISSING_TEXT = "The AI did not return an assessment for this item."


# ------------------------------- helpers ----------------------------------
def r1(x):
    """Round to 1 decimal, halves go UP (5.35 -> 5.4), so scores match hand calculation."""
    return float(Decimal(str(x)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def _to_int(value):
    try:
        return int(round(float(str(value).strip().split("/")[0])))
    except (TypeError, ValueError):
        return None


def _text(value, default=""):
    if value is None:
        return default
    if isinstance(value, (list, tuple)):
        return "; ".join(str(v).strip() for v in value if str(v).strip())
    return str(value).strip() or default


def _list(value, limit=6):
    if value is None:
        return []
    if isinstance(value, str):
        value = [value]
    out = []
    for item in value:
        if isinstance(item, dict):
            item = " - ".join(str(v) for v in item.values() if v)
        s = str(item).strip()
        if s:
            out.append(s)
    return out[:limit]


def _match_by_id_or_name(raw_items, definition):
    """Find the AI's entry for one framework parameter (by id, else by name)."""
    if not isinstance(raw_items, list):
        return None
    for item in raw_items:
        if isinstance(item, dict) and _to_int(item.get("id")) == definition["id"]:
            return item
    wanted = re.sub(r"\W+", "", definition["name"].lower())
    for item in raw_items:
        if isinstance(item, dict):
            got = re.sub(r"\W+", "", str(item.get("name", "")).lower())
            if got and (got == wanted or got in wanted or wanted in got):
                return item
    return None


# ------------------------------- bands ------------------------------------
def band(score):
    """Verdict wording for a 1-10 market/overall score."""
    if score is None:
        return "Not scored"
    if score >= 8.0:
        return "Strong"
    if score >= 6.5:
        return "Promising"
    if score >= 5.0:
        return "Needs validation"
    if score >= 3.5:
        return "High risk"
    return "Weak"


def rating(score):
    """Word for a single criterion score."""
    if score is None:
        return "Not scored"
    if score >= 8:
        return "Strong"
    if score >= 6:
        return "Solid"
    if score >= 4:
        return "Uncertain"
    return "Weak"


# ---------------------------- evaluation ----------------------------------
def normalize_evaluation(raw: dict) -> dict:
    """Rebuild the evaluation with all 20 criteria and computed scores."""
    if not isinstance(raw, dict):
        raise ValueError("The evaluation reply was not a JSON object.")

    result = {
        "idea_summary": _text(raw.get("idea_summary"), "No summary returned."),
        "biggest_strength": _text(raw.get("biggest_strength"), "Not stated."),
        "biggest_risk": _text(raw.get("biggest_risk"), "Not stated."),
        "recommendation_reasoning": _text(raw.get("recommendation_reasoning"), ""),
        "priority_actions": _list(raw.get("priority_actions"), 5),
        "missing_items": 0,
    }

    rec = _text(raw.get("recommendation"))
    result["recommendation"] = next(
        (r for r in RECOMMENDATIONS if r.lower() == rec.lower()),
        next((r for r in RECOMMENDATIONS if rec and r.lower() in rec.lower()), None),
    )

    scored_any = False
    for market in MARKETS:
        block = raw.get(market) if isinstance(raw.get(market), dict) else {}
        raw_items = block.get("criteria")
        criteria = []
        for definition in EVAL_PARAMS[market]:
            item = _match_by_id_or_name(raw_items, definition) or {}
            score = _to_int(item.get("score"))
            if score is not None:
                score = max(1, min(10, score))
                scored_any = True
            else:
                result["missing_items"] += 1
            criteria.append({
                "id": definition["id"],
                "name": definition["name"],
                "score": score,
                "rating": rating(score),
                "rationale": _text(item.get("rationale"), MISSING_TEXT),
            })
        valid = [c["score"] for c in criteria if c["score"] is not None]
        market_score = r1(sum(valid) / len(valid)) if valid else None
        result[market] = {
            "summary": _text(block.get("summary"), ""),
            "criteria": criteria,
            "score": market_score,
            "verdict": band(market_score),
        }

    if not scored_any:
        raise ValueError("The AI reply contained none of the 20 evaluation scores.")

    scores = [result[m]["score"] for m in MARKETS if result[m]["score"] is not None]
    overall = r1(sum(scores) / len(scores)) if scores else None
    result["overall_score"] = overall
    result["overall_verdict"] = band(overall)
    if not result["recommendation"]:
        # Fall back to a recommendation derived from the score.
        result["recommendation"] = (
            "Proceed to build" if (overall or 0) >= 7.5 else
            "Validate further before building" if (overall or 0) >= 5.0 else
            "Pivot needed" if (overall or 0) >= 3.5 else
            "Do not proceed as-is"
        )
    return result


# ------------------------------ research ----------------------------------
def normalize_sections(raw_sections, market: str, ids):
    """Return the research sections for `ids` of one market, in framework order."""
    out = []
    for definition in RESEARCH_PARAMS[market]:
        if definition["id"] not in ids:
            continue
        item = _match_by_id_or_name(raw_sections, definition) or {}
        confidence = _text(item.get("confidence"), "Low").capitalize()
        if confidence not in ("Low", "Medium", "High"):
            confidence = "Low"
        found = bool(item)
        out.append({
            "id": definition["id"],
            "name": definition["name"],
            "findings": _list(item.get("findings"), 5) or ([] if found else [MISSING_TEXT]),
            "analysis": _text(item.get("analysis"), ""),
            "data_points": _list(item.get("data_points"), 4),
            "validate_next": _list(item.get("validate_next"), 4),
            "confidence": confidence,
        })
    return out


def normalize_risks(raw):
    out = []
    if isinstance(raw, list):
        for item in raw[:6]:
            if isinstance(item, dict):
                risk = _text(item.get("risk"))
                if risk:
                    out.append({"risk": risk, "mitigation": _text(item.get("mitigation"), "")})
            elif str(item).strip():
                out.append({"risk": str(item).strip(), "mitigation": ""})
    return out


def normalize_plan(raw):
    out = []
    if isinstance(raw, list):
        for item in raw[:8]:
            if isinstance(item, dict):
                action = _text(item.get("action"))
                if action:
                    out.append({"when": _text(item.get("when"), ""), "action": action})
            elif str(item).strip():
                out.append({"when": "", "action": str(item).strip()})
    return out


def assemble_research(parts):
    """Merge the four research replies into one structure.
    parts: list of (market, part, lo, hi, raw_dict) where part is "A" (areas 1-5) or "B" (6-10)."""
    research = {m: {"snapshot": "", "sections": [], "key_risks": [], "validation_plan": []} for m in MARKETS}
    for market, part, lo, hi, raw in parts:
        ids = set(range(lo + 1, hi + 1))
        research[market]["sections"] += normalize_sections(raw.get("sections"), market, ids)
        if part == "A":
            research[market]["snapshot"] = _text(raw.get("snapshot"))
        else:
            research[market]["key_risks"] = normalize_risks(raw.get("key_risks"))
            research[market]["validation_plan"] = normalize_plan(raw.get("validation_plan"))
    for market in MARKETS:
        research[market]["sections"].sort(key=lambda sec: sec["id"])
    return research
