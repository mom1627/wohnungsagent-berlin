# Authorized feed setup

The scheduled workflow checks at five UTC times per day. GitHub Actions schedules may be delayed or skipped; there is no guarantee of instant response.

This is a **read-only integration skeleton**, not a live portal integration. No housing source is configured by default. No applications or notifications are sent.

To enable a source, first verify that the source explicitly permits automated retrieval and that it provides a JSON array with the schema in sample_listings.json. Then configure repository **Settings > Secrets and variables > Actions > Variables**:
- HOUSING_FEED_URL: HTTPS URL of the authorized JSON feed
- FEED_ALLOWED_HOSTS: exact hostname of that feed (comma-separated if needed)

Do not enter credentials, tokens, applicant documents, or private profile details as Actions variables. Never put credentials in feed URLs.

The feed must explicitly mark WBS 100 eligibility and application-open status. Unknown values are excluded. The feed output is only candidate screening, not confirmation of current availability.

GitHub Actions runners do not retain local SQLite state between runs. Persistent deduplication and notifications are not implemented yet. Never interpret the same candidate on separate runs as a newly listed apartment without a persistent seen-store.

Immomio submission requires a separate authorized integration and portal-side confirmation. Do not bypass CAPTCHA or MFA.
