# GRC Evidence Collector

## Purpose
Portfolio project for GRC engineer roles: Python scripts that pull compliance
evidence from systems of record and save it as timestamped JSON.

## Rules
- Python + `requests` only; keep code simple and readable
- Secrets from env vars only (GITHUB_TOKEN); never hardcode; .env in .gitignore
- Control mappings are hardcoded and verified, never AI-generated
- Handle API errors gracefully: record "not_applicable" or "error", don't crash

## Checks
1. GitHub default-branch protection
   Maps to: NIST SP 800-53 CM-3, SOC 2 CC8.1, ISO 27001:2022 A.8.32
   Note: free plan private repos return errors -> mark not_applicable

## Roadmap
- Weekly GitHub Actions schedule
- Check 2: AWS IAM users with MFA (read-only SecurityAudit policy)
