from typing import Literal

from pydantic import BaseModel, Field, model_validator


class Analysis(BaseModel):
    verdict: Literal["passed", "failed", "inconclusive", "error"]
    reasoning: str = Field(description="Short explanation comparing expected and actual behavior")
    evidence_used: list[str] = Field(
        default_factory=list,
        description="Specific evidence supporting the verdict, e.g. 'POST /login returned 409'",
    )
    is_application_defect: bool = Field(
        description="True only if the evidence shows the application itself misbehaved"
    )
    severity: Literal["critical", "high", "medium", "low", "none"] = "none"

    @model_validator(mode="after")
    def check_consistency(self):
        if self.verdict == "failed" and not self.evidence_used:
            raise ValueError("A 'failed' verdict must cite evidence")
        if self.verdict in ("passed", "error", "inconclusive") and self.is_application_defect:
            raise ValueError(f"A '{self.verdict}' verdict cannot be an application defect")
        if self.verdict == "failed" and not self.is_application_defect:
            raise ValueError("A 'failed' verdict must be an application defect")
        return self