"""Safe prerequisite check. Does not submit applications."""
import json
from application_profile import load_profile

def main():
    profile = load_profile()
    print(json.dumps({"contact_secrets_configured": profile["ready"],
                      "missing_secrets": profile.get("missing_secrets", []),
                      "submission_implemented": False,
                      "applications_submitted": 0}, ensure_ascii=False))
    if not profile["ready"]:
        print("Configure the missing GitHub Actions repository secrets.")
    print("Application submission is disabled until a permitted, tested provider-specific adapter exists.")

if __name__ == "__main__":
    main()
