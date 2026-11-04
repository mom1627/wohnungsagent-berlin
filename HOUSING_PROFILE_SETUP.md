# Protected housing profile

The agent reads APPLICANT_HOUSING_PROFILE from an encrypted repository Actions
secret. Applicant eligibility facts must never be committed to source files,
workflow inputs, artifacts or logs.

The JSON object must contain exactly these fields:

| Field | Type | Meaning |
| --- | --- | --- |
| salutation | string | An observed form option: Herr, Frau or Keine |
| household_size | integer | Number of occupants |
| apply_for_self | boolean | Applicant is making the request for themself |
| wbs_type | string | WBS category |
| wbs_valid_until | string | Expiry date in YYYY-MM-DD format |
| wbs_max_area_sqm | number | WBS-authorized dwelling area |
| wbs_special_need | boolean | Special housing need documented in WBS |
| wofg9_certificate | boolean | Separate section 9 certificate is held |
| enrolled | boolean | Enrollment certificate is currently held |
| immomio_account | boolean | An account already exists; no login credentials |

The three contact secrets APPLICANT_NAME, APPLICANT_EMAIL and APPLICANT_PHONE
remain unchanged. The workflow references the additional secret but never prints
or writes its value. An absent, corrupt or expired profile prevents dispatch.

A first legitimate qualifying request may validate the browser adapter. An
explicit visible success confirmation is required. A pending or uncertain
attempt is persisted before the submit click and permanently blocks retries for
that property. A new uncertain outcome pauses only that provider for the rest of
the current run; subsequent runs may try different eligible properties. Adapter validation is code-version-specific.

This setup does not establish eligibility for senior, student, wheelchair,
special-need or other restricted housing. The applicant must actually meet all
current property conditions. Jobcenter approval and income are never inferred.

STADT UND LAND additionally reads APPLICANT_EARLIEST_MOVE_IN (`ASAP` or an
explicit YYYY-MM-DD date) and APPLICANT_MONTHLY_NET_INCOME. The move-in secret
must be supplied from the user's confirmed answer; no default is invented.
Missing values disable this provider before applicant data is filled. Its
35-percent question receives the truthful mathematical answer, never an assumed
Jobcenter payment guarantee. New conditional requirements stop submission.
