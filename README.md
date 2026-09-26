# grc-evidence-collector

Python scripts that pull compliance evidence from systems of record and save it
as timestamped JSON.

## Checks

| Check | Script | Controls |
|---|---|---|
| GitHub default-branch protection | `check_branch_protection.py` | NIST SP 800-53 CM-3, SOC 2 CC8.1, ISO 27001:2022 A.8.32 |
| AWS IAM users with MFA | `check_iam_mfa.py` | NIST SP 800-53 IA-2(1), IA-2(2), SOC 2 CC6.1, ISO 27001:2022 A.8.5 |

### GitHub default-branch protection

Each run records one of these results:

- `pass`: the default branch blocks deletions and force pushes, and requires
  pull requests (via classic branch protection or a ruleset)
- `fail`: one or more of those rules is missing; `details` lists which
- `not_applicable`: branch protection isn't available (free-plan private repos)
- `error`: the check couldn't complete; the reason is in `details`

### AWS IAM users with MFA

- `pass`: the root user and every IAM user who can sign in to the console
  have MFA
- `fail`: the root user or a console user has no MFA; `details` lists who
- `error`: the check couldn't complete; the reason is in `details`

Users without a console password (API-only, like the script's own user) can't
sign in with MFA, so they're listed under `api_only_users` for review instead
of failing the check. Evidence records user names and dates only, not ARNs,
so the AWS account ID stays out of the files.

## Setup

1. Install the dependency:

   ```
   pip install -r requirements.txt
   ```

2. Create a GitHub fine-grained personal access token with read-only access
   to the repository: **Metadata: Read-only** and **Administration: Read-only**.

3. Put the token in an environment variable (never in code):

   macOS / Linux:

   ```
   export GITHUB_TOKEN=your_token_here
   ```

   Windows PowerShell (input is masked):

   ```
   $env:GITHUB_TOKEN = [System.Net.NetworkCredential]::new("", (Read-Host "Paste your GitHub token" -AsSecureString)).Password
   ```

4. For the AWS check, create an IAM user with no console access and only the
   AWS-managed **SecurityAudit** policy (read-only), then create an access key
   for it (**Application running outside AWS**). Set the key the same way:

   ```
   export AWS_ACCESS_KEY_ID=your_key_id_here
   export AWS_SECRET_ACCESS_KEY=your_secret_here
   ```

## Usage

```
python check_branch_protection.py owner/repo
python check_iam_mfa.py
```

Evidence is saved to `evidence/github_branch_protection_<timestamp>.json` and
`evidence/aws_iam_mfa_<timestamp>.json`. Each script exits with code 1 on `fail` or `error`, after saving the evidence.
See `examples/` for sample `fail` and `pass` results from real runs.

## Automated weekly run

`.github/workflows/weekly-evidence.yml` runs both checks every Monday at
09:00 UTC, and on demand from the **Actions** tab (**Run workflow**). Each
run's evidence is kept as a downloadable artifact for 90 days, and a `fail`
shows as a failed run.

It reads these repository secrets (**Settings → Secrets and variables →
Actions**), with the same read-only permissions as above:

- `EVIDENCE_TOKEN`: the GitHub token
- `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`: the SecurityAudit user's key
