# FoundersLens

A website that takes a startup idea through a DNotifier workflow of two AI agents:

1. **evaluator-agent** scores 20 criteria (10 Pakistan, 10 Global) from 1 to 10.
2. **research-agent** researches 20 areas (10 Pakistan, 10 Global) in four parallel calls.

It then builds two PDFs: an **evaluation sheet** and a **research report**.
The 40 parameters come from your two PDFs and live in `framework.py`.

## Run it (Windows)
```
cd /d "D:\your\folder"
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python check_ai.py        (should print: AI reply: AI IS WORKING)
python app.py
```
Open http://localhost:5000

`.env` holds your DNotifier App ID and Secret. Rotate the secret in the DNotifier dashboard
if it was ever shared, then paste the new one into `.env`.

## Test without internet or credits
`python test_offline.py` uses a fake AI and checks the agents, score maths, PDFs, every page
and the background job. Expect `ALL CHECKS PASSED`.

## Files
- `framework.py` the 40 parameters (edit names/descriptions here)
- `agents/` the two agents and their prompts
- `workflow.py` the DNotifier workflow (observability on: see runs in the dashboard)
- `scoring.py` score maths and verdict bands (done in code, not by the AI)
- `pdf_reports.py` the two PDFs
- `app.py`, `templates/`, `static/` the website
- `demo_data.py` the sample report shown on /sample

## Notes
- Research is written from the model's knowledge, not live web data; estimates are labelled.
- Reports are saved in `outputs/<id>/` and open again at /report/<id>.
- If a run fails, the progress page shows why (usually: no OpenAI key added in the DNotifier dashboard).
