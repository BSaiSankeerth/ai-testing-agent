from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.browser.url_guard import BlockedURLError, validate_url
from app.core.config import get_settings
from app.db.models import TestCase, TestResult, TestSession, User
from app.db.session import get_db
from app.schemas.session import (
    SessionCreate,
    SessionDetail,
    SessionStats,
    SessionSummary,
)
from app.services.runner import RunnerBusy, create_pending_session, start_run

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionSummary, status_code=202)
def create_session(
    payload: SessionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    settings = get_settings()
    target = str(payload.target_url)
    try:
        validate_url(target, settings.approved_targets)
    except BlockedURLError:
        raise HTTPException(status_code=403, detail="Target is not on the approved list")

    session = create_pending_session(db, user.id, target.rstrip("/"), payload.instructions)
    try:
        start_run(session.id, user.id)
    except RunnerBusy:
        db.delete(session)  # don't leave a stray failed row behind
        db.commit()
        raise HTTPException(status_code=409, detail="A test run is already in progress")
    return session


@router.get("", response_model=list[SessionSummary])
def list_sessions(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.scalars(
        select(TestSession)
        .where(TestSession.user_id == user.id)
        .order_by(TestSession.id.desc())
        .limit(50)
    ).all()


@router.get("/stats", response_model=SessionStats)
def stats(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    counts = dict(
        db.execute(
            select(TestResult.status, func.count())
            .join(TestCase, TestResult.test_case_id == TestCase.id)
            .join(TestSession, TestCase.session_id == TestSession.id)
            .where(TestSession.user_id == user.id)
            .group_by(TestResult.status)
        ).all()
    )
    return SessionStats(
        sessions=db.scalar(
            select(func.count()).select_from(TestSession).where(TestSession.user_id == user.id)
        )
        or 0,
        test_cases=db.scalar(
            select(func.count())
            .select_from(TestCase)
            .join(TestSession, TestCase.session_id == TestSession.id)
            .where(TestSession.user_id == user.id)
        )
        or 0,
        passed=counts.get("passed", 0),
        failed=counts.get("failed", 0),
        inconclusive=counts.get("inconclusive", 0),
        blocked=counts.get("blocked", 0),
        error=counts.get("error", 0),
        not_run=counts.get("not_run", 0),
    )


@router.get("/{session_id}", response_model=SessionDetail)
def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session = db.scalar(
        select(TestSession)
        .where(TestSession.id == session_id, TestSession.user_id == user.id)
        .options(
            selectinload(TestSession.test_cases)
            .selectinload(TestCase.results)
            .selectinload(TestResult.bug_reports)
        )
    )
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session