"""Inspect public Gewobag offer DOM for application entry points, without sending data."""
import asyncio
import json
from pathlib import Path
from urllib.parse import urlparse

URLS = [
    "https://www.gewobag.de/fuer-mietinteressentinnen/mietangebote/1000-00264-0102-0246",
    "https://www.gewobag.de/fuer-mietinteressentinnen/mietangebote/1000-00160-0202-0067",
]
KEYWORDS = ("bewerb", "anfrag", "interesse", "besichtig", "immomio", "kontakt")

async def main():
    from playwright.async_api import async_playwright
    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(locale="de-DE")
        for url in URLS:
            result = {"offer": url, "application_submitted": False}
            try:
                from urllib.robotparser import RobotFileParser
                from urllib.request import urlopen, Request
                robots = RobotFileParser()
                with urlopen(Request("https://www.gewobag.de/robots.txt", headers={"User-Agent":"WohnungsAgentBerlin/0.1"}), timeout=20) as r:
                    robots.parse(r.read(200001).decode("utf-8", "replace").splitlines())
                if not robots.can_fetch("WohnungsAgentBerlin/0.1", url):
                    raise PermissionError("robots.txt disallows offer page")
                page = await context.new_page()
                await page.goto(url, wait_until="domcontentloaded", timeout=35000)
                await page.wait_for_timeout(2500)
                result["page_title"] = (await page.title())[:140]
                result["final_host"] = urlparse(page.url).hostname
                if result["final_host"] != "www.gewobag.de":
                    raise ValueError("Unexpected redirect")
                elements = await page.locator("a,button,[role=button],iframe,form,input").evaluate_all("""els => els.map(e => ({
                    tag:e.tagName.toLowerCase(),
                    text:(e.innerText||e.getAttribute('aria-label')||'').trim().slice(0,140),
                    href:e.getAttribute('href')||'',
                    type:e.getAttribute('type')||'',
                    name:e.getAttribute('name')||'',
                    id:e.id||'',
                    src:e.tagName.toLowerCase()==='iframe'?(e.getAttribute('src')||''):''
                }))""")
                result["application_elements"] = [e for e in elements if any(k in json.dumps(e, ensure_ascii=False).lower() for k in KEYWORDS)][:35]
                result["forms_count"] = await page.locator("form").count()
                result["iframe_sources"] = [e["src"] for e in elements if e["tag"]=="iframe"][:10]
                await page.close()
            except Exception as exc:
                result["error"] = type(exc).__name__ + ": " + str(exc)[:180]
            results.append(result)
        await browser.close()
    Path("dynamic_application_inspection.json").write_text(json.dumps(results, ensure_ascii=False, indent=2)+"\n",encoding="utf-8")
    print(json.dumps(results,ensure_ascii=False,indent=2))

if __name__=="__main__":
    asyncio.run(main())
