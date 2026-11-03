from typing import Literal

from pydantic import BaseModel, Field


class PlanTask(BaseModel):
    feature: str = Field(description="Feature under test, e.g. 'login' or 'registration'")
    scenario: str = Field(description="One specific scenario to verify, e.g. 'login with a wrong password'")
    category: Literal["positive", "negative", "boundary"]
    priority: Literal["high", "medium", "low"]


class TestPlan(BaseModel):
    summary: str = Field(description="One or two sentences describing what will be tested")
    features: list[str] = Field(min_length=1, max_length=10)
    tasks: list[PlanTask] = Field(min_length=1, max_length=20)
    notes: str | None = Field(
        default=None,
        description="Assumptions or anything unclear in the instructions",
    )