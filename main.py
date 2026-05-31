import uvicorn
from fastapi import FastAPI
from webhook import router as webhook_router

app = FastAPI(
    title="Composio PR Agent & Linear Sync",
    description="Automated GitHub Code Review and Linear integration webhook server",
    version="1.0.0"
)

# Root endpoint for health check / verification
@app.get("/")
async def root():
    return {
        "status": "healthy",
        "service": "Composio GitHub PR Review & Linear Sync Agent",
        "endpoints": {
            "health": "/",
            "github_pr_webhook": "/webhook/github-pr"
        }
    }

# Include the webhook endpoint router
app.include_router(webhook_router)

if __name__ == "__main__":
    print("Starting Composio PR Review Agent Webhook Server...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
