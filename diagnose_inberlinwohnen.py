"""Read-only reachability and site-structure diagnostic for inBerlinWohnen.

This is not a scraper. It never logs in, bypasses access controls, or submits.
"""
import json
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser

BASE = "https://inberlinwohnen.de/"
USER_AGENT = "WohnungsAgentBerlin/0.1"

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.links.append(href)

def diagnose():
    result = {"site": BASE, "robots": "unknown", "homepage": "not_checked", "candidate_paths": []}
    robots_url = urljoin(BASE, "robots.txt")
    rp = RobotFileParser()
    try:
        with urlopen(Request(robots_url, headers={"User-Agent": USER_AGENT}), timeout=15) as r:
            rp.parse(r.read(200000).decode("utf-8", "replace").splitlines())
        result["robots"] = "allowed" if rp.can_fetch(USER_AGENT, BASE) else "disallowed"
    except Exception as exc:
        result["robots"] = "unavailable"
        result["robots_error"] = type(exc).__name__
    if result["robots"] != "allowed":
        return result
    try:
        with urlopen(Request(BASE, headers={"User-Agent": USER_AGENT}), timeout=15) as r:
            final = urlsplit(r.geturl())
            if final.hostname not in ("inberlinwohnen.de", "www.inberlinwohnen.de"):
                raise ValueError("Unexpected redirect host")
            data = r.read(1_000_001)
            if len(data) > 1_000_000:
                raise ValueError("Page too large")
            parser = Links()
            parser.feed(data.decode("utf-8", "replace"))
            paths = []
            for href in parser.links:
                absolute = urljoin(BASE, href)
                host = urlsplit(absolute).hostname
                if host in ("inberlinwohnen.de", "www.inberlinwohnen.de") and any(
                    term in absolute.lower() for term in ("wohnung", "miet", "angebot", "finder")
                ):
                    paths.append(absolute)
            result["homepage"] = "reachable"
            result["candidate_paths"] = sorted(set(paths))[:40]
    except Exception as exc:
        result["homepage"] = "unavailable"
        result["homepage_error"] = type(exc).__name__
    return result

if __name__ == "__main__":
    print(json.dumps(diagnose(), ensure_ascii=False, indent=2))
