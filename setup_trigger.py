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
        # Inspecting GITHUB_PULL_REQUEST_EVENT trigger details
        print("Retrieving GITHUB_PULL_REQUEST_EVENT trigger metadata...")
        trigger_type = composio.triggers.get_type("GITHUB_PULL_REQUEST_EVENT")
        print(f"Trigger Name: {trigger_type.name}")
        print(f"Required Configuration Fields: {list(trigger_type.config.keys()) if trigger_type.config else 'None'}")

        # Register the trigger
        print(f"\nRegistering trigger GITHUB_PULL_REQUEST_EVENT for {owner}/{repo}...")
        trigger = composio.triggers.create(
            slug="GITHUB_PULL_REQUEST_EVENT",
            user_id=user_email,
            trigger_config={
                "owner": owner,
                "repo": repo,
            },
        )
        print("\n✅ Trigger registered successfully!")
        print(f"Trigger ID: {trigger.id}")
        print(f"Trigger Info: {trigger}")
        print("\nUse this Trigger ID or manage it in your Composio dashboard.")

    except Exception as e:
        print(f"\n❌ Error setting up trigger: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
