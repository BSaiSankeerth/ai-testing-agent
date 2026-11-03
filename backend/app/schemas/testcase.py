from typing import Literal

from pydantic import BaseModel, Field, model_validator

ALLOWED_PLACEHOLDERS = {
    "{{unique_email}}",
    "{{unique_username}}",
    "{{valid_password}}",
    "{{wrong_password}}",
    "{{existing_email}}",
    "{{invalid_email}}",
    "{{empty}}",
}


class TestStep(BaseModel):
    action: Literal["goto", "fill", "click", "expect_text", "expect_url_contains"]
    selector: str | None = Field(default=None, description="Selector copied from the exploration data")
    value: str | None = Field(
        default=None,
        description="URL for goto, text for expect_*, or a {{placeholder}} for fill",
    )
    page_url: str | None = Field(
        default=None, description="Page the selector belongs to, copied from the exploration data"
    )

    @model_validator(mode="after")
    def check_required_fields(self):
        if self.action in ("fill", "click") and not self.selector:
            raise ValueError(f"'{self.action}' step needs a selector")
        if self.action in ("goto", "fill", "expect_text", "expect_url_contains") and self.value is None:
            raise ValueError(f"'{self.action}' step needs a value")
        if self.action == "fill" and self.value not in ALLOWED_PLACEHOLDERS:
            raise ValueError(
                f"fill value must be one of {sorted(ALLOWED_PLACEHOLDERS)}, got {self.value!r}"
            )
        return self


class GeneratedTestCase(BaseModel):
    title: str
    description: str | None = None
    category: Literal["positive", "negative", "boundary"]
    priority: Literal["high", "medium", "low"]
    steps: list[TestStep] = Field(min_length=1, max_length=25)
    expected_result: str = Field(description="What a correct application should do, in plain language")


class GeneratedTestSuite(BaseModel):
    test_cases: list[GeneratedTestCase] = Field(min_length=1, max_length=20)