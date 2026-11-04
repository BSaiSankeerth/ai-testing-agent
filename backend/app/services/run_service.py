from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.state import RunState
from app.db.models import (
    BugReport,
    TestCase,
    TestEvidence,
    TestResult,
    TestSession,
    User,
)

DEV_EMAIL = "dev@example.com"


def get_or_create_dev_user(db: Session) -> User:
    user = db.scalar(select(User).where(User.email == DEV_EMAIL))
    if user is None:
        user = User(email=DEV_EMAIL, full_name="Dev User", hashed_password="!disabled")
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def _result_status(outcome: dict) -> str:
    if outcome["result"]["status"] == "blocked":
        return "blocked"
    return outcome["analysis"].verdict


def _session_status(final: RunState) -> str:
    if final.get("stage") != "done":
        return "failed"
    incomplete = bool(final.get("rejected_cases")) or any(
        o["analysis"].reasoning.startswith("Analysis failed")
        for o in final.get("outcomes", [])
    )
    return "completed_with_gaps" if incomplete else "completed"


def save_run(
    db: Session,
    user_id: int,
    final: RunState,
    started_at: datetime,
    session: TestSession | None = None,
) -> TestSession:
    try:
        if session is None:
            session = TestSession(
                user_id=user_id,
                target_url=final["target_url"],
                instructions=final["instructions"],
                started_at=started_at,
            )
            db.add(session)
        session.status = _session_status(final)
        session.completed_at = datetime.now(timezone.utc)
        db.flush()

        result_ids: dict[str, int] = {}  # case title -> test_results.id

        for outcome in final.get("outcomes", []):
            case, res, analysis = outcome["case"], outcome["result"], outcome["analysis"]

            db_case = TestCase(
                session_id=session.id,
                title=case.title,
                description=case.description,
                steps=[s.model_dump() for s in case.steps],
                expected_result=case.expected_result,
                category=case.category,
                priority=case.priority,
            )
            db.add(db_case)
            db.flush()

            status = _result_status(outcome)
            db_result = TestResult(
                test_case_id=db_case.id,
                status=status,
                actual_result=analysis.reasoning,
                duration_ms=res["duration_ms"],
                error_details=(res["detail"] or None)
                if res["status"] in ("automation_error", "blocked")
                else None,
            )
            db.add(db_result)
            db.flush()
            result_ids.setdefault(case.title, db_result.id)

            db.add(
                TestEvidence(
                    test_result_id=db_result.id,
                    screenshot_path=res["screenshot"],
                    console_logs=res["console_errors"],
                    network_errors=res["http_errors"],
                    extra={
                        "final_url": res["final_url"],
                        "page_text": res["page_text"],
                        "api_calls": res["api_calls"],
                        "validation_messages": res["validation_messages"],
                        "unmet_expectations": res["unmet_expectations"],
                        "analysis_evidence": analysis.evidence_used,
                        "severity": analysis.severity,
                    },
                )
            )

        # Plan tasks that never became a runnable test case
        for rej in final.get("rejected_cases", []):
            db_case = TestCase(
                session_id=session.id,
                title=rej["title"],
                description="Test case was not generated or was rejected",
                steps=[],
                expected_result="Not generated",
                category="positive",
                priority="medium",
            )
            db.add(db_case)
            db.flush()
            db.add(
                TestResult(
                    test_case_id=db_case.id,
                    status="not_run",
                    error_details=rej["reason"],
                )
            )

        for item in final.get("bugs", []):
            result_id = result_ids.get(item["case_title"])
            if result_id is None:
                continue
            bug = item["bug"]
            db.add(
                BugReport(
                    test_result_id=result_id,
                    title=bug.title,
                    description=bug.description,
                    severity=bug.severity,
                    priority=bug.priority,
                    steps_to_reproduce=bug.steps_to_reproduce,
                    expected_result=bug.expected_result,
                    actual_result=bug.actual_result,
                )
            )

        db.commit()
        db.refresh(session)
        return session
    except Exception:
        db.rollback()
        raise