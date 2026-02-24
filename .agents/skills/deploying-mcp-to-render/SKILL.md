---
name: deploying-mcp-to-render
description: Deploys FastMCP servers to Render.com using Docker. Handles health check routes, StreamableHTTP protocol configuration, and Supergateway integration. Use when the user wants to make an MCP server publicly accessible.
---

# Deploying MCP Servers to Render

## When to use this skill
- User wants to deploy a Python FastMCP server to the cloud.
- Encountering 404 errors during Render deployment health checks.
- Setting up a permanent URL for a community MCP server.

## Workflow

### 1. Structure Verification
- [ ] Ensure `fastmcp` and `uvicorn` are in `requirements.txt`.
- [ ] Verify `Dockerfile` uses `uvicorn` to expose the ASGI `app`.
- [ ] Check that `server.py` defines a Starlette `app` with a `/health` route.

### 2. FastMCP Configuration Template
Use this pattern in `server.py` to satisfy Render's health checks without duplicating the `/mcp` route (FastMCP 3.x already implements `/mcp` internally):
```python
from fastmcp import FastMCP
from starlette.responses import JSONResponse
from starlette.routing import Route

mcp = FastMCP("MyServer")
async def health_check(request): 
    return JSONResponse({"status": "ok"})

# ✅ CORRECT: Inject health routes directly into the FastMCP http_app
mcp_app = mcp.http_app()
mcp_app.routes.insert(0, Route("/", endpoint=health_check))
mcp_app.routes.insert(1, Route("/health", endpoint=health_check))

app = mcp_app
```

### 3. Local Client Integration
Update `mcp_config.json` to use the bridge:
- Command: `npx -y supergateway`
- Args: `["--streamableHttp", "https://<your-app>.onrender.com/mcp"]`

## Instructions

1.  **Health Check Priority**: Always set Render's "Health Check Path" to `/health`. Avoid using the root `/` if FastMCP is mounted there, as it might return 404 or 405.
2.  **Port Handling**: Always use `os.environ.get("PORT", 10000)` in the start command.
3.  **Transport Protocol**: For FastMCP 3.x+, prefer `StreamableHTTP` via `supergateway` for the best reliability in cloud environments.

## Resources
- [See Dockerfile Template](resources/Dockerfile.template)
