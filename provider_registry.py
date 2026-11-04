"""Explicit provider hosts. Only actual public offer-card links are followed."""
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

PROVIDERS = {"gewobag.de":"gewobag", "howoge.de":"howoge", "gesobau.de":"gesobau",
             "degewo.de":"degewo", "wbm.de":"wbm", "stadtundland.de":"stadtundland", "berlinovo.de":"berlinovo"}

def provider_for(url):
    u = urlsplit(url)
    if u.scheme != "https" or u.username or u.password or u.port not in (None,443):
        return None
    return PROVIDERS.get((u.hostname or "").removeprefix("www."))

def canonical_offer(url):
    """Preserve identity-bearing query parameters; remove known tracking only."""
    u = urlsplit(url)
    host = (u.hostname or "").lower().removeprefix("www.")
    path = u.path.rstrip("/")
    if host == "howoge.de":
        path = path.replace("/wohnungen-gewerbe/", "/immobiliensuche/")
    query = urlencode(sorted((k,v) for k,v in parse_qsl(u.query, keep_blank_values=True)
                            if not k.lower().startswith("utm_") and k.lower() not in {"t","fbclid","gclid"}))
    return urlunsplit(("https",host,path,query,""))
