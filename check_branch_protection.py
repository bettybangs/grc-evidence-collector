"""Check 1: GitHub default-branch protection.

Asks the GitHub API whether a repository's default branch is protected and
saves the answer as timestamped JSON evidence in the evidence/ folder.

Usage:
    export GITHUB_TOKEN=your_token_here
    python check_branch_protection.py owner/repo
"""

import json
import os
import sys
from datetime import datetime, timezone

import requests

API_URL = "https://api.github.com"

# Hardcoded and verified control mappings (see CLAUDE.md). Never generated.
CONTROLS = {
    "NIST SP 800-53": ["CM-3"],
    "SOC 2": ["CC8.1"],
    "ISO 27001:2022": ["A.8.32"],
}

# The specific rules the default branch must have to pass.
REQUIRED_RULES = {
    "restrict_deletions": "Nobody can delete the branch",
    "block_force_pushes": "Nobody can rewrite the branch history",
    "require_pull_request": "Every change must go through a pull request",
}


def rules_in_place(classic_protection, rulesets):
    """Return which required rules are enforced, from either protection style."""
    ruleset_types = {rule.get("type") for rule in rulesets or []}
    classic = classic_protection or {}
    has_classic = bool(classic)

    return {
        "restrict_deletions": "deletion" in ruleset_types
        or (has_classic and not classic.get("allow_deletions", {}).get("enabled")),
        "block_force_pushes": "non_fast_forward" in ruleset_types
        or (has_classic and not classic.get("allow_force_pushes", {}).get("enabled")),
        "require_pull_request": "pull_request" in ruleset_types
        or "required_pull_request_reviews" in classic,
    }


def github_get(path, token):
    """Send a GET request to the GitHub API and return the response."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    return requests.get(f"{API_URL}{path}", headers=headers, timeout=30)


def error_message(response):
    """Pull GitHub's error message out of a response, if there is one."""
    try:
        return response.json().get("message", "")
    except ValueError:
        return response.text[:200]


def check_repo(repo, token):
    """Run the check against one repo and return a result dictionary."""
    result = {
        "repository": repo,
        "default_branch": None,
        "status": None,
        "details": "",
        "classic_protection": None,
        "rulesets": None,
    }

    # Step 1: find the default branch (usually "main").
    response = github_get(f"/repos/{repo}", token)
    if response.status_code != 200:
        result["status"] = "error"
        result["details"] = (
            f"Could not read repository (HTTP {response.status_code}): "
            f"{error_message(response)}"
        )
        return result
    branch = response.json()["default_branch"]
    result["default_branch"] = branch

    # Step 2: check classic branch protection rules.
    response = github_get(f"/repos/{repo}/branches/{branch}/protection", token)
    message = error_message(response) if response.status_code != 200 else ""
    if response.status_code == 200:
        result["classic_protection"] = response.json()
    elif response.status_code == 404 and "not protected" in message.lower():
        result["classic_protection"] = {}
    elif response.status_code == 403 and "upgrade" in message.lower():
        # Free-plan private repos can't use branch protection at all.
        result["status"] = "not_applicable"
        result["details"] = f"Branch protection unavailable on this plan: {message}"
        return result
    else:
        result["status"] = "error"
        result["details"] = (
            f"Could not read branch protection (HTTP {response.status_code}): {message}"
        )
        return result

    # Step 3: check repository rulesets, GitHub's newer way to protect branches.
    response = github_get(f"/repos/{repo}/rules/branches/{branch}", token)
    if response.status_code == 200:
        result["rulesets"] = response.json()
    elif response.status_code == 403 and "upgrade" in error_message(response).lower():
        result["rulesets"] = []
    else:
        result["status"] = "error"
        result["details"] = (
            f"Could not read rulesets (HTTP {response.status_code}): "
            f"{error_message(response)}"
        )
        return result

    # Step 4: check each required rule, then decide pass or fail.
    rules = rules_in_place(result["classic_protection"], result["rulesets"])
    result["required_rules"] = rules
    missing = [REQUIRED_RULES[name] for name, enforced in rules.items() if not enforced]
    if not missing:
        result["status"] = "pass"
        result["details"] = f"Default branch '{branch}' has all required protection rules."
    elif len(missing) == len(REQUIRED_RULES):
        result["status"] = "fail"
        result["details"] = f"Default branch '{branch}' has no protection rules."
    else:
        result["status"] = "fail"
        result["details"] = f"Default branch '{branch}' is missing: " + "; ".join(missing)
    return result


def main():
    if len(sys.argv) != 2 or "/" not in sys.argv[1]:
        print("Usage: python check_branch_protection.py owner/repo")
        sys.exit(1)
    repo = sys.argv[1]

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("GITHUB_TOKEN is not set. See the Setup section of README.md.")
        sys.exit(1)

    collected_at = datetime.now(timezone.utc)
    try:
        result = check_repo(repo, token)
    except requests.RequestException as exc:
        result = {
            "repository": repo,
            "status": "error",
            "details": f"Network error: {exc}",
        }

    evidence = {
        "check": "github_default_branch_protection",
        "collected_at": collected_at.isoformat(),
        "source": "GitHub REST API",
        "controls": CONTROLS,
        "result": result,
    }

    os.makedirs("evidence", exist_ok=True)
    filename = f"evidence/github_branch_protection_{collected_at:%Y-%m-%dT%H-%M-%SZ}.json"
    with open(filename, "w") as f:
        json.dump(evidence, f, indent=2)

    print(f"{repo}: {result['status']} - {result['details']}")
    print(f"Evidence saved to {filename}")

    # Exit with code 1 on fail or error so automated runs (like GitHub Actions)
    # show a red X. The evidence file is always saved first.
    if result["status"] in ("fail", "error"):
        sys.exit(1)


if __name__ == "__main__":
    main()
