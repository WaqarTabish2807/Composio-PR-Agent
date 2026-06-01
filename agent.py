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

    # Support both flat Composio webhook payloads and nested GitHub structures
    pr_url = pr_data.get("url") or pr_data.get("pull_request", {}).get("html_url", "")
    pr_number = pr_data.get("number") or pr_data.get("pull_request", {}).get("number", 0)
    pr_body = pr_data.get("description") or pr_data.get("pull_request", {}).get("body") or ""

    # Parse repository full name from PR url or fallback
    repo_full_name = ""
    if pr_url and "github.com/" in pr_url:
        try:
            parts = pr_url.split("github.com/")[-1].split("/")
            repo_full_name = f"{parts[0]}/{parts[1]}"
        except Exception:
            pass

    if not repo_full_name:
        repo_full_name = pr_data.get("repository", {}).get("full_name", "")

    if not pr_url or not pr_number or not repo_full_name:
        print("[Agent] WARNING: PR payload is missing critical details. Falling back to default test repository settings...")
        pr_url = pr_url or "https://github.com/WaqarTabish2807/Composio-PR-Agent/pull/1"
        pr_number = pr_number or 1
        repo_full_name = repo_full_name or "WaqarTabish2807/Composio-PR-Agent"
        pr_body = pr_body or "Automated Test PR. WAQ-1"

    prompt = f"""
    A PR was opened: {pr_url}
    PR #{pr_number} in repository {repo_full_name}
    PR description:
    \"\"\"
    {pr_body}
    \"\"\"
    
    Do the following in order:
    1. Get the list of modified files and their code diffs (patches) using GITHUB_LIST_PULL_REQUESTS_FILES for repository '{repo_full_name}' and pull number {pr_number}. (Note: This action returns the list of files and their unified diff 'patch' contents).
    2. Write a short structured code review (max 200 words) based on the code diff patches: what looks good, and any concerns.
    3. Post that review as a comment on PR #{pr_number} in repository '{repo_full_name}' using GITHUB_CREATE_AN_ISSUE_COMMENT or GITHUB_CREATE_A_REVIEW_COMMENT_FOR_A_PULL_REQUEST.
    4. If the PR description/body mentions any Linear issue ID (e.g. WAQ-1 or ENG-42), extract the issue key and update that Linear issue status to "In Review".
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
            
        # We must append the assistant message to history first!
        messages.append(assistant_message)
        
        print(f"[Agent] OpenAI triggered tool calls. Executing via Composio...")
        try:
            results = composio.provider.handle_tool_calls(
                user_id=user_email,
                response=response,
            )
            # Truncate response details in logs to keep clean console
            result_preview = str(results)[:300] + "..." if len(str(results)) > 300 else str(results)
            print(f"[Agent] Tool call execution result preview: {result_preview}")

            # For each tool_call generated by OpenAI, find its corresponding output from Composio and append it as a "tool" message!
            # Since Composio executes them in the same order, the index matches!
            for i, tool_call in enumerate(assistant_message.tool_calls):
                tool_call_id = tool_call.id
                # Get the result from Composio
                output_data = results[i] if i < len(results) else {"error": "No execution result returned from Composio"}
                
                # Append the correct tool response message format expected by OpenAI
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": json.dumps(output_data) if not isinstance(output_data, str) else output_data
                })
        except Exception as e:
            print(f"[Agent] Error executing tools via Composio: {e}")
            # Append error responses for each tool_call so OpenAI API doesn't crash on invalid sequence
            for tool_call in assistant_message.tool_calls:
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": f"Error during tool execution: {str(e)}"
                })
        step += 1

if __name__ == "__main__":
    print("Testing agent module initialization and mock loading...")
    load_dotenv()
    if not os.getenv("COMPOSIO_API_KEY") or not os.getenv("OPENAI_API_KEY"):
        print("Note: COMPOSIO_API_KEY or OPENAI_API_KEY not configured. Skipping dry run.")
    else:
        print("Dry run initialized. Run through webhook server or run this file with a mock payload.")
