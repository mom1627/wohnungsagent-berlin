"""Paginated public inBerlinWohnen discovery, honoring robots policy."""
from urllib.parse import urljoin,urlsplit,urlunsplit
from urllib.request import Request,urlopen
from urllib.robotparser import RobotFileParser
from collect_inberlinwohnen import ROOT,FINDER,UA,PROVIDERS,AnchorParser

def collect(max_pages=40):
    rp=RobotFileParser()
    with urlopen(Request(ROOT+"/robots.txt",headers={"User-Agent":UA}),timeout=20) as response:
        rp.parse(response.read(200001).decode("utf-8","replace").splitlines())
    results=[]
    seen=set()
    pages_checked=0
    for page in range(1,max_pages+1):
        url=FINDER+("?page="+str(page) if page>1 else "")
        if not rp.can_fetch(UA,url):
            break
        with urlopen(Request(url,headers={"User-Agent":UA}),timeout=20) as response:
            if urlsplit(response.geturl()).hostname not in ("www.inberlinwohnen.de","inberlinwohnen.de"):
                raise ValueError("unexpected_redirect")
            data=response.read(1000001)
        if len(data)>1000000:
            raise ValueError("page_too_large")
        parser=AnchorParser()
        parser.feed(data.decode("utf-8","replace"))
        pages_checked+=1
        page_hits=0
        for href in parser.links:
            target=urlsplit(urljoin(url,href))
            provider=PROVIDERS.get((target.hostname or "").lower())
            if not provider or not provider[1].match(target.path):
                continue
            page_hits+=1
            normalized=urlunsplit(("https",target.hostname.lower(),target.path.rstrip("/"),"",""))
            if normalized not in seen:
                seen.add(normalized)
                results.append({"url":normalized,"provider":provider[0],"source":url})
        if page>1 and page_hits==0:
            break
    return {"source":FINDER,"count":len(results),"pages_checked":pages_checked,"listings":results}
