from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.browser.url_guard import BlockedURLError, validate_url
from app.core.config import get_settings
from app.db.models import TestCase, TestResult, TestSession
from app.db.session import get_db
from app.schemas.session import (
    SessionCreate,
    SessionDetail,
    SessionStats,
    SessionSummary,
)
from app.services.run_service import get_or_create_dev_user
from app.services.runner import RunnerBusy, create_pending_session, start_run

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionSummary, status_code=202)
def create_session(payload: SessionCreate, db: Session = Depends(get_db)):
    settings = get_settings()
    target = str(payload.target_url)
    try:
        validate_url(target, settings.approved_targets)
    except BlockedURLError:
        raise HTTPException(status_code=403, detail="Target is not on the approved list")

    user = get_or_create_dev_user(db)
    session = create_pending_session(db, user.id, target.rstrip("/"), payload.instructions)
    try:
        start_run(session.id, user.id)
    except RunnerBusy:
        session.status = "failed"
        db.commit()
        raise HTTPException(status_code=409, detail="A test run is already in progress")
    return session


@router.get("", response_model=list[SessionSummary])
def list_sessions(db: Session = Depends(get_db)):
    return db.scalars(select(TestSession).order_by(TestSession.id.desc()).limit(50)).all()


@router.get("/stats", response_model=SessionStats)
def stats(db: Session = Depends(get_db)):
    counts = dict(
        db.execute(select(TestResult.status, func.count()).group_by(TestResult.status)).all()
    )
    return SessionStats(
        sessions=db.scalar(select(func.count()).select_from(TestSession)) or 0,
        test_cases=db.scalar(select(func.count()).select_from(TestCase)) or 0,
        passed=counts.get("passed", 0),
        failed=counts.get("failed", 0),
        inconclusive=counts.get("inconclusive", 0),
        blocked=counts.get("blocked", 0),
        error=counts.get("error", 0),
        not_run=counts.get("not_run", 0),
    )


@router.get("/{session_id}", response_model=SessionDetail)
def get_session(session_id: int, db: Session = Depends(get_db)):
    session = db.scalar(
        select(TestSession)
        .where(TestSession.id == session_id)
        .options(
            selectinload(TestSession.test_cases)
            .selectinload(TestCase.results)
            .selectinload(TestResult.bug_reports)
        )
    )
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session