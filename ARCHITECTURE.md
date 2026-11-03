# WohnungsAgent Berlin — architecture and safety

## Status
MVP only. This repository does **not** contain a live crawler, cloud deployment, Immomio integration, or automatic application submission.

## Search profile
Single applicant; WBS 100; 1 room; Berlin-Reinickendorf, Wedding, Mitte, Pankow; maximum EUR 550 monthly warm rent. Cooperative entry costs should be low; the current conservative screening threshold is EUR 500 and is configurable per listing (not an authorization to pay).

## Planned pipeline
1. Obtain listing data only from sources whose access and automation rules permit it (official feeds, notifications, or authorized browser access).
2. Validate exact warm rent, room count, district, WBS 100 eligibility, open application status, cooperative fees, and deadlines.
3. Deduplicate listings persistently and recheck the original offer before action.
4. Generate an application draft from applicant-approved information.
5. Add a portal-specific integration only after testing permissions, login, MFA, and submission confirmation.
6. Log submission IDs and notify the applicant; never submit duplicates.

## Security
Never commit credentials, cookies, WBS documents, benefit statements, or personal identifiers. Use a secret manager and least-privilege access. Respect CAPTCHA/MFA and site terms. Do not claim submission unless confirmed by the portal. Obtain user approval for the final submission mode before enabling unattended sends. Do not sign leases or commit to payments.

## Run
`python -m unittest discover -s tests`
`python agent.py sample_listings.json`
