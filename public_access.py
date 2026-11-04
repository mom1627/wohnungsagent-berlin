"""Public robots policy: failures are explicit, and fail closed."""
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser
from collect_inberlinwohnen import UA

def check_robots(url, cache):
    host = urlsplit(url).hostname
    if host not in cache:
        rp = RobotFileParser()
        try:
            with urlopen(Request("https://"+host+"/robots.txt",headers={"User-Agent":UA}),timeout=20) as r:
                rp.parse(r.read(200001).decode("utf-8","replace").splitlines())
        except HTTPError as exc:
            if exc.code == 404:
                rp.parse([])
            else:
                raise PermissionError("robots_unavailable") from None
        cache[host] = rp
    if not cache[host].can_fetch(UA,url):
        raise PermissionError("robots_disallowed")
