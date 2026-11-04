# Automatic dispatch status

The Gewobag / Wohnungshelden browser adapter is implemented and covered by safety
regression tests. A real successful submission has not yet been confirmed for
version gewobag_browser_v2. The production workflow is configured for live
dispatch, but requires a valid APPLICANT_HOUSING_PROFILE encrypted Actions secret,
the three existing contact secrets, matching current property conditions and
an available durable remote ledger.

The first qualifying request is the authorized real validation attempt. Only a
new, explicit provider success message counts as confirmed. The same durable
record enables later automatic requests. An unresolved reservation or ambiguous
submission stops this adapter until reviewed, including across workflow runs.

Invisible reCAPTCHA scripts and badges do not alone block the normal form.
The adapter only uses the website's actual request button and its ordinary
verification flow. Visible challenges are not solved, and no CAPTCHA token,
fingerprint, request endpoint or session is manipulated.

Required field answers are read from the protected profile, not hard-coded
applicant values. Dynamic WBS fields are inspected after answering WBS possession.
The observed single-person / up-to-50-square-metre cluster is supported. Unknown
mandatory fields, changed acknowledgements, unavailable certificates and
unvalidated room clusters stop the form before submitting.

The observed Gewobag acknowledgement states accuracy of the supplied information
and awareness of its privacy notice. Its exact text is checked. No extra terms,
paid commitments, marketing subscriptions or additional consents are accepted.

HOWOGE and other providers remain read-only until their own sending contracts
have been implemented and validated. Immomio account ownership is profile
metadata only; no password or authentication session is stored by this code.
