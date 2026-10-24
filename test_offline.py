"""
Offline self-test. Uses a FAKE AI (no network, no credits) to prove that everything except the
live DNotifier connection works: both agents, the workflow, score maths, both PDFs, the website
pages, the background job and the downloads.

Run:  python test_offline.py
"""
import json
import os
import re
import shutil
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import main as main_module
from dnotifier.workflow.runner import WorkflowRunner
import demo_data
from framework import MARKETS, RESEARCH_SPLITS

CALLS = []


class FakeDNotifier:
    """Stands in for the real DNotifier client; its send_ai replies like a model would."""
    def __init__(self, app_id=None, secret=None, transport=None, user_id=None, **kw):
        self.app_id, self.auth_token, self.user_id = app_id, "fake-token", user_id

    async def connect(self):
        return None

    async def disconnect(self):
        return None

    async def send_ai(self, sender_id, message, save_history=True, session_id=None, provider=None, model=None):
        system = message["messages"][0]["content"]
        assert provider == "open_ai" and model == "gpt-4o", (provider, model)
        task = re.match(r"\[TASK:([A-Z_0-9]+)\]", system).group(1)
        CALLS.append(task)
        if task == "EVAL":
            body = demo_data.raw_eval()
        else:
            _, market, part = task.split("_")
            body = demo_data.raw_research(market.lower(), part)
        # reply the way models often do: prose + a fenced JSON block
        return {"data": {"content": "Sure, here is the JSON:\n```json\n" + json.dumps(body) + "\n```"}}

    async def run_workflow(self, workflow, input_data, sender_id=None):
        workflow.observability = False  # no network in the test
        return await WorkflowRunner(self, sender_id or self.user_id, workflow).run(input_data=input_data)


main_module.DNotifier = FakeDNotifier
os.environ.setdefault("DNOTIFIER_APP_ID", "test")
os.environ.setdefault("DNOTIFIER_SECRET", "test")

import logging
import app as web  # noqa: E402  (imported after the fake is installed)
web.app.logger.setLevel(logging.CRITICAL)  # the deliberate-failure test would otherwise print a traceback

ok = True


def check(name, cond, extra=""):
    global ok
    ok = ok and bool(cond)
    print(("PASS  " if cond else "FAIL  ") + name + (f"  {extra}" if extra and not cond else ""))


# 1) pipeline through the real workflow + agents ------------------------------------------------
import asyncio
intake = demo_data.sample_intake()
result = asyncio.run(main_module.run_pipeline(dict(intake)))
ev, rs = result["evaluation"], result["research"]
check("evaluator scored 20 criteria", len(ev["pakistan"]["criteria"]) == 10 and len(ev["global"]["criteria"]) == 10)
check("market + overall scores computed (5.8 / 4.9 / 5.4)", (ev["pakistan"]["score"], ev["global"]["score"], ev["overall_score"]) == (5.8, 4.9, 5.4))
check("verdict band", ev["overall_verdict"] == "Needs validation")
check("research has 10 areas per market", all(len(rs[m]["sections"]) == 10 for m in MARKETS))
check("research risks + 90-day plans present", all(rs[m]["key_risks"] and rs[m]["validation_plan"] and rs[m]["snapshot"] for m in MARKETS))
check("5 AI calls made (1 eval + 4 research)", len(CALLS) == 5 and CALLS.count("EVAL") == 1, str(CALLS))

# 2) score maths edge cases ----------------------------------------------------------------------
from scoring import normalize_evaluation, r1
raw = demo_data.raw_eval()
raw["pakistan"]["criteria"][0]["score"] = 99          # out of range
raw["pakistan"]["criteria"][1]["score"] = "7/10"      # odd format
del raw["global"]["criteria"][9]                       # missing item
e2 = normalize_evaluation(raw)
check("score clamped to 10", e2["pakistan"]["criteria"][0]["score"] == 10)
check("'7/10' parsed as 7", e2["pakistan"]["criteria"][1]["score"] == 7)
check("missing criterion handled, not crashed", e2["missing_items"] == 1 and e2["global"]["criteria"][9]["score"] is None)
check("half-up rounding (5.35 -> 5.4)", r1(5.35) == 5.4 and r1(4.25) == 4.3)
try:
    normalize_evaluation({"pakistan": {}, "global": {}})
    check("empty reply rejected", False)
except ValueError:
    check("empty reply rejected", True)

# 3) PDFs ------------------------------------------------------------------------------------------
from pdf_reports import build_pdfs
tmp = os.path.join(os.path.dirname(__file__), "outputs", "_test_pdfs")
shutil.rmtree(tmp, ignore_errors=True)
e_pdf, r_pdf = build_pdfs(result, tmp)
check("evaluation PDF written", os.path.getsize(e_pdf) > 8000 and open(e_pdf, "rb").read(4) == b"%PDF")
check("research PDF written", os.path.getsize(r_pdf) > 20000 and open(r_pdf, "rb").read(4) == b"%PDF")
# hostile text must not break the PDF
evil = json.loads(json.dumps(result))
evil["intake"]["company_name"] = "A&B <Test> \u0627\u0644\u0639\u0631\u0628\u064a\u0629 \U0001F680"
evil["evaluation"]["idea_summary"] = "5 < 6 & 7 > 3 <b>bold</b> </para>"
build_pdfs(evil, tmp)
check("PDF survives <, &, Arabic and emoji text", True)
shutil.rmtree(tmp, ignore_errors=True)

# 4) website ---------------------------------------------------------------------------------------
c = web.app.test_client()
for path in ("/", "/framework", "/how-it-works", "/evaluate", "/sample"):
    r = c.get(path)
    check(f"page {path} loads", r.status_code == 200 and b"FoundersLens" in r.data, str(r.status_code))
check("404 page", c.get("/nope").status_code == 404)
check("sample PDF download", c.get("/download/sample/evaluation").status_code == 200 and c.get("/download/sample/research").status_code == 200)

bad = c.post("/api/submit", data={"full_name": "x"})
check("validation rejects empty form", bad.status_code == 400 and len(bad.get_json()["errors"]) > 5)

form = dict(intake)
form["progress_so_far"] = ["Online research", "Talked to potential customers"]
form["needs_most"] = ["Complete Actionable Roadmap"]
r = c.post("/api/submit", data=form)
job = r.get_json()["job_id"]
check("submit starts a job", r.status_code == 200 and re.match(r"^[a-f0-9]{12}$", job))
status = {}
for _ in range(60):
    status = c.get(f"/api/status/{job}").get_json()
    if status["status"] != "running":
        break
    time.sleep(0.5)
check("job finished", status.get("status") == "done", str(status))
rep = c.get(f"/report/{job}")
check("report page renders with scores", rep.status_code == 200 and b"Needs validation" in rep.data and b"CropLink" in rep.data)
check("report shows 20 criteria and 20 research areas", rep.data.count(b'<details class="crit"') == 20 and rep.data.count(b'<details class="rs"') == 20)
check("PDF downloads work", c.get(f"/download/{job}/evaluation").status_code == 200 and c.get(f"/download/{job}/research").status_code == 200)
check("bad ids are rejected", c.get("/report/../../etc/passwd").status_code == 404 and c.get("/download/zzz/evaluation").status_code == 404)
from agents.evaluator_agent import build_user_prompt
prompt = build_user_prompt(main_module.normalize_intake(intake))
check("prompt excludes name/phone/email", intake["email"] not in prompt and intake["phone_number"] not in prompt and intake["full_name"] not in prompt)

# 5) a failing AI is reported clearly -----------------------------------------------------------------
class DeadAI(FakeDNotifier):
    async def send_ai(self, *a, **k):
        return None
main_module.DNotifier = DeadAI
r = c.post("/api/submit", data=form)
job2 = r.get_json()["job_id"]
for _ in range(80):
    st = c.get(f"/api/status/{job2}").get_json()
    if st["status"] != "running":
        break
    time.sleep(0.5)
check("AI failure surfaces a friendly error", st["status"] == "error" and "AI model did not answer" in (st["error"] or ""), str(st))

shutil.rmtree(os.path.join(web.jobs.OUTPUT_DIR, job), ignore_errors=True)
shutil.rmtree(os.path.join(web.jobs.OUTPUT_DIR, job2), ignore_errors=True)
print("\n" + ("ALL CHECKS PASSED" if ok else "SOME CHECKS FAILED"))
sys.exit(0 if ok else 1)
