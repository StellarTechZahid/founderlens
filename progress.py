"""Tiny hook so the agents can tell the website how far a job has got.
The web app registers a handler; the CLI/tests simply leave it unset."""
_handler = None


def set_handler(fn):
    global _handler
    _handler = fn


def report(job_id, **info):
    if job_id and _handler:
        try:
            _handler(job_id, **info)
        except Exception:  # progress must never break the pipeline
            pass
