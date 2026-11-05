from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models import TestCase, TestEvidence, TestResult, TestSession, User
from app.db.session import get_db

router = APIRouter(prefix="/results", tags=["results"])

SHOTS_ROOT = Path("storage/screenshots").resolve()


class EvidenceOut(BaseModel):
    has_screenshot: bool
    final_url: str | None = None
    page_text: str | None = None
    api_calls: list = []
    validation_messages: list = []
    console_errors: list = []
    http_errors: list = []
    analysis_evidence: list = []


def _own_evidence(db: Session, result_id: int, user: User) -> TestEvidence:
    evidence = db.scalar(
        select(TestEvidence)
        .join(TestResult, TestEvidence.test_result_id == TestResult.id)
        .join(TestCase, TestResult.test_case_id == TestCase.id)
        .join(TestSession, TestCase.session_id == TestSession.id)
        .where(TestEvidence.test_result_id == result_id, TestSession.user_id == user.id)
    )
    if evidence is None:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return evidence


@router.get("/{result_id}/evidence", response_model=EvidenceOut)
def get_evidence(
    result_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ev = _own_evidence(db, result_id, user)
    extra = ev.extra or {}
    return EvidenceOut(
        has_screenshot=bool(ev.screenshot_path),
        final_url=extra.get("final_url"),
        page_text=extra.get("page_text"),
        api_calls=extra.get("api_calls", []),
        validation_messages=extra.get("validation_messages", []),
        console_errors=ev.console_logs or [],
        http_errors=ev.network_errors or [],
        analysis_evidence=extra.get("analysis_evidence", []),
    )


@router.get("/{result_id}/screenshot")
def get_screenshot(
    result_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ev = _own_evidence(db, result_id, user)
    if not ev.screenshot_path:
        raise HTTPException(status_code=404, detail="No screenshot")
    path = Path(ev.screenshot_path).resolve()
    if not path.is_relative_to(SHOTS_ROOT) or not path.is_file():
        raise HTTPException(status_code=404, detail="Screenshot not available")
    return FileResponse(path, media_type="image/png")