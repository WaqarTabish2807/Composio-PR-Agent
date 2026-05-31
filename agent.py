import os
import sys
import json
import composio
print(f"[Debug-Agent] Python Interpreter: {sys.executable}")
print(f"[Debug-Agent] Composio File: {getattr(composio, '__file__', 'unknown')}")
from dotenv import load_dotenv
from composio import Composio
from openai import OpenAI

# Load environment variables
load_dotenv()

def handle_pr_event(pr_data: dict):
    user_email = os.getenv("USER_EMAIL")
    api_key = os.getenv("COMPOSIO_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    model_name = os.getenv("OPENAI_MODEL", "gpt-4o")

    if not api_key:
        print("ERROR: COMPOSIO_API_KEY is not set.")
        return
    if not openai_key:
        print("ERROR: OPENAI_API_KEY is not set.")
        return
    if not user_email:
        print("ERROR: USER_EMAIL is not set.")
        return

    print(f"\n[Agent] Starting agent loop for user: {user_email}")
    composio = Composio(api_key=api_key)
    openai_client = OpenAI(api_key=openai_key)

    try:
        # Get tools from both toolkits
        print("[Agent] Fetching GITHUB and LINEAR tools from Composio...")
        tools = composio.tools.get(
            user_id=user_email,
            toolkits=["GITHUB", "LINEAR"],
            limit=30, # Fetch enough actions to support all tasks
        )
        print(f"[Agent] Retrieved {len(tools)} tools from Composio.")
    except Exception as e:
        print(f"[Agent] Error fetching tools from Composio: {e}")
        return

    pr_url = pr_data.get("pull_request", {}).get("html_url", "")
    pr_number = pr_data.get("pull_request", {}).get("number", 0)
    repo_full_name = pr_data.get("repository", {}).get("full_name", "")
    pr_body = pr_data.get("pull_request", {}).get("body") or ""

    if not pr_url or not pr_number or not repo_full_name:
        print("[Agent] WARNING: PR payload is missing critical details. Falling back to default test repository settings...")
        pr_url = pr_url or "https://github.com/WaqarTabish2807/Composio-PR-Agent/pull/1"
        pr_number = pr_number or 1
        repo_full_name = repo_full_name or "WaqarTabish2807/Composio-PR-Agent"
        pr_body = pr_body or "Automated Test PR. ENG-42"

    prompt = f"""
    A PR was opened: {pr_url}
    PR #{pr_number} in repository {repo_full_name}
    PR description:
    \"\"\"
    {pr_body}
    \"\"\"
    
    Do the following in order:
    1. Get the PR diff using GITHUB_GET_A_PULL_REQUEST for repository '{repo_full_name}' and pull number {pr_number}.
    2. Write a short structured code review (max 200 words): what looks good, and any concerns.
    3. Post that review as a comment on PR #{pr_number} in repository '{repo_full_name}'.
    4. If the PR description/body mentions any Linear issue ID (e.g. ENG-123 or ENG-42), extract the issue key and update that Linear issue status to "In Review".
    """

    print(f"[Agent] PR Details: Repo={repo_full_name}, PR #{pr_number}")
    print(f"[Agent] Initiating Agentic Loop using model: {model_name}")

    messages = [{"role": "user", "content": prompt}]
    
    step = 1
    # Agentic loop
    while True:
        print(f"\n--- [Agent Step {step}] ---")
        try:
            response = openai_client.chat.completions.create(
                model=model_name,
                messages=messages,
                tools=tools,
            )
        except Exception as e:
            print(f"[Agent] OpenAI API Error: {e}")
            break

        # Log OpenAI response details
        assistant_message = response.choices[0].message
        if assistant_message.content:
            print(f"OpenAI Response:\n{assistant_message.content}")

        if not assistant_message.tool_calls:
            print("\n✅ [Agent] Completed task successfully!")
            break
            
        print(f"[Agent] OpenAI triggered tool calls. Executing via Composio...")
        
        try:
            result = composio.provider.handle_tool_calls(
                user_id=user_email,
                response=response,
            )
            # Truncate response details in logs to keep clean console
            result_preview = str(result)[:300] + "..." if len(str(result)) > 300 else str(result)
            print(f"[Agent] Tool call execution result preview: {result_preview}")
        except Exception as e:
            print(f"[Agent] Error executing tools via Composio: {e}")
            result = f"Error during tool execution: {str(e)}"

        # Convert tool result to appropriate type (often string or dictionary containing output)
        if not isinstance(result, str):
            result = json.dumps(result)

        # Append assistant response and tool execution result to message history
        messages.append(assistant_message)
        messages.append({"role": "user", "content": result})
        step += 1

if __name__ == "__main__":
    print("Testing agent module initialization and mock loading...")
    load_dotenv()
    if not os.getenv("COMPOSIO_API_KEY") or not os.getenv("OPENAI_API_KEY"):
        print("Note: COMPOSIO_API_KEY or OPENAI_API_KEY not configured. Skipping dry run.")
    else:
        print("Dry run initialized. Run through webhook server or run this file with a mock payload.")
