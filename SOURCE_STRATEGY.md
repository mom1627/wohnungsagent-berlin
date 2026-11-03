# Source strategy — Berlin housing agent

## Priority order
1. **inberlinwohnen.de** — primary discovery hub for Berlin's state-owned housing providers.
2. **Direct provider websites** — degewo, GESOBAU, Gewobag, HOWOGE, STADT UND LAND, WBM, berlinovo.
3. **Immomio** — application workflow where officially offered by a provider (GESOBAU documents this flow).
4. **Additional sources** — ImmoScout24, immowelt, Kleinanzeigen, and affordable cooperatives.

Sources are discovery targets, **not implemented or authorized scrapers**. Before building a site adapter, verify technical accessibility, terms, robots rules, rate limits, and allowed application methods. Prefer official feeds and supported alerts. Do not bypass login restrictions, CAPTCHAs, or anti-bot measures.

## Matching policy
- One applicant; WBS 100; 1 room.
- Berlin-Reinickendorf, Wedding, Mitte, Pankow.
- Warm rent at most EUR 550; exclude offers with unknown total warm rent.
- Exclude closed listings, incompatible WBS tiers, age-limited offers not confirmed eligible, member-only cooperative offers, and high upfront shares.
- Jobcenter has approved moving, **not necessarily the rent of a specific new apartment**. Flag each offer for separate cost approval as applicable.
- Deduplicate across portals by address + unit details when verified, not just URL.

## Application pipeline (not yet enabled)
1. Verify an active application route and applicant eligibility.
2. Prepare only truthful, user-approved application data.
3. Submit only on sites where permitted and after separately enabling that adapter.
4. Record portal receipt / confirmation; avoid duplicate submissions.
5. Stop on uncertain eligibility, CAPTCHA/MFA, unexpected documents, payment requests, or consent forms.

## Current state
Prototype source modules are not yet connected to these websites. No cloud deployment of live browsing, no authenticated portal session, no automatic applications, no notifications. GitHub Actions is only a candidate for periodic checks and may be delayed.
