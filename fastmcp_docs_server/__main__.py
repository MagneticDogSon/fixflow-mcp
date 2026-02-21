import os
from fastmcp_docs_server.server import mcp

port = int(os.environ.get("PORT", 8000))
mcp.run(transport="sse", host="0.0.0.0", port=port)
