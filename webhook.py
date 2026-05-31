from fastapi import APIRouter, Request, BackgroundTasks
from agent import handle_pr_event

router = APIRouter()

@router.post("/webhook/github-pr")
async def github_pr_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    FastAPI endpoint designed to receive GITHUB_PULL_REQUEST_EVENT webhooks forwarded by Composio.
    Launches the code review and Linear update loop in the background to avoid timing out the caller.
    """
    try:
        payload = await request.json()
        print(f"\n[Webhook] Received incoming webhook payload type: {payload.get('type')}")
        
        if payload.get("type") == "GITHUB_PULL_REQUEST_EVENT":
            pr_data = payload.get("data", {})
            # The action can be found at the 'data' level or inside 'pull_request' depending on exact format
            action = pr_data.get("action") or pr_data.get("pull_request", {}).get("action", "")
            
            print(f"[Webhook] Pull Request action detected: {action}")
            if action in ["opened", "synchronize", "reopened"]:
                print(f"[Webhook] Triggering agent review thread in background...")
                background_tasks.add_task(handle_pr_event, pr_data)
                return {"status": "processing", "message": "PR sync agent triggered in the background."}
            else:
                print(f"[Webhook] Action '{action}' ignored. Only reviewing opened, synchronize, or reopened PRs.")
                return {"status": "ignored", "reason": f"Action '{action}' is not reviewed."}
        else:
            print(f"[Webhook] Event type '{payload.get('type')}' is not supported.")
            return {"status": "ignored", "reason": "Event type not supported."}

    except Exception as e:
        print(f"[Webhook] Error processing webhook payload: {e}")
        return {"status": "error", "detail": str(e)}
