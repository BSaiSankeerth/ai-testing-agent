from typing import Literal

from pydantic import BaseModel, Field, model_validator


class BugDraft(BaseModel):
    title: str = Field(max_length=150, description="Short, specific summary of the defect")
    description: str = Field(description="What is wrong and what impact it has on a user")
    severity: Literal["critical", "high", "medium", "low"]
    priority: Literal["urgent", "high", "normal", "low"]
    steps_to_reproduce: list[str] = Field(min_length=1, max_length=15)
    expected_result: str
    actual_result: str
    evidence: list[str] = Field(
        min_length=1,
        description="Specific observations from the recorded evidence, e.g. 'POST /login returned 200 for a wrong password'",
    )

    @model_validator(mode="after")
    def check_not_vague(self):
        if self.expected_result.strip().lower() == self.actual_result.strip().lower():
            raise ValueError("expected_result and actual_result must differ")
        return self