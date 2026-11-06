from app.db.models import TestSession
from app.db.session import SessionLocal


def report_progress(session_id: int | None, **fields) -> None:
    """Merge fields into the session's progress JSON. Never raises."""
    if session_id is None:
        return
    try:
        with SessionLocal() as db:
            session = db.get(TestSession, session_id)
            if session is None:
                return
            session.progress = {**(session.progress or {}), **fields}
            db.commit()
    except Exception as exc:
        print(f"[progress] could not save progress: {str(exc)[:150]}", flush=True)