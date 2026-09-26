"""Check 2: AWS IAM users with MFA.

Asks AWS IAM which users can sign in to the AWS console and whether each one
has MFA, checks the root user too, and saves the answer as timestamped JSON
evidence in the evidence/ folder.

Usage:
    export AWS_ACCESS_KEY_ID=your_key_id_here
    export AWS_SECRET_ACCESS_KEY=your_secret_here
    python check_iam_mfa.py
"""

import json
import os
import sys
from datetime import datetime, timezone

import boto3
from botocore.exceptions import BotoCoreError, ClientError

# Hardcoded and verified control mappings (see CLAUDE.md). Never generated.
CONTROLS = {
    "NIST SP 800-53": ["IA-2(1)", "IA-2(2)"],
    "SOC 2": ["CC6.1"],
    "ISO 27001:2022": ["A.8.5"],
}


def has_console_access(iam, user_name):
    """Return True if the user has a console password (a "login profile")."""
    try:
        iam.get_login_profile(UserName=user_name)
        return True
    except ClientError as exc:
        if exc.response["Error"]["Code"] == "NoSuchEntity":
            return False
        raise


def check_account(iam):
    """Run the check against the AWS account and return a result dictionary."""
    result = {
        "status": None,
        "details": "",
        "root_mfa_enabled": None,
        "users": [],
    }

    # Step 1: check the root user. SecurityAudit can read this from the
    # account summary without touching root credentials.
    summary = iam.get_account_summary()["SummaryMap"]
    result["root_mfa_enabled"] = summary.get("AccountMFAEnabled") == 1

    # Step 2: list every IAM user and record console access and MFA.
    # Only names and dates are saved, not ARNs, to keep the account ID out.
    for page in iam.get_paginator("list_users").paginate():
        for user in page["Users"]:
            name = user["UserName"]
            mfa_devices = iam.list_mfa_devices(UserName=name)["MFADevices"]
            result["users"].append({
                "user_name": name,
                "created": user["CreateDate"].isoformat(),
                "console_access": has_console_access(iam, name),
                "mfa_enabled": len(mfa_devices) > 0,
            })

    # Step 3: decide pass or fail. MFA is required for anyone who can sign in
    # to the console. API-only users (like this script's own user) can't use
    # a console password, so they are listed but don't fail the check.
    console_users = [u for u in result["users"] if u["console_access"]]
    api_only = [u["user_name"] for u in result["users"] if not u["console_access"]]
    missing = [u["user_name"] for u in console_users if not u["mfa_enabled"]]
    result["console_users_without_mfa"] = missing
    result["api_only_users"] = api_only

    problems = []
    if not result["root_mfa_enabled"]:
        problems.append("Root user has no MFA")
    if missing:
        problems.append("Console users without MFA: " + ", ".join(missing))

    if problems:
        result["status"] = "fail"
        result["details"] = "; ".join(problems)
    else:
        result["status"] = "pass"
        result["details"] = (
            f"Root user and all {len(console_users)} console user(s) have MFA. "
            f"{len(api_only)} API-only user(s) listed for review."
        )
    return result


def main():
    if not os.environ.get("AWS_ACCESS_KEY_ID") or not os.environ.get("AWS_SECRET_ACCESS_KEY"):
        print("AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY must be set. "
              "See the Setup section of README.md.")
        sys.exit(1)

    collected_at = datetime.now(timezone.utc)
    try:
        # IAM is a global service; us-east-1 is its home region.
        iam = boto3.client("iam", region_name="us-east-1")
        result = check_account(iam)
    except ClientError as exc:
        error = exc.response["Error"]
        result = {
            "status": "error",
            "details": f"AWS API error ({error.get('Code')}): {error.get('Message')}",
        }
    except BotoCoreError as exc:
        result = {"status": "error", "details": f"AWS connection error: {exc}"}

    evidence = {
        "check": "aws_iam_user_mfa",
        "collected_at": collected_at.isoformat(),
        "source": "AWS IAM API",
        "controls": CONTROLS,
        "result": result,
    }

    os.makedirs("evidence", exist_ok=True)
    filename = f"evidence/aws_iam_mfa_{collected_at:%Y-%m-%dT%H-%M-%SZ}.json"
    with open(filename, "w") as f:
        json.dump(evidence, f, indent=2)

    print(f"AWS IAM MFA: {result['status']} - {result['details']}")
    print(f"Evidence saved to {filename}")

    # Exit with code 1 on fail or error so automated runs (like GitHub Actions)
    # show a red X. The evidence file is always saved first.
    if result["status"] in ("fail", "error"):
        sys.exit(1)


if __name__ == "__main__":
    main()
