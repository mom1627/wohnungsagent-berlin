"""Find visible application entry points on specific Gewobag listings.

Read-only. Does not submit personal data or automate login/CAPTCHA.
"""
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser

URLS = [
    "https://www.gewobag.de/fuer-mietinteressentinnen/mietangebote/1000-00264-0102-0246",
    "https://www.gewobag.de/fuer-mietinteressentinnen/mietangebote/1000-00160-0202-0067",
]
UA = "WohnungsAgentBerlin/0.1"

class FormAndLinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.anchors = []
        self.forms = []
        self.active_anchor = None
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a":
            self.active_anchor = {"href": attrs.get("href", ""), "text": ""}
        elif tag == "form":
            self.forms.append({"action": attrs.get("action", ""), "method": attrs.get("method", "get").lower()})
    def handle_data(self, data):
        if self.active_anchor is not None:
            self.active_anchor["text"] += data
    def handle_endtag(self, tag):
        if tag == "a" and self.active_anchor is not None:
            self.anchors.append(self.active_anchor)
            self.active_anchor = None

def main():
    rp = RobotFileParser()
    with urlopen(Request("https://www.gewobag.de/robots.txt", headers={"User-Agent": UA}), timeout=20) as r:
        rp.parse(r.read(200001).decode("utf-8", "replace").splitlines())
    results = []
    for url in URLS:
        result = {"offer": url, "application_submitted": False, "links": [], "forms": []}
        try:
            if not rp.can_fetch(UA, url):
                raise PermissionError("robots.txt disallows URL")
            with urlopen(Request(url, headers={"User-Agent": UA}), timeout=20) as r:
                final = urlsplit(r.geturl())
                if final.hostname != "www.gewobag.de" or final.scheme != "https":
                    raise ValueError("Unexpected redirect")
                html = r.read(900001)
                if len(html) > 900000:
                    raise ValueError("Page too large")
                result["http_status"] = r.status
            p = FormAndLinkParser()
            p.feed(html.decode("utf-8", "replace"))
            keywords = ("bewerb", "interesse", "anfrag", "kontakt", "immomio", "besichtig")
            result["links"] = [
                {"url": urljoin(url, a["href"]), "label": " ".join(a["text"].split())[:120]}
                for a in p.anchors
                if any(k in (a["text"] + " " + a["href"]).lower() for k in keywords)
                and urlsplit(urljoin(url, a["href"])).scheme in ("https", "http")
            ][:25]
            result["forms"] = p.forms[:10]
        except Exception as exc:
            result["error"] = type(exc).__name__ + ": " + str(exc)[:160]
        results.append(result)
    Path("gewobag_application_paths.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(results, ensure_ascii=False, indent=2))
if __name__ == "__main__":
    main()
