"""Per-request MoodleClient construction, shared by every Phase 1 tool.

`_session_manager` is a single process-wide SessionManager -- that's what
lets a second tool call in the same MCP connection reuse the wstoken from
the first, instead of logging in again (see PLAN.md / issue #10).
"""

import uuid
from collections.abc import Mapping

from mcp.server.mcpserver import Context

from plato_mcp.auth import PlatoSession, SessionManager
from plato_mcp.config import load_config
from plato_mcp.moodle_client import MoodleClient

_session_manager = SessionManager()

# A stdio connection serves exactly one client for the whole lifetime of
# the process (Claude Code/Desktop spawns one `plato-mcp` subprocess per
# connection), so one value generated at import time is already stable for
# every tool call that process ever handles -- mirroring what the
# `mcp-session-id` header gives for free over HTTP transports (see
# `_session_key` below).
_STDIO_SESSION_KEY = f"stdio-{uuid.uuid4().hex}"

_MCP_SESSION_ID_HEADER = "mcp-session-id"


def _session_key(ctx: Context) -> str:
    """A key stable across every tool call on one logical client connection
    -- used both for `write_tools.PreviewTracker` matching (issue #37) and
    for `MoodleClient`'s wstoken/cookie-session caching (issue #10).

    Previously `f"mcp-session-{id(ctx.session)}"`, on the assumption that
    `ctx.session` (a `ServerSession`) is one stable object per connection.
    It isn't, as of the installed SDK (`mcp>=2.0.0`, unpinned in
    pyproject.toml): `ServerRunner._make_context` (mcp/server/runner.py)
    constructs a brand-new `ServerSession` for every single inbound
    request. `id(ctx.session)` was therefore a different value on every
    call, silently breaking both PreviewTracker (a dry_run=True preview
    could never be matched by a later dry_run=False, over any transport)
    and wstoken caching (a fresh PLATO login on every tool call instead of
    once per connection) -- found live while verifying issue #153 against
    the real deployment (issue #155).

    Fixed by keying on something the SDK actually keeps stable per
    connection: the `mcp-session-id` request header for HTTP transports --
    the same value `streamable_http_manager.py` itself uses to route
    repeat requests back to the same transport/session, confirmed stable
    across calls empirically. stdio has no such header (`ctx.headers` is
    `None` there), so `_STDIO_SESSION_KEY` covers that case instead.
    """
    if ctx.headers is None:
        return _STDIO_SESSION_KEY

    headers: Mapping[str, str] = ctx.headers
    http_session_id = headers.get(_MCP_SESSION_ID_HEADER)
    if http_session_id:
        return f"mcp-session-{http_session_id}"

    # No session id on this request (e.g. a stateless-mode deployment, or a
    # client that hasn't completed its first round trip yet) -- fall back
    # to the old per-request identity. Unstable across calls, but a *safe*
    # failure (a confirm that won't match its own preview) rather than a
    # cross-session collision between two different remote users who'd
    # otherwise share this fallback.
    return f"mcp-session-{id(ctx.session)}"


def get_client(ctx: Context) -> MoodleClient:
    config = load_config(ctx.headers)
    return MoodleClient(
        _session_manager,
        _session_key(ctx),
        config.pnu_id,
        config.pnu_password,
        timeout=config.request_timeout_seconds,
    )


def get_ubboard_session(ctx: Context) -> PlatoSession:
    """Ensure a cookie-session (for ubboard scraping) is ready for this connection."""
    config = load_config(ctx.headers)
    return _session_manager.ensure_ubboard_session(
        _session_key(ctx), config.pnu_id, config.pnu_password
    )


def get_userid(client: MoodleClient) -> int:
    site_info = client.call("core_webservice_get_site_info")
    return site_info["userid"]
