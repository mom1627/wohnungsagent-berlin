# Public website integration (experimental)

This module can read schema.org JSON-LD metadata from public HTTPS pages that the operator explicitly configures and is permitted to access automatically. It does not interpret this metadata as a confirmed available rental, does not extract WBS status or warm rent, and does not apply.

## Configure
Under Settings > Secrets and variables > Actions > Variables, configure:
- PUBLIC_ALLOWED_HOSTS: exact approved hostnames, comma separated
- PUBLIC_LISTING_URLS: full HTTPS listing page URLs, one per line

Run Actions > Inspect approved public listing pages > Run workflow. Without configuration, the workflow safely exits without network access.

Before adding a host, check its robots.txt, terms, and whether automated requests are authorized. Never use private account URLs, credentials, session cookies or tokens. No CAPTCHA bypass, automated login, or protected profile access.

This is a building block, not a functioning housing crawler. Site-specific adapters, persistent cross-run deduplication, notification, and Immomio application integration remain unimplemented.
