import re

from playwright.sync_api import Page

_INSPECT_JS = """
() => {
  const visible = (el) => {
    const r = el.getBoundingClientRect();
    const s = window.getComputedStyle(el);
    return r.width > 0 && r.height > 0 &&
           s.visibility !== 'hidden' && s.display !== 'none';
  };
  const text = (el) => (el.innerText || el.value || '').trim().slice(0, 80);
  const iconClass = (el) => {
    const icon = el.querySelector('i, svg');
    if (!icon) return null;
    const c = icon.getAttribute('class');
    return c ? c.slice(0, 80) : 'svg';
  };
  const pick = (el) => ({
    tag: el.tagName.toLowerCase(),
    id: el.id || null,
    name: el.getAttribute('name'),
    type: el.getAttribute('type'),
    placeholder: el.getAttribute('placeholder'),
    testid: el.getAttribute('data-testid'),
    aria: el.getAttribute('aria-label'),
    title: el.getAttribute('title'),
    classes: Array.from(el.classList),
    icon: iconClass(el),
    text: text(el),
    href: el.getAttribute('href'),
  });
  const all = (sel) => Array.from(document.querySelectorAll(sel)).filter(visible);

  return {
    url: location.href,
    title: document.title,
    inputs: all('input, textarea, select').map(pick),
    buttons: all('button, [role="button"], input[type="submit"]').map(pick),
    links: all('a[href]').map(pick),
    forms: Array.from(document.querySelectorAll('form')).filter(visible).map(f => ({
      id: f.id || null,
      action: f.getAttribute('action'),
      method: f.getAttribute('method'),
      field_count: f.querySelectorAll('input, textarea, select').length,
    })),
  };
}
"""

_SAFE_CLASS = re.compile(r"^[A-Za-z_][\w-]*$")


def _quote_ok(value: str | None) -> bool:
    return bool(value) and '"' not in value and "\n" not in value


def _candidates(el: dict) -> list[str]:
    tag = el["tag"]
    out: list[str] = []
    if _quote_ok(el.get("testid")):
        out.append(f'[data-testid="{el["testid"]}"]')
    if _quote_ok(el.get("id")):
        out.append(f'[id="{el["id"]}"]')
    if _quote_ok(el.get("name")):
        out.append(f'{tag}[name="{el["name"]}"]')
    if _quote_ok(el.get("aria")):
        out.append(f'{tag}[aria-label="{el["aria"]}"]')
    if _quote_ok(el.get("title")):
        out.append(f'{tag}[title="{el["title"]}"]')
    if tag in ("button", "a") and _quote_ok(el.get("text")):
        out.append(f'{tag}:has-text("{el["text"]}")')
    if tag == "a" and _quote_ok(el.get("href")):
        out.append(f'a[href="{el["href"]}"]')
    if _quote_ok(el.get("placeholder")):
        out.append(f'{tag}[placeholder="{el["placeholder"]}"]')
    if tag == "input" and _quote_ok(el.get("type")):
        out.append(f'input[type="{el["type"]}"]')
    classes = [c for c in el.get("classes", []) if _SAFE_CLASS.match(c)]
    if classes:
        out.append(tag + "".join(f".{c}" for c in classes))
    return out


def _unique_selector(page: Page, el: dict) -> str | None:
    for sel in _candidates(el):
        try:
            if page.locator(sel).count() == 1:
                return sel
        except Exception:
            continue  # invalid selector, try the next candidate
    return None


def inspect_page(page: Page) -> dict:
    """Return a verified snapshot of the interactive elements on the page."""
    data = page.evaluate(_INSPECT_JS)
    for group in ("inputs", "buttons", "links"):
        for el in data[group]:
            el["selector"] = _unique_selector(page, el)
    return data