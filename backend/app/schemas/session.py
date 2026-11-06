from datetime import datetime

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field


class SessionCreate(BaseModel):
    target_url: AnyHttpUrl
    instructions: str = Field(min_length=10, max_length=2000)


class BugOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    severity: str
    priority: str
    steps_to_reproduce: list
    expected_result: str
    actual_result: str
    status: str


class ResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    actual_result: str | None
    duration_ms: int | None
    error_details: str | None
    bug_reports: list[BugOut] = []


class CaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    category: str
    priority: str
    expected_result: str
    steps: list
    results: list[ResultOut] = []


class SessionSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    target_url: str
    instructions: str
    status: str
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    progress: dict | None = None


class SessionDetail(SessionSummary):
    test_cases: list[CaseOut] = []


class SessionStats(BaseModel):
    sessions: int
    test_cases: int
    passed: int
    failed: int
    inconclusive: int
    blocked: int
    error: int
    not_run: int