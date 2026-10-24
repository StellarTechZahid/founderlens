"""
Pipeline runner + command-line entry.

    python main.py intake_data/sample_intake.json     -> runs the two agents, writes both PDFs to outputs/
"""
import asyncio
import json
import os
import sys

from dotenv import load_dotenv
from dnotifier import DNotifier

from workflow import founderslens_workflow
from pdf_reports import build_pdfs, slugify

load_dotenv()

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs")


def normalize_intake(raw: dict) -> dict:
    """Checkbox answers arrive as lists; flatten them to readable text for the AI prompts."""
    data = dict(raw)
    for key in ("progress_so_far", "needs_most"):
        if isinstance(data.get(key), list):
            data[key] = ", ".join(data[key])
    return data


async def run_pipeline(intake: dict) -> dict:
    """Connect to DNotifier, run the workflow, return {intake, evaluation, research}."""
    app_id = os.environ.get("DNOTIFIER_APP_ID")
    secret = os.environ.get("DNOTIFIER_SECRET")
    user_id = os.environ.get("DNOTIFIER_USER_ID", "founderslens-system")
    if not app_id or not secret:
        raise RuntimeError(
            "Missing DNOTIFIER_APP_ID / DNOTIFIER_SECRET. Open the .env file in the project "
            "folder and paste your App ID and Secret from app.dnotifier.com."
        )

    notifier = DNotifier(app_id=app_id, secret=secret, transport="http", user_id=user_id)
    await notifier.connect()
    try:
        result = await notifier.run_workflow(workflow=founderslens_workflow, input_data=normalize_intake(intake))
    finally:
        await notifier.disconnect()

    # run_workflow returns {"result": <entry return>, "state": {...}, "executionId": "..."}
    output = result.get("result") if isinstance(result, dict) else None
    if not isinstance(output, dict) or "evaluation" not in output:
        raise RuntimeError(f"The workflow returned an unexpected result: {str(result)[:400]}")
    if isinstance(result, dict) and result.get("executionId"):
        output["execution_id"] = result["executionId"]
    return output


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <path-to-intake.json>")
        sys.exit(1)
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        intake = json.load(f)
    print("Running evaluator-agent and research-agent through DNotifier (1-3 minutes)...")
    result = asyncio.run(run_pipeline(intake))
    slug = slugify(result["intake"].get("company_name"))
    e, r = build_pdfs(result, OUTPUT_DIR, f"{slug}_evaluation_sheet.pdf", f"{slug}_research_report.pdf")
    print("\nDone.\n  Evaluation sheet:", e, "\n  Research report: ", r)


if __name__ == "__main__":
    main()
