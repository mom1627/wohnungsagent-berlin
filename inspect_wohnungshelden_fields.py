"""Read-only inspection of the application iframe embedded in Gewobag listings.

No applicant data, no clicks on submit, no form submission.
"""
import asyncio
import json
from pathlib import Path
from urllib.parse import urlparse

OFFERS = [
 "https://www.gewobag.de/fuer-mietinteressentinnen/mietangebote/1000-00264-0102-0246",
 "https://www.gewobag.de/fuer-mietinteressentinnen/mietangebote/1000-00160-0202-0067",
]

async def main():
 from playwright.async_api import async_playwright
 results=[]
 async with async_playwright() as p:
  browser=await p.chromium.launch(headless=True)
  context=await browser.new_context(locale="de-DE")
  for url in OFFERS:
   result={"offer":url,"application_submitted":False}
   page=await context.new_page()
   try:
    await page.goto(url,wait_until="domcontentloaded",timeout=35000)
    await page.wait_for_timeout(3500)
    result["frames"]=[]
    for frame in page.frames:
     host=urlparse(frame.url).hostname or ""
     if host not in ("www.gewobag.de","app.wohnungshelden.de"):
      continue
     info={"host":host,"path":urlparse(frame.url).path}
     info["inputs"]=await frame.locator("input,textarea,select").evaluate_all("""els=>els.map(e=>({
       tag:e.tagName.toLowerCase(),type:e.getAttribute('type')||'',
       name:e.getAttribute('name')||'',id:e.id||'',
       placeholder:e.getAttribute('placeholder')||'',
       required:e.required||false,autocomplete:e.getAttribute('autocomplete')||''
     }))""")
     info["buttons"]=await frame.locator("button,[type=submit]").evaluate_all("""els=>els.map(e=>({
       text:(e.innerText||e.value||'').trim().slice(0,100),
       type:e.getAttribute('type')||''
     }))""")
     info["labels"]=await frame.locator("label").all_text_contents()
     info["labels"]=[x.strip()[:100] for x in info["labels"][:30]]
     result["frames"].append(info)
   except Exception as exc:
    result["error"]=type(exc).__name__+": "+str(exc)[:160]
   finally:
    await page.close()
   results.append(result)
  await browser.close()
 Path("wohnungshelden_field_report.json").write_text(json.dumps(results,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps(results,ensure_ascii=False,indent=2))
if __name__=="__main__":
 asyncio.run(main())
