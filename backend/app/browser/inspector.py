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
  const pick = (el) => ({
    tag: el.tagName.toLowerCase(),
    id: el.id || null,
    name: el.getAttribute('name'),
    type: el.getAttribute('type'),
    placeholder: el.getAttribute('placeholder'),
    testid: el.getAttribute('data-testid'),
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


def _suggest_selector(el: dict) -> str | None:
    if el.get("testid"):
        return f'[data-testid="{el["testid"]}"]'
    if el.get("id"):
        return f'#{el["id"]}'
    if el.get("name"):
        return f'{el["tag"]}[name="{el["name"]}"]'
    if el.get("tag") == "button" and el.get("text"):
        return f'button:has-text("{el["text"]}")'
    if el.get("tag") == "a" and el.get("href"):
        return f'a[href="{el["href"]}"]'
    return None


def inspect_page(page: Page) -> dict:
    """Return a verified snapshot of the interactive elements on the page."""
    data = page.evaluate(_INSPECT_JS)
    for group in ("inputs", "buttons", "links"):
        for el in data[group]:
            el["selector"] = _suggest_selector(el)
    return data