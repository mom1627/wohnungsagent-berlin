# Verified adapter status — 4 November 2026

No application has been sent or confirmed during development. Live sending is
disabled because no provider has passed a real submission/confirmation test.

## Public forms inspected in the browser

* Gewobag / Wohnungshelden: request tab must be opened. Visible required fields
  include salutation, first and last name, email, total occupants, who applies,
  §9(2) WoFG certificate question, mobile number and a combined factual-accuracy /
  privacy acknowledgement. The actual form includes invisible reCAPTCHA.
  WBS possession does not establish the separate certificate answer.
* HOWOGE: actual contact link redirects into a multistep application. Notices
  cover WBS, income (three times total rent), and credit checks. No income,
  acceptable credit status, additional certificate, or guarantor is asserted.
* GESOBAU, degewo, WBM, STADT UND LAND, berlinovo: public finder discovery is
  supported, but no sending adapter has been validated. Matching offers are
  reported as blocked, never silently discarded.

## Runtime guarantees

The daily workflow follows the site's real Next buttons until the last page
(up to 200 pages, with an explicit incomplete status if capped or repeated).
All seven provider domains are recognized. Only current public property details
can confirm rent, rooms, district, WBS category and availability. Generic WBS
wording remains unverified. A Jobcenter rental-cost approval is not presumed.

The SHA-256-keyed ledger lives at .agent-state/application-ledger.json on main
in this private repository. GitHub Contents API compare-and-swap writes provide
durability; a reservation must be written BEFORE a submit click. Pending and
ambiguous entries block retries permanently until manually investigated. Tokens,
applicant contacts and form values must never be stored. The production workflow
has one concurrency group and never cancels an in-flight application run.

ENABLE_LIVE_APPLICATIONS alone cannot authorize an unvalidated sender.
VERIFIED_SENDERS is empty. The old apply_gewobag entry point is disabled, so no
alternate script can accidentally use the unvalidated previous implementation.
