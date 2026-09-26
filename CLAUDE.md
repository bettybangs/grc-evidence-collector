# GRC Evidence Collector

## Purpose
Portfolio project for GRC engineer roles: Python scripts that pull compliance
evidence from systems of record and save it as timestamped JSON.

## Rules
- Python + `requests` (GitHub) and `boto3` (AWS) only; keep code simple and readable
- Secrets from env vars only (GITHUB_TOKEN, AWS_ACCESS_KEY_ID,
  AWS_SECRET_ACCESS_KEY); never hardcode; .env in .gitignore
- Control mappings are hardcoded and verified, never AI-generated
- Handle API errors gracefully: record "not_applicable" or "error", don't crash

## Checks
1. GitHub default-branch protection
   Maps to: NIST SP 800-53 CM-3, SOC 2 CC8.1, ISO 27001:2022 A.8.32
   Note: free plan private repos return errors -> mark not_applicable
2. AWS IAM users with MFA (read-only SecurityAudit policy)
   Maps to: NIST SP 800-53 IA-2(1), IA-2(2), SOC 2 CC6.1, ISO 27001:2022 A.8.5
   Note: root MFA + console users must have MFA; API-only users listed, not failed
   Note: save user names only, never ARNs (keeps the account ID out)

## Done
- Weekly GitHub Actions schedule (both checks)
