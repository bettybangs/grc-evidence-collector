# grc-evidence-collector

Python scripts that pull compliance evidence from systems of record and save it
as timestamped JSON.

## Checks

| Check | Script | Controls |
|---|---|---|
| GitHub default-branch protection | `check_branch_protection.py` | NIST SP 800-53 CM-3, SOC 2 CC8.1, ISO 27001:2022 A.8.32 |

Each run records one of these results:

- `pass`: the default branch blocks deletions and force pushes, and requires
  pull requests (via classic branch protection or a ruleset)
- `fail`: one or more of those rules is missing; `details` lists which
- `not_applicable`: branch protection isn't available (free-plan private repos)
- `error`: the check couldn't complete; the reason is in `details`

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

## Usage

```
python check_branch_protection.py owner/repo
```

Evidence is saved to `evidence/github_branch_protection_<timestamp>.json`.
The script exits with code 1 on `fail` or `error`, after saving the evidence.
See `examples/` for a sample `fail` and `pass`.

## Automated weekly run

`.github/workflows/weekly-evidence.yml` runs the check every Monday at
09:00 UTC, and on demand from the **Actions** tab (**Run workflow**). Each
run's evidence is kept as a downloadable artifact for 90 days, and a `fail`
shows as a failed run.

It reads the token from a repository secret named `EVIDENCE_TOKEN`
(**Settings → Secrets and variables → Actions**), with the same read-only
permissions as above.
