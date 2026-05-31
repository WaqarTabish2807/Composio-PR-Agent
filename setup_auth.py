import os
import sys
from dotenv import load_dotenv
from composio import Composio

# Load .env file
load_dotenv()

def main():
    api_key = os.getenv("COMPOSIO_API_KEY")
    user_email = os.getenv("USER_EMAIL")
    github_id = os.getenv("GITHUB_AUTH_CONFIG_ID")
    linear_id = os.getenv("LINEAR_AUTH_CONFIG_ID")

    if not api_key:
        print("ERROR: COMPOSIO_API_KEY is not set in the environment or .env file.")
        sys.exit(1)
    if not user_email:
        print("ERROR: USER_EMAIL is not set in the environment or .env file.")
        sys.exit(1)
    if not github_id or github_id.startswith("ac_github_config_id"):
        print("ERROR: Please set a valid GITHUB_AUTH_CONFIG_ID in your .env file.")
        sys.exit(1)
    if not linear_id or linear_id.startswith("ac_linear_config_id"):
        print("ERROR: Please set a valid LINEAR_AUTH_CONFIG_ID in your .env file.")
        sys.exit(1)

    print(f"Initializing Composio client for user: {user_email}...")
    composio = Composio(api_key=api_key)

    try:
        # 1. Initiate GitHub OAuth
        print("\n[GitHub] Initiating OAuth connection...")
        github_request = composio.connected_accounts.initiate(
            integration_id=github_id,
            entity_id=user_email,
        )
        print(f"[GitHub] Please open this URL in your browser to authorize GitHub:")
        print(f"👉 {github_request.redirect_url}\n")

        # 2. Initiate Linear OAuth
        print("[Linear] Initiating OAuth connection...")
        linear_request = composio.connected_accounts.initiate(
            integration_id=linear_id,
            entity_id=user_email,
        )
        print(f"[Linear] Please open this URL in your browser to authorize Linear:")
        print(f"👉 {linear_request.redirect_url}\n")

        # 3. Wait for connection
        print("Waiting for GitHub connection to be completed...")
        github_request.wait_for_connection()
        print("✅ GitHub connected successfully!")

        print("\nWaiting for Linear connection to be completed...")
        linear_request.wait_for_connection()
        print("✅ Linear connected successfully!")

        print("\n🎉 Both accounts are successfully authenticated and connected to Composio!")

    except Exception as e:
        print(f"\n❌ Error establishing connection: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
