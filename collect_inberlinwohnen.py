"""Read-only collection of directly linked housing offers on inBerlinWohnen.

No Livewire endpoint guessing, login, CAPTCHA bypass or applications.
Only links on the first publicly accessible HTML response are collected.
"""
import json
import re
import sys
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit, urlunsplit
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser
from pathlib import Path

ROOT = "https://www.inberlinwohnen.de"
FINDER = ROOT + "/wohnungsfinder"
UA = "WohnungsAgentBerlin/0.1"
PROVIDERS = {
    "www.gewobag.de": ("gewobag", re.compile(r"^/fuer-mietinteressentinnen/mietangebote/[^/]+/?$")),
    "www.howoge.de": ("howoge", re.compile(r"^/wohnungen-gewerbe/wohnungssuche/detail/[^/]+\.html$")),
}
class AnchorParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.links.append(href)

def collect():
    rp = RobotFileParser()
    with urlopen(Request(ROOT + "/robots.txt", headers={"User-Agent": UA}), timeout=20) as r:
        rp.parse(r.read(200_001).decode("utf-8", "replace").splitlines())
    if not rp.can_fetch(UA, FINDER):
        raise PermissionError("robots.txt does not permit this page")
    with urlopen(Request(FINDER, headers={"User-Agent": UA}), timeout=20) as r:
        if urlsplit(r.geturl()).hostname not in ("inberlinwohnen.de", "www.inberlinwohnen.de"):
            raise ValueError("Unexpected redirect")
        html = r.read(1_000_001)
    if len(html) > 1_000_000:
        raise ValueError("Page too large")
    parser = AnchorParser()
    parser.feed(html.decode("utf-8", "replace"))
    seen = set()
    results = []
    for href in parser.links:
        u = urlsplit(urljoin(FINDER, href))
        provider = PROVIDERS.get((u.hostname or "").lower())
        if not provider or not provider[1].match(u.path):
            continue
        normalized = urlunsplit(("https", u.hostname.lower(), u.path.rstrip("/"), "", ""))
        if normalized in seen:
            continue
        seen.add(normalized)
        results.append({
            "url": normalized, "provider": provider[0], "source": FINDER,
            "warm_rent_eur": None, "rooms": None, "district": None,
            "wbs_100_eligible": None, "application_open": None,
            "screening_status": "unverified",
        })
    return {"checked_at_utc": datetime.now(timezone.utc).isoformat(),
            "source": FINDER, "count": len(results), "listings": results}

def main():
    output = Path("inberlinwohnen_candidates.json")
    result = collect()
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Collected {result['count']} unverified direct offer links")
    for item in result["listings"]:
        print(item["provider"] + ": " + item["url"])
    print("No eligibility claims or applications; see artifact for structured results.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("Collection failed: " + type(e).__name__ + ": " + str(e), file=sys.stderr)
        sys.exit(1)
