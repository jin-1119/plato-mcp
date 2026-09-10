import pytest

from plato_mcp.server import mcp

EXPECTED_TOOLS = {
    # Phase 1 (official API)
    "list_courses",
    "get_course_contents",
    "list_assignments",
    "get_assignment_detail",
    "get_grades",
    "list_calendar_events",
    "get_unread_messages",
    # Phase 2 (ubboard)
    "list_notices",
    "get_notice_detail",
    "list_qna",
    "get_qna_detail",
    # Phase 3 (write)
    "submit_assignment",
    "post_qna_question",
    # Phase 4 (files)
    "download_course_file",
}


@pytest.mark.asyncio
async def test_server_boots_with_expected_tools_registered():
    tools = await mcp.list_tools()
    names = {t.name for t in tools}
    assert names == EXPECTED_TOOLS


@pytest.mark.asyncio
async def test_every_tool_parameter_has_a_description():
    """Regression guard for issue #77 (Smithery quality score)."""
    tools = await mcp.list_tools()
    for tool in tools:
        properties = (tool.input_schema or {}).get("properties", {})
        for param_name, schema in properties.items():
            if param_name == "ctx":
                continue
            assert schema.get("description"), f"{tool.name}.{param_name} has no description"


@pytest.mark.asyncio
async def test_every_tool_has_annotations():
    """Regression guard for issue #77 (Smithery quality score)."""
    tools = await mcp.list_tools()
    for tool in tools:
        assert tool.annotations is not None, f"{tool.name} has no annotations"


def test_server_metadata_is_set():
    """Regression guard for issue #77 (Smithery quality score).

    Icon is set directly in the Smithery dashboard, not in code -- see #77.
    """
    assert mcp.website_url
