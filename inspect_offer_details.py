"""Inspect public provider offer pages, without guessing eligibility.

Robots policy is checked separately for each provider. No authentication,
form submission, bypasses, or unverified matching claims.
"""
import json
import re
import sys
from html.parser import HTMLParser
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser
from pathlib import Path

UA = "WohnungsAgentBerlin/0.1"
ALLOWED = {"www.gewobag.de", "www.howoge.de"}
MAX_BYTES = 750_000

class DetailParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []
        self.jsonld = []
        self.capture_script = False
        self.script_data = []
    def handle_starttag(self, tag, attrs):
        if tag == "script" and dict(attrs).get("type", "").lower() == "application/ld+json":
            self.capture_script = True
            self.script_data = []
    def handle_data(self, data):
        if self.capture_script:
            self.script_data.append(data)
        else:
            self.text.append(data)
    def handle_endtag(self, tag):
        if tag == "script" and self.capture_script:
            try:
                self.jsonld.append(json.loads("".join(self.script_data)))
            except json.JSONDecodeError:
                pass
            self.capture_script = False

def inspect_url(url, robots_cache):
    parsed = urlsplit(url)
    result = {"url": url, "status": "unverified", "application_submitted": False}
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED:
        result["error"] = "Unapproved offer host"
        return result
    host = parsed.hostname
    try:
        if host not in robots_cache:
            rp = RobotFileParser()
            with urlopen(Request("https://" + host + "/robots.txt", headers={"User-Agent": UA}), timeout=15) as r:
                rp.parse(r.read(200_001).decode("utf-8", "replace").splitlines())
            robots_cache[host] = rp
        if not robots_cache[host].can_fetch(UA, url):
            result["error"] = "robots.txt disallows offer URL"
            return result
        with urlopen(Request(url, headers={"User-Agent": UA}), timeout=15) as r:
            final = urlsplit(r.geturl())
            if final.scheme != "https" or final.hostname != host:
                result["error"] = "Redirect outside approved host"
                return result
            data = r.read(MAX_BYTES + 1)
            if len(data) > MAX_BYTES:
                result["error"] = "Page too large"
                return result
            result["http_status"] = r.status
        p = DetailParser()
        p.feed(data.decode("utf-8", "replace"))
        visible = " ".join(" ".join(p.text).split())
        # Evidence snippets only, never classify as verified warm rent or WBS.
        patterns = {
            "rent_mentions": r".{0,55}(?:Warmmiete|Gesamtmiete|Bruttowarmmiete).{0,100}",
            "room_mentions": r".{0,40}(?:Zimmer|Räume).{0,70}",
            "wbs_mentions": r".{0,55}(?:WBS|Wohnberechtigungsschein).{0,110}",
            "district_mentions": r".{0,40}(?:Reinickendorf|Wedding|Mitte|Pankow).{0,70}",
            "application_mentions": r".{0,45}(?:bewerben|Bewerbung|Interessenten).{0,80}",
        }
        result["evidence"] = {
            key: [m.group(0) for m in list(re.finditer(regex, visible, re.I))[:5]]
            for key, regex in patterns.items()
        }
        result["jsonld_count"] = len(p.jsonld)
        result["status"] = "readable_unverified"
    except Exception as exc:
        result["error"] = type(exc).__name__ + ": " + str(exc)[:140]
    return result

def main():
    source = Path("inberlinwohnen_candidates.json")
    if not source.exists():
        raise SystemExit("Missing collector output")
    data = json.loads(source.read_text(encoding="utf-8"))
    cache = {}
    results = [inspect_url(item["url"], cache) for item in data["listings"][:30]]
    output = Path("inberlinwohnen_offer_evidence.json")
    output.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"total": len(results), "readable": sum(x["status"] == "readable_unverified" for x in results),
                      "blocked_or_failed": sum(x["status"] != "readable_unverified" for x in results),
                      "output": str(output), "applications_submitted": 0}, ensure_ascii=False))
    for x in results:
        print(x["status"] + " " + x["url"] + (" [" + x["error"] + "]" if "error" in x else ""))

if __name__ == "__main__":
    main()
