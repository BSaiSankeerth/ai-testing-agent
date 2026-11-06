import threading
from datetime import datetime, timezone

from app.agents.graph import build_graph
from app.core.config import get_settings
from app.db.models import TestSession
from app.db.session import SessionLocal
from app.llm.groq_client import GroqClient
from app.services.run_service import save_run

_run_lock = threading.Lock()


class RunnerBusy(Exception):
    """Another test run is already in progress."""


def create_pending_session(db, user_id: int, target_url: str, instructions: str) -> TestSession:
    session = TestSession(
        user_id=user_id,
        target_url=target_url,
        instructions=instructions,
        status="pending",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def _execute(session_id: int, user_id: int) -> None:
    settings = get_settings()
    try:
        with SessionLocal() as db:
            session = db.get(TestSession, session_id)
            started = datetime.now(timezone.utc)
            session.status = "running"
            session.started_at = started
            db.commit()
            try:
                graph = build_graph(
                    GroqClient(),
                    headless=settings.browser_headless,
                    slow_mo_ms=settings.browser_slow_mo_ms,
                )
                final = graph.invoke(
                    {
                        "session_id": session_id,
                        "target_url": session.target_url,
                        "instructions": session.instructions,
                        "allowed_origins": settings.approved_targets + settings.approved_api_origins,
                    }
                )
                save_run(db, user_id, final, started, session=session)
            except Exception as exc:
                db.rollback()
                session = db.get(TestSession, session_id)
                session.status = "failed"
                session.completed_at = datetime.now(timezone.utc)
                db.commit()
                print(f"[runner] session {session_id} crashed: {str(exc)[:300]}", flush=True)
    finally:
        _run_lock.release()


def start_run(session_id: int, user_id: int) -> None:
    """Start the run in a background thread. Raises RunnerBusy if one is active."""
    if not _run_lock.acquire(blocking=False):
        raise RunnerBusy("A test run is already in progress")
    thread = threading.Thread(target=_execute, args=(session_id, user_id), daemon=True)
    thread.start()