"""Unit tests for context.py's _session_key (issue #155).

_session_key previously had zero coverage -- the bug it fixes (a new
ServerSession per request, breaking anything keyed on id(ctx.session))
was invisible to the rest of the test suite because test_abuse_prevention.py
and test_write_tools.py set client.session_key directly on a mocked client,
never going through this function at all. These tests exercise _session_key
itself against lightweight stand-ins for Context, instead of a mocked client.
"""

from plato_mcp.context import _session_key


def _fake_ctx(mocker, headers=None):
    """A minimal stand-in for mcp.server.mcpserver.Context -- _session_key
    only ever reads .headers and .session off it."""
    ctx = mocker.Mock()
    ctx.headers = headers
    ctx.session = object()
    return ctx


def test_stdio_headers_none_is_stable_across_calls(mocker):
    ctx1 = _fake_ctx(mocker, headers=None)
    ctx2 = _fake_ctx(mocker, headers=None)  # a second, distinct request

    assert _session_key(ctx1) == _session_key(ctx2)


def test_http_same_mcp_session_id_header_is_stable_across_calls(mocker):
    """The core regression this issue fixes: two separate requests (each
    getting its own fresh ctx.session, per the real SDK's per-request
    ServerSession) must still resolve to the same key as long as they
    carry the same mcp-session-id header."""
    ctx1 = _fake_ctx(mocker, headers={"mcp-session-id": "abc123"})
    ctx2 = _fake_ctx(mocker, headers={"mcp-session-id": "abc123"})

    assert ctx1.session is not ctx2.session  # distinct ServerSession objects
    assert _session_key(ctx1) == _session_key(ctx2)


def test_http_different_mcp_session_ids_get_different_keys(mocker):
    """Two different remote connections (e.g. two different real users)
    must never collide onto the same key."""
    ctx1 = _fake_ctx(mocker, headers={"mcp-session-id": "session-A"})
    ctx2 = _fake_ctx(mocker, headers={"mcp-session-id": "session-B"})

    assert _session_key(ctx1) != _session_key(ctx2)


def test_http_without_session_id_header_falls_back_to_per_request_identity(mocker):
    """No mcp-session-id on the request (e.g. a stateless-mode deployment) --
    falls back to the old per-ctx.session identity. Unstable across calls,
    but must never coincide with the stdio key or with another connection's
    key just because both lack a header."""
    ctx1 = _fake_ctx(mocker, headers={})
    ctx2 = _fake_ctx(mocker, headers={})

    assert _session_key(ctx1) != _session_key(ctx2)
    assert _session_key(ctx1) != _session_key(_fake_ctx(mocker, headers=None))


def test_stdio_and_http_keys_never_collide(mocker):
    stdio_ctx = _fake_ctx(mocker, headers=None)
    http_ctx = _fake_ctx(mocker, headers={"mcp-session-id": "abc123"})

    assert _session_key(stdio_ctx) != _session_key(http_ctx)
