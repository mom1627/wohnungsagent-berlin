# Private contact setup

The application agent must **never** commit applicant name, email, phone, identity
documents, or login credentials to source code or workflow artifacts.

In the private GitHub repository open Settings → Secrets and variables →
Actions → New repository secret. Add:
- `APPLICANT_NAME`: full name for application forms
- `APPLICANT_EMAIL`: email used for housing applications
- `APPLICANT_PHONE`: phone used for housing applications

Then run **Application contact preflight**. It reports only which secrets
are missing, never their values.

Default message is stored in `application_profile.py`.

**Important:** This is a contact-data preflight, not an application sender.
No applications are submitted. An approved provider-specific submission
adapter, duplicate prevention, offer eligibility checks, and confirmation
verification must be implemented and tested before enabling sending.
GitHub Actions secrets are exposed to workflow code, so restrict repository
collaborators and workflow write access. Avoid putting personal data in logs.
