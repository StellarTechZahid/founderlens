"""
Job store for the website. Each submission becomes a job that runs in a background thread.
State lives in memory for speed and is saved to outputs/<job_id>/ so reports survive a restart.
"""
import json
import os
import re
import threading
import time
import uuid

BASE = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE, "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

_lock = threading.Lock()
_jobs = {}
ID_RE = re.compile(r"^[a-f0-9]{12}$")

STAGES = ["queued", "evaluating", "researching", "pdf", "done"]


def valid_id(job_id: str) -> bool:
    return bool(job_id and ID_RE.match(job_id))


def job_dir(job_id):
    return os.path.join(OUTPUT_DIR, job_id)


def create(intake: dict) -> str:
    job_id = uuid.uuid4().hex[:12]
    os.makedirs(job_dir(job_id), exist_ok=True)
    with open(os.path.join(job_dir(job_id), "intake.json"), "w", encoding="utf-8") as f:
        json.dump(intake, f, indent=2, ensure_ascii=False)
    with _lock:
        _jobs[job_id] = {"status": "running", "stage": "queued", "research_done": 0,
                         "research_total": 4, "error": None, "started": time.time()}
    return job_id


def update(job_id, **kw):
    with _lock:
        if job_id in _jobs:
            _jobs[job_id].update(kw)


def get(job_id):
    """Current state of a job (falls back to disk so finished reports survive a restart)."""
    with _lock:
        job = _jobs.get(job_id)
        if job:
            snap = dict(job)
            snap["elapsed"] = int(time.time() - snap["started"])
            return snap
    if os.path.exists(os.path.join(job_dir(job_id), "result.json")):
        return {"status": "done", "stage": "done", "research_done": 4, "research_total": 4,
                "error": None, "elapsed": 0}
    return None


def save_result(job_id, result):
    with open(os.path.join(job_dir(job_id), "result.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)


def load_result(job_id):
    path = os.path.join(job_dir(job_id), "result.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
