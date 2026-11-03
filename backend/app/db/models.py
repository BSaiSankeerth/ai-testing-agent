from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    sessions: Mapped[list["TestSession"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class TestSession(Base):
    __tablename__ = "test_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    target_url: Mapped[str] = mapped_column(String(2048))
    instructions: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user: Mapped["User"] = relationship(back_populates="sessions")
    test_cases: Mapped[list["TestCase"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class TestCase(Base):
    __tablename__ = "test_cases"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("test_sessions.id"), index=True
    )
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    steps: Mapped[list] = mapped_column(JSON)
    expected_result: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(50))  # positive/negative/boundary
    priority: Mapped[str] = mapped_column(String(20), default="medium")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    session: Mapped["TestSession"] = relationship(back_populates="test_cases")
    results: Mapped[list["TestResult"]] = relationship(
        back_populates="test_case", cascade="all, delete-orphan"
    )


class TestResult(Base):
    __tablename__ = "test_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    test_case_id: Mapped[int] = mapped_column(
        ForeignKey("test_cases.id"), index=True
    )
    # passed / failed / blocked / inconclusive / error
    status: Mapped[str] = mapped_column(String(50))
    actual_result: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_details: Mapped[str | None] = mapped_column(Text, nullable=True)
    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    test_case: Mapped["TestCase"] = relationship(back_populates="results")
    evidence: Mapped[list["TestEvidence"]] = relationship(
        back_populates="result", cascade="all, delete-orphan"
    )
    bug_reports: Mapped[list["BugReport"]] = relationship(
        back_populates="result", cascade="all, delete-orphan"
    )


class TestEvidence(Base):
    __tablename__ = "test_evidence"

    id: Mapped[int] = mapped_column(primary_key=True)
    test_result_id: Mapped[int] = mapped_column(
        ForeignKey("test_results.id"), index=True
    )
    screenshot_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    console_logs: Mapped[list | None] = mapped_column(JSON, nullable=True)
    network_errors: Mapped[list | None] = mapped_column(JSON, nullable=True)
    extra: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    result: Mapped["TestResult"] = relationship(back_populates="evidence")


class BugReport(Base):
    __tablename__ = "bug_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    test_result_id: Mapped[int] = mapped_column(
        ForeignKey("test_results.id"), index=True
    )
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(20))  # critical/high/medium/low
    steps_to_reproduce: Mapped[list] = mapped_column(JSON)
    expected_result: Mapped[str] = mapped_column(Text)
    actual_result: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="open")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    result: Mapped["TestResult"] = relationship(back_populates="bug_reports")