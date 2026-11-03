import re
from collections import deque
from urllib.parse import urljoin, urlparse

from app.browser.inspector import inspect_page
from app.browser.manager import BrowserManager
from app.browser.url_guard import BlockedURLError, validate_url

_NUMERIC_SEGMENT = re.compile(r"/\d+(?=/|$)")
DEFAULT_FOCUS = ("login", "register", "signup", "sign up", "sign-up", "account")


def _clean(href: str, base: str) -> str:
    absolute = urljoin(base, href)
    return urlparse(absolute)._replace(fragment="", query="").geturl()


def _pattern(url: str) -> str:
    parsed = urlparse(url)
    return _NUMERIC_SEGMENT.sub("/{id}", parsed.path.rstrip("/") or "/")


def _is_focus(link: dict, keywords: tuple[str, ...]) -> bool:
    haystack = " ".join(
        str(link.get(k) or "") for k in ("href", "text", "aria", "title")
    ).lower()
    return any(k in haystack for k in keywords)


def explore(
    bm: BrowserManager,
    start_url: str,
    max_pages: int = 12,
    max_depth: int = 2,
    focus_keywords: tuple[str, ...] = DEFAULT_FOCUS,
) -> list[dict]:
    """Visit pages breadth-first and return verified element snapshots."""
    queue = deque([(start_url, 0)])
    seen_patterns: set[str] = set()
    pages: list[dict] = []

    while queue and len(pages) < max_pages:
        url, depth = queue.popleft()
        pattern = _pattern(url)
        if pattern in seen_patterns:
            continue
        seen_patterns.add(pattern)

        try:
            bm.goto(url)
        except BlockedURLError:
            continue
        except Exception as exc:  # navigation failure is recorded, not fatal
            pages.append({"url": url, "error": str(exc).splitlines()[0]})
            continue

        bm.page.wait_for_timeout(1000)

        # Redirect detection: where did we really land?
        final_pattern = _pattern(bm.page.url)
        redirected_from = None
        if final_pattern != pattern:
            redirected_from = url
            if final_pattern in seen_patterns:
                continue  # already explored this destination
            seen_patterns.add(final_pattern)

        snapshot = inspect_page(bm.page)
        snapshot["depth"] = depth
        snapshot["pattern"] = final_pattern
        snapshot["redirected_from"] = redirected_from
        pages.append(snapshot)

        if depth >= max_depth:
            continue

        priority, normal = [], []
        for link in snapshot["links"]:
            href = link.get("href")
            if not href or href.startswith(("mailto:", "tel:", "javascript:")):
                continue
            target = _clean(href, snapshot["url"])
            try:
                validate_url(target, bm.allowed_origins)
            except BlockedURLError:
                continue
            if _pattern(target) in seen_patterns:
                continue
            bucket = priority if _is_focus(link, focus_keywords) else normal
            bucket.append((target, depth + 1))

        for item in reversed(priority):
            queue.appendleft(item)
        queue.extend(normal)

    return pages