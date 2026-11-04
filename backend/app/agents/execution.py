import time
from dataclasses import dataclass, field
from pathlib import Path

from app.agents.test_data import RunIdentity
from app.browser.manager import BrowserManager
from app.browser.tools import BrowserTools
from app.schemas.testcase import GeneratedTestCase

NEEDS_ACCOUNT = {"{{existing_email}}"}

_VALIDATION_JS = """
() => Array.from(document.querySelectorAll('input, textarea, select'))
    .filter(el => el.validationMessage)
    .map(el => ({
        field: el.getAttribute('placeholder') || el.name || el.type,
        message: el.validationMessage,
    }))
"""


@dataclass
class CaseResult:
    title: str
    status: str  # completed / inconclusive / automation_error / blocked
    detail: str = ""
    failed_step: int | None = None
    final_url: str = ""
    page_text: str = ""
    screenshot: str | None = None
    unmet_expectations: list[str] = field(default_factory=list)
    api_calls: list[dict] = field(default_factory=list)
    http_errors: list[dict] = field(default_factory=list)
    console_errors: list[dict] = field(default_factory=list)
    duration_ms: int = 0
    validation_messages: list[dict] = field(default_factory=list)


def _visits_signup(case: GeneratedTestCase) -> bool:
    return any(s.action == "goto" and "/signup" in (s.value or "") for s in case.steps)


def _uses_account(case: GeneratedTestCase) -> bool:
    return any(s.action == "fill" and s.value in NEEDS_ACCOUNT for s in case.steps) or (
        not _visits_signup(case)
        and any(s.action == "fill" and s.value == "{{unique_email}}" for s in case.steps)
    )


def order_cases(cases: list[GeneratedTestCase]) -> list[GeneratedTestCase]:
    def key(c: GeneratedTestCase):
        return (
            0 if _visits_signup(c) and c.category == "positive" else 1,
            0 if _visits_signup(c) else 1,
        )

    return sorted(cases, key=key)


def _registration_succeeded(api_calls: list[dict]) -> bool:
    return any(
        c["status"] in (200, 201)
        and ("/signup" in c["url"] or "regist" in c["url"])
        for c in api_calls
    )


def run_case(
    bm: BrowserManager,
    case: GeneratedTestCase,
    identity: RunIdentity,
    shots_dir: str = "storage/screenshots",
) -> CaseResult:
    if _uses_account(case) and not identity.registered:
        return CaseResult(case.title, "blocked", "Registration did not succeed in this run")

    bm.new_session()
    tools = BrowserTools(bm)
    marks = (len(bm.api_calls), len(bm.http_errors), len(bm.console_messages))
    result = CaseResult(case.title, "completed")
    started = time.time()

    for index, step in enumerate(case.steps):
        if step.action == "goto":
            try:
                bm.goto(step.value)
                bm.page.wait_for_timeout(800)
            except Exception as exc:
                result.status, result.failed_step = "automation_error", index
                result.detail = f"goto failed: {str(exc).splitlines()[0]}"
                break
        elif step.action in ("fill", "click"):
            if step.action == "fill":
                out = tools.fill(step.selector, identity.resolve(step.value))
            else:
                out = tools.click(step.selector)
            if out["status"] != "ok":
                result.status, result.failed_step = "automation_error", index
                result.detail = f"{step.action} {out['status']}: {out['detail']}"
                break
            if step.action == "click":
                bm.page.wait_for_timeout(1500)
        elif step.action == "expect_text":
            body = bm.page.inner_text("body")
            if step.value.lower() not in body.lower():
                result.unmet_expectations.append(f"text not found: {step.value!r}")
        elif step.action == "expect_url_contains":
            if step.value not in bm.page.url:
                result.unmet_expectations.append(f"url missing {step.value!r}: {bm.page.url}")

    if result.status == "completed" and result.unmet_expectations:
        result.status = "inconclusive"

    # --- evidence ---------------------------------------------------------
    result.final_url = bm.page.url
    result.page_text = bm.page.inner_text("body")[:1500]
    result.api_calls = [
        c for c in bm.api_calls[marks[0]:] if "refresh-token" not in c["url"]
    ]
    result.http_errors = bm.http_errors[marks[1]:]
    result.console_errors = [
        m for m in bm.console_messages[marks[2]:] if m["type"] == "error"
    ]
    # Fixed JavaScript written by us (not the LLM): reads the browser's own
    # form-validation messages, e.g. "Please fill out this field".
    result.validation_messages = bm.page.evaluate(_VALIDATION_JS)

    safe = "".join(ch if ch.isalnum() else "_" for ch in case.title)[:50]
    result.screenshot = bm.screenshot(Path(shots_dir) / f"{safe}.png")
    result.duration_ms = int((time.time() - started) * 1000)

    if _visits_signup(case) and _registration_succeeded(result.api_calls):
        identity.registered = True

    return result