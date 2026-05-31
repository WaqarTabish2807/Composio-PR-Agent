import os
import sys
import argparse
from dotenv import load_dotenv
from composio import Composio

# Load .env file
load_dotenv()

def main():
    parser = argparse.ArgumentParser(description="Set up Composio GitHub PR Trigger")
    parser.add_argument("--owner", help="GitHub owner or organization (e.g. waqartabish)")
    parser.add_argument("--repo", help="GitHub repository name (e.g. Composio-PR-Agent)")
    args = parser.parse_args()

    api_key = os.getenv("COMPOSIO_API_KEY")
    user_email = os.getenv("USER_EMAIL")

    if not api_key:
        print("ERROR: COMPOSIO_API_KEY is not set in the environment or .env file.")
        sys.exit(1)
    if not user_email:
        print("ERROR: USER_EMAIL is not set in the environment or .env file.")
        sys.exit(1)

    owner = args.owner or os.getenv("GITHUB_OWNER")
    repo = args.repo or os.getenv("GITHUB_REPO")

    if not owner or not repo:
        print("ERROR: Both GitHub --owner and --repo must be provided via CLI arguments or GITHUB_OWNER / GITHUB_REPO env variables.")
        sys.exit(1)

    print(f"Initializing Composio client for user: {user_email}...")
    composio = Composio(api_key=api_key)

    try:
        # Find active connected accounts to retrieve the GITHUB connection ID
        print("Retrieving connected accounts for the user...")
        accounts = composio.connected_accounts.get(entity_ids=[user_email])
        if not isinstance(accounts, list):
            accounts = [accounts]

        # Find active GITHUB account
        github_account = next((acc for acc in accounts if acc.appName.lower() == "github" and acc.status.lower() == "active"), None)
        if not github_account:
            print("ERROR: No active GITHUB connected account found for this user.")
            print("Please run setup_auth.py first to establish the GitHub connection.")
            sys.exit(1)

        github_connected_account_id = github_account.id
        print(f"Found active GitHub connected account: {github_connected_account_id}")

        # Register/Enable the trigger
        print(f"\nEnabling trigger GITHUB_PULL_REQUEST_EVENT for {owner}/{repo}...")
        trigger = composio.triggers.enable(
            name="GITHUB_PULL_REQUEST_EVENT",
            connected_account_id=github_connected_account_id,
            config={
                "owner": owner,
                "repo": repo,
            },
        )
        print("\n✅ Trigger enabled successfully!")
        print(f"Trigger Info: {trigger}")
        print("\nUse this Trigger or manage it in your Composio dashboard.")

    except Exception as e:
        print(f"\n❌ Error setting up trigger: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
