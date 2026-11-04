from typing import TypedDict

from app.schemas.analysis import Analysis
from app.schemas.planning import TestPlan
from app.schemas.testcase import GeneratedTestCase


class CaseOutcome(TypedDict):
    """Everything known about one executed test case."""

    case: GeneratedTestCase
    result: dict  # CaseResult converted to a plain dict
    analysis: Analysis


class RunState(TypedDict, total=False):
    # inputs
    target_url: str
    instructions: str
    allowed_origins: list[str]

    # filled in by the nodes, in order
    plan: TestPlan
    pages: list[dict]
    test_cases: list[GeneratedTestCase]
    rejected_cases: list[dict]
    outcomes: list[CaseOutcome]
    bugs: list[dict]

    # progress and errors
    stage: str  # planning / exploring / generating / executing / done / failed
    errors: list[str]