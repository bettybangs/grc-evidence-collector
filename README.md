# grc-evidence-collector

Python scripts that pull compliance evidence from systems of record and save it
as timestamped JSON.

## Checks

| Check | Script | Controls |
|---|---|---|
| GitHub default-branch protection | `check_branch_protection.py` | NIST SP 800-53 CM-3, SOC 2 CC8.1, ISO 27001:2022 A.8.32 |

Each run records one of these results:

- `pass`: the default branch is protected (classic branch protection or a ruleset)
- `fail`: the default branch has no protection rules
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

   ```
   export GITHUB_TOKEN=your_token_here
   ```

## Usage

```
python check_branch_protection.py owner/repo
```

Evidence is saved to `evidence/github_branch_protection_<timestamp>.json`.
