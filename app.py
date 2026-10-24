"""
FoundersLens website.

Pages:   /  /framework  /how-it-works  /evaluate  /sample  /report/<id>  /processing/<id>
API:     POST /api/submit      -> starts a job, returns {job_id}
         GET  /api/status/<id> -> live progress for the processing page
Files:   /download/<id>/evaluation|research  -> the two PDFs

Run:  python app.py      then open  http://localhost:5000
"""
import asyncio
import json
import os
import re
import threading
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, send_file, abort

import jobs
import progress
from demo_data import build_demo_result
from framework import (EVAL_PARAMS, RESEARCH_PARAMS, MARKETS, MARKET_LABEL)
from main import run_pipeline, normalize_intake
from pdf_reports import build_pdfs, slugify

load_dotenv()

BASE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(BASE, "intake_schema.json"), "r", encoding="utf-8") as f:
    SCHEMA = json.load(f)

QUESTION_COUNT = sum(len(s["fields"]) for s in SCHEMA["sections"])
PIPELINE_TIMEOUT_SECONDS = 15 * 60
_slots = threading.BoundedSemaphore(int(os.environ.get("MAX_PARALLEL_JOBS", "2")))

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "founderslens-local-secret")
app.config["TEMPLATES_AUTO_RELOAD"] = True

# the agents report live progress into the job store
progress.set_handler(lambda job_id, **info: jobs.update(job_id, **info))


# ------------------------------- helpers ----------------------------------
def lens_geometry(pk, gl):
    """Numbers for the report's two-circle graphic (kept in Python so the template stays readable)."""
    r, d = 130, 150
    cx1, cx2, cy = 40 + r, 40 + r + d, 160

    def level(score):
        score = score or 0
        return round(cy + r - 2 * r * (score / 10.0), 1)

    return {"r": r, "cx1": cx1, "cx2": cx2, "cy": cy, "mid": (cx1 + cx2) / 2,
            "y_pk": level(pk), "y_gl": level(gl), "w": cx2 + r + 40, "h": cy + r + 70}


def report_context(result, job_id, is_sample=False):
    ev = result["evaluation"]
    return {
        "result": result,
        "ev": ev,
        "rs": result["research"],
        "intake": result["intake"],
        "job_id": job_id,
        "is_sample": is_sample,
        "geo": lens_geometry(ev["pakistan"]["score"], ev["global"]["score"]),
        "markets": MARKETS,
        "market_label": MARKET_LABEL,
    }


_sample_cache = {}


def sample_result():
    if "result" not in _sample_cache:
        result = build_demo_result()
        out = os.path.join(jobs.OUTPUT_DIR, "_sample")
        if not (os.path.exists(os.path.join(out, "evaluation_sheet.pdf"))
                and os.path.exists(os.path.join(out, "research_report.pdf"))):
            build_pdfs(result, out)
        _sample_cache["result"] = result
    return _sample_cache["result"]


def friendly_error(exc: Exception) -> str:
    msg = str(exc)
    low = msg.lower()
    if "returned nothing" in low or "send_ai" in low:
        return ("The AI model did not answer. Check that an OpenAI key is added in your DNotifier "
                "dashboard, that AI is enabled on your plan, and that you have AI requests left this month.")
    if "authentication" in low or "missing dnotifier" in low:
        return "DNotifier rejected the App ID or Secret. Check the .env file and try again."
    if isinstance(exc, asyncio.TimeoutError) or "timeout" in low:
        return "The run took too long and was stopped. Please try again."
    return msg[:400] or "Something went wrong while running the evaluation."


# --------------------------------- pages ----------------------------------
@app.route("/")
def home():
    ev = sample_result()["evaluation"]
    return render_template("home.html", page="home", question_count=QUESTION_COUNT,
                           eval_params=EVAL_PARAMS, research_params=RESEARCH_PARAMS,
                           sample_ev=ev, sample_lens=lens_geometry(ev["pakistan"]["score"], ev["global"]["score"]))


@app.route("/framework")
def framework_page():
    return render_template("framework.html", page="framework", eval_params=EVAL_PARAMS,
                           research_params=RESEARCH_PARAMS)


@app.route("/how-it-works")
def how_it_works():
    return render_template("how.html", page="how", question_count=QUESTION_COUNT)


@app.route("/evaluate")
def evaluate():
    with open(os.path.join(BASE, "intake_data", "sample_intake.json"), "r", encoding="utf-8") as f:
        example = json.load(f)
    return render_template("evaluate.html", page="evaluate", schema=SCHEMA,
                           question_count=QUESTION_COUNT, example=example)


@app.route("/sample")
def sample():
    result = sample_result()
    return render_template("report.html", page="sample", **report_context(result, "sample", is_sample=True))


@app.route("/report/<job_id>")
def report(job_id):
    if not jobs.valid_id(job_id):
        abort(404)
    result = jobs.load_result(job_id)
    if not result:
        state = jobs.get(job_id)
        if state and state["status"] in ("running", "error"):
            return render_template("processing.html", page="evaluate", job_id=job_id)
        abort(404)
    return render_template("report.html", page="report", **report_context(result, job_id))


@app.route("/processing/<job_id>")
def processing(job_id):
    if not jobs.valid_id(job_id) or not jobs.get(job_id):
        abort(404)
    return render_template("processing.html", page="evaluate", job_id=job_id)


# ---------------------------------- API -----------------------------------
def _collect(form):
    data = {}
    for section in SCHEMA["sections"]:
        for field in section["fields"]:
            if field["type"] == "checkbox_group":
                data[field["key"]] = [v.strip() for v in form.getlist(field["key"]) if v.strip()]
            else:
                data[field["key"]] = (form.get(field["key"]) or "").strip()
    return data


def _validate(data):
    errors = []
    for section in SCHEMA["sections"]:
        for field in section["fields"]:
            value = data.get(field["key"])
            if field.get("required") and not value:
                errors.append({"key": field["key"], "message": "This answer is required."})
            elif field["type"] == "email" and value and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", value):
                errors.append({"key": field["key"], "message": "Enter a valid email address."})
            elif field["type"] == "textarea" and field.get("required") and value and len(value) < 8:
                errors.append({"key": field["key"], "message": "Add a little more detail (at least 8 characters)."})
    return errors


def _worker(job_id, intake):
    with _slots:
        try:
            jobs.update(job_id, stage="evaluating")
            run_input = dict(normalize_intake(intake))
            run_input["_job_id"] = job_id

            async def go():
                return await asyncio.wait_for(run_pipeline(run_input), PIPELINE_TIMEOUT_SECONDS)

            result = asyncio.run(go())

            jobs.update(job_id, stage="pdf")
            result["intake"] = normalize_intake(intake)
            result["meta"] = {"id": job_id, "generated_at": datetime.now().strftime("%d %B %Y"),
                              "is_sample": False, "execution_id": result.pop("execution_id", None)}
            build_pdfs(result, jobs.job_dir(job_id))
            jobs.save_result(job_id, result)
            jobs.update(job_id, status="done", stage="done")
        except Exception as exc:  # noqa: BLE001 - shown to the user in plain words
            app.logger.exception("Job %s failed", job_id)
            jobs.update(job_id, status="error", error=friendly_error(exc), detail=str(exc)[:800])


@app.route("/api/submit", methods=["POST"])
def api_submit():
    data = _collect(request.form)
    errors = _validate(data)
    if errors:
        return jsonify({"ok": False, "errors": errors}), 400
    job_id = jobs.create(data)
    threading.Thread(target=_worker, args=(job_id, data), daemon=True).start()
    return jsonify({"ok": True, "job_id": job_id})


@app.route("/api/status/<job_id>")
def api_status(job_id):
    if not jobs.valid_id(job_id):
        return jsonify({"ok": False}), 404
    state = jobs.get(job_id)
    if not state:
        return jsonify({"ok": False}), 404
    return jsonify({"ok": True, **{k: state.get(k) for k in
                    ("status", "stage", "research_done", "research_total", "elapsed", "error", "detail")}})


@app.route("/download/<job_id>/<kind>")
def download(job_id, kind):
    if kind not in ("evaluation", "research"):
        abort(404)
    if job_id == "sample":
        result = sample_result()
        folder = os.path.join(jobs.OUTPUT_DIR, "_sample")
    else:
        if not jobs.valid_id(job_id):
            abort(404)
        folder, result = jobs.job_dir(job_id), jobs.load_result(job_id)
        if not result:
            abort(404)
    fname = "evaluation_sheet.pdf" if kind == "evaluation" else "research_report.pdf"
    path = os.path.join(folder, fname)
    if not os.path.exists(path):
        abort(404)
    slug = slugify(result["intake"].get("company_name"))
    nice = f"{slug}-{'evaluation-sheet' if kind == 'evaluation' else 'research-report'}.pdf"
    return send_file(path, as_attachment=True, download_name=nice, mimetype="application/pdf")


@app.errorhandler(404)
def not_found(_):
    return render_template("404.html", page="404"), 404


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    print(f"\n  FoundersLens is running: http://localhost:{port}\n")
    app.run(host="127.0.0.1", port=port, debug=False, threaded=True)
