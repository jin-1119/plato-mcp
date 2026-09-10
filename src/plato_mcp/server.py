"""MCP server entrypoint for PLATO (Pusan National University LMS).

Tools are registered per phase as they land (see PLAN.md / GitHub issues).

Two run modes, selected by the `MCP_TRANSPORT` env var:
- unset / "stdio" (default): local dev, Claude Desktop -- one process per
  user, config from `.env`/environment (see config.py).
- "streamable-http": the Smithery container runtime (issue #29/#30) --
  listens on `PORT` (Smithery sets 8081), config carried per-request via
  headers/query-params (see asgi.py, config.py).
"""

import os

from mcp.server.mcpserver import MCPServer
from mcp.types import Icon

from plato_mcp.tools import register_all

# Same icon set on the Smithery listing dashboard, embedded here so it's
# also served in the MCP protocol's own server metadata (128x128 PNG).
_ICON_DATA_URI = (
    "data:image/png;base64,"
    "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"
)

mcp = MCPServer(
    name="plato-mcp",
    description="Unofficial MCP server for PLATO (plato.pusan.ac.kr), PNU's Moodle-based LMS.",
    website_url="https://github.com/jin-1119/plato_mcp",
    icons=[Icon(src=_ICON_DATA_URI, mime_type="image/png", sizes=["128x128"])],
)

register_all(mcp)


def run_http() -> None:
    """Run under Streamable HTTP, as required by Smithery's container runtime."""
    import uvicorn
    from starlette.middleware.cors import CORSMiddleware

    from plato_mcp.asgi import QueryParamsToHeadersMiddleware, RedactedAccessLogMiddleware

    port = int(os.environ.get("PORT", "8081"))
    app = mcp.streamable_http_app(host="0.0.0.0")
    app = QueryParamsToHeadersMiddleware(app)
    # Wildcard origin: safe here because Smithery's gateway is the only thing
    # that ever talks to this container directly (it isn't exposed to
    # arbitrary browsers on the open internet on its own) -- see
    # docs/smithery_deployment_model.md's #63 addendum. Revisit if this
    # server is ever deployed standalone, reachable directly by browsers.
    app = CORSMiddleware(
        app,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # access_log=False + RedactedAccessLogMiddleware: uvicorn's default access
    # log includes the full request line (query string included), which would
    # log pnu_id/pnu_password in plaintext on every request (issue #63).
    app = RedactedAccessLogMiddleware(app)

    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info", access_log=False)


def main() -> None:
    if os.environ.get("MCP_TRANSPORT") == "streamable-http":
        run_http()
    else:
        mcp.run()


if __name__ == "__main__":
    main()
