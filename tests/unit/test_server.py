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
    # Phase 7 (issue #88)
    "get_course_completion_status",
    "get_activity_completion_status",
    # Phase 7 (issue #89)
    "get_upcoming_action_events",
    "get_courses_by_timeline",
    "get_grades_overview",
    # Phase 7 (issue #85)
    "list_quizzes",
    "get_quiz_attempts",
    "get_quiz_best_grade",
    # Phase 7 (issue #86)
    "list_forums",
    "get_forum_discussions",
    "get_discussion_posts",
    "add_discussion",
    "add_discussion_post",
    # Phase 7 (issue #95)
    "get_grades_access_info",
    # Phase 7 (issue #100)
    "remove_submission",
    # Phase 7 (issue #102)
    "get_course_updates_since",
    # Phase 7 (issue #103)
    "get_course_module",
    "search_courses",
    "get_recent_courses",
    # Phase 7 (issue #87)
    "get_unread_notification_count",
    # Phase 7 (issue #90)
    "get_calendar_access_info",
    "create_calendar_event",
    "delete_calendar_event",
    # Phase 7 (issue #116)
    "get_recent_items",
    "get_starred_courses",
    # Phase 7 (issue #91)
    "list_video_conferences",
    # Phase 7 (issue #93)
    "list_lessons",
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
    """Regression guard for issue #77 (Smithery quality score)."""
    assert mcp.website_url
    assert mcp.icons
