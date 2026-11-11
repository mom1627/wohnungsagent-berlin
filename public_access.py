"""Public robots policy: failures are explicit, and fail closed."""
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from protego import Protego
from collect_inberlinwohnen import UA

def check_robots(url, cache):
    host = urlsplit(url).hostname
    if host not in cache:
        rules = ""
        try:
            with urlopen(Request("https://"+host+"/robots.txt",headers={"User-Agent":UA}),timeout=20) as r:
                data = r.read(500001)
                if len(data) > 500000:
                    raise PermissionError("robots_response_too_large")
                rules = data.decode("utf-8","replace")
        except HTTPError as exc:
            if exc.code not in (404, 410):
                raise PermissionError("robots_unavailable") from None
        cache[host] = Protego.parse(rules)
    if not cache[host].can_fetch(url,UA):
        raise PermissionError("robots_disallowed")
