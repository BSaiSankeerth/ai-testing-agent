from pathlib import Path

from playwright.sync_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    Route,
    sync_playwright,
)

from app.browser.url_guard import BlockedURLError, validate_url


class ActionLimitExceeded(Exception):
    """Raised when a session performs more actions than allowed."""

#
class BrowserManager:
    def __init__(
        self,
        allowed_origins: list[str],
        headless: bool = True,
        timeout_ms: int = 10_000,
        max_actions: int = 100,
        slow_mo_ms: int = 0,
    ):
        self.allowed_origins = allowed_origins
        self.headless = headless
        self.timeout_ms = timeout_ms
        self.max_actions = max_actions
        self.slow_mo_ms = slow_mo_ms

        self.actions_used = 0
        self.console_messages: list[dict] = []
        self.network_errors: list[dict] = []
        self.blocked_requests: list[str] = []
        self.http_errors: list[dict] = []
        self.api_calls: list[dict] = []  # every non-GET response, any status

        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self.page: Page | None = None

    # --- lifecycle -------------------------------------------------------
    def start(self) -> "BrowserManager":
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(
            headless=self.headless, slow_mo=self.slow_mo_ms
        )
        self.new_session()
        return self

    def new_session(self) -> None:
        """Open a clean, logged-out context. Collected logs are kept."""
        if self._context:
            self._context.close()
        self._context = self._browser.new_context(
            viewport={"width": 1280, "height": 800}
        )
        self._context.set_default_timeout(self.timeout_ms)
        self._context.route("**/*", self._guard_route)

        self.page = self._context.new_page()
        self.page.on("console", self._on_console)
        self.page.on("requestfailed", self._on_request_failed)
        self.page.on("response", self._on_response)

    def stop(self) -> None:
        if self._context:
            self._context.close()
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()
        self._context = self._browser = self._playwright = self.page = None

    def __enter__(self) -> "BrowserManager":
        return self.start()

    def __exit__(self, *exc) -> None:
        self.stop()

    # --- guards and listeners -------------------------------------------
    def _guard_route(self, route: Route) -> None:
        url = route.request.url
        if url.startswith(("data:", "blob:", "about:")):
            route.continue_()
            return
        try:
            validate_url(url, self.allowed_origins)
            route.continue_()
        except BlockedURLError:
            self.blocked_requests.append(url)
            route.abort()

    def _on_console(self, message) -> None:
        self.console_messages.append({"type": message.type, "text": message.text})

    def _on_request_failed(self, request) -> None:
        self.network_errors.append({"url": request.url, "failure": request.failure})

    def _on_response(self, response) -> None:
        entry = {
            "url": response.url,
            "status": response.status,
            "method": response.request.method,
        }
        if response.status >= 400:
            self.http_errors.append(entry)
        if entry["method"] != "GET":
            self.api_calls.append(entry)

    def _use_action(self) -> None:
        if self.actions_used >= self.max_actions:
            raise ActionLimitExceeded(f"Limit of {self.max_actions} actions reached")
        self.actions_used += 1

    # --- basic actions ---------------------------------------------------
    def goto(self, url: str) -> str:
        validate_url(url, self.allowed_origins)
        self._use_action()
        self.page.goto(url)
        return self.page.title()

    def screenshot(self, path: str | Path) -> str:
        self._use_action()
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.page.screenshot(path=str(path))
        return str(path)