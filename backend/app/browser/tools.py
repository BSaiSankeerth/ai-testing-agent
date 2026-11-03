import re

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeout

from app.browser.manager import ActionLimitExceeded, BrowserManager

MAX_SELECTOR_LEN = 300
MAX_VALUE_LEN = 500
DESTRUCTIVE = re.compile(
    r"\b(delete|pay|place order|purchase|buy now)\b", re.IGNORECASE
)


class ToolRefused(Exception):
    """Internal: a validation rule rejected the request."""

    def __init__(self, status: str, detail: str):
        super().__init__(detail)
        self.status = status
        self.detail = detail


class BrowserTools:
    def __init__(self, manager: BrowserManager):
        self.bm = manager

    # --- validation ------------------------------------------------------
    def _resolve(self, selector: str):
        if not isinstance(selector, str) or not selector.strip():
            raise ToolRefused("error", "Selector must be a non-empty string")
        if len(selector) > MAX_SELECTOR_LEN or "\n" in selector:
            raise ToolRefused("error", "Selector is too long or multi-line")

        locator = self.bm.page.locator(selector)
        count = locator.count()
        if count == 0:
            raise ToolRefused("error", f"No element matches: {selector}")
        if count > 1:
            raise ToolRefused("error", f"{count} elements match (ambiguous): {selector}")
        if not locator.is_visible():
            raise ToolRefused("error", f"Element is not visible: {selector}")
        return locator

    def _run(self, action: str, selector: str, fn) -> dict:
        result = {"action": action, "selector": selector}
        try:
            locator = self._resolve(selector)
            self.bm._use_action()
            detail = fn(locator)
            result.update(status="ok", detail=detail, url=self.bm.page.url)
        except ToolRefused as exc:
            result.update(status=exc.status, detail=exc.detail)
        except ActionLimitExceeded as exc:
            result.update(status="blocked", detail=str(exc))
        except PlaywrightTimeout:
            result.update(status="error", detail="Timed out waiting for the element")
        except PlaywrightError as exc:
            result.update(status="error", detail=str(exc).splitlines()[0])
        return result

    # --- approved tools --------------------------------------------------
    def click(self, selector: str, approved: bool = False) -> dict:
        def do(locator):
            label = " ".join(
                filter(
                    None,
                    [
                        locator.inner_text(),
                        locator.get_attribute("aria-label"),
                        locator.get_attribute("title"),
                    ],
                )
            )
            if DESTRUCTIVE.search(label) and not approved:
                raise ToolRefused("needs_approval", f"Looks destructive: '{label}'")
            locator.click()
            return "clicked"

        return self._run("click", selector, do)

    def fill(self, selector: str, value: str) -> dict:
        def do(locator):
            if len(value) > MAX_VALUE_LEN:
                raise ToolRefused("error", "Value is too long")
            locator.fill(value)
            return "filled"

        return self._run("fill", selector, do)