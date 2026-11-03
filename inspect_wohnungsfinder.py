"""Read-only inspection of public inBerlinWohnen finder pages.
Checks robots for each URL; prints safe structural diagnostics only.
"""
import json
import re
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser

ROOT = "https://inberlinwohnen.de"
PATHS = ("/wohnungsfinder", "/der-persoenliche-wohnungsfinder")
UA = "WohnungsAgentBerlin/0.1"

class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.forms = []
        self.scripts = []
        self.iframes = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "a" and a.get("href"):
            self.links.append(a["href"])
        elif tag == "form":
            self.forms.append({"method": a.get("method", "get"), "action": a.get("action", "")})
        elif tag == "script" and a.get("src"):
            self.scripts.append(a["src"])
        elif tag == "iframe" and a.get("src"):
            self.iframes.append(a["src"])

def inspect():
    rp = RobotFileParser()
    with urlopen(Request(ROOT + "/robots.txt", headers={"User-Agent": UA}), timeout=15) as response:
        rp.parse(response.read(200000).decode("utf-8", "replace").splitlines())
    reports = []
    for path in PATHS:
        url = ROOT + path
        entry = {"url": url, "robots_allowed": rp.can_fetch(UA, url)}
        if not entry["robots_allowed"]:
            reports.append(entry)
            continue
        try:
            with urlopen(Request(url, headers={"User-Agent": UA}), timeout=20) as response:
                final = response.geturl()
                if urlsplit(final).hostname not in ("inberlinwohnen.de", "www.inberlinwohnen.de"):
                    raise ValueError("Redirected to external host; not following for inspection")
                raw = response.read(1_000_001)
                if len(raw) > 1_000_000:
                    raise ValueError("Response too large")
                entry["status"] = response.status
                entry["final_url"] = final
                entry["content_type"] = response.headers.get("Content-Type", "")
            html = raw.decode("utf-8", "replace")
            parser = PageParser()
            parser.feed(html)
            entry["forms"] = parser.forms[:15]
            entry["iframes"] = parser.iframes[:15]
            entry["scripts"] = parser.scripts[:20]
            entry["housing_links"] = sorted(set(
                urljoin(final, href) for href in parser.links
                if any(term in href.lower() for term in ("wohnung", "angebot", "expose", "miet"))
            ))[:40]
            entry["has_jsonld"] = 'application/ld+json' in html
            entry["has_search_terms"] = {
                word: bool(re.search(word, html, re.I))
                for word in ("wohnungsangebot", "filter", "iframe", "immomio")
            }
        except Exception as exc:
            entry["error"] = type(exc).__name__ + ": " + str(exc)[:180]
        reports.append(entry)
    return reports

if __name__ == "__main__":
    print(json.dumps(inspect(), ensure_ascii=False, indent=2))
