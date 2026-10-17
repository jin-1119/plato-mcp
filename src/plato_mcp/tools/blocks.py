"""Tools: get_recent_items, get_starred_courses (issue #116).

Issue #116 audited core_block_*, block_*, aiplacement_*, core_ai_*, and
message_airnotifier_*/message_popup_* (~16 functions) against the real
account. Decisions, all confirmed live:

- `block_recentlyaccesseditems_get_recent_items` -- real, useful data
  (recently-accessed modules across courses with direct view URLs).
  Wired as get_recent_items. Possible overlap with #103's
  get_recent_courses (course-level, not module-level) -- different
  granularity, not deduplicated.
- `block_starredcourses_get_starred_courses` -- works, returns [] for
  this account (no starred courses, a valid empty state, not an error).
  Wired as get_starred_courses.
- `message_popup_get_popup_notifications` -- compared against
  get_unread_messages (core_message_get_messages): same underlying
  notification data (a real assignment-due reminder showed up in both
  shapes), just with extra HTML-formatted fields. Documented as
  redundant -- NOT wired as a second tool.
- `core_block_get_dashboard_blocks`/`get_course_blocks`/`fetch_addable_blocks`
  -- UI layout data (which blocks are docked where), not useful
  standalone for an AI assistant. Skipped.
- `aiplacement_courseassist_summarise_text`/`editor_generate_image`/
  `editor_generate_text`, `core_ai_get_policy_status`/`set_policy_status`
  -- PLATO exposes Moodle 4.5's own built-in AI features. Documented
  decision: plato-mcp does NOT proxy a different LMS's AI
  generation/summarization features -- that's a different product
  decision than "expose Moodle's data via MCP tools", and an AI client
  calling an MCP tool that itself calls another AI is a confusing
  indirection with no clear benefit over the client's own model doing
  the summarizing/generating directly. Not wired, regardless of exact
  live parameter requirements (both errored with invalidparameter on a
  minimal call; not pursued further since the decision doesn't depend
  on them actually working).
- `message_airnotifier_*` (4 functions) -- confirmed live:
  `is_system_configured` returns `0` (push notifications are not set up
  on this platform at all). Skipped, nothing to build on top of a
  disabled feature.
"""

from mcp.server.mcpserver import Context

from plato_mcp.context import get_client
from plato_mcp.models import CourseSummary, RecentItem
from plato_mcp.moodle_client import MoodleClient
from plato_mcp.tool_annotations import READ_ONLY_TOOL_ANNOTATIONS


def get_recent_items_for(client: MoodleClient) -> list[RecentItem]:
    result = client.call("block_recentlyaccesseditems_get_recent_items")
    return [RecentItem(**i) for i in result]


def get_starred_courses_for(client: MoodleClient) -> list[CourseSummary]:
    result = client.call("block_starredcourses_get_starred_courses")
    return [CourseSummary(**c) for c in result]


def register(mcp) -> None:
    @mcp.tool(annotations=READ_ONLY_TOOL_ANNOTATIONS)
    async def get_recent_items(ctx: Context) -> list[RecentItem]:
        """Get this account's recently-accessed course modules (files,
        assignments, etc.) across all courses, most recent first."""
        return get_recent_items_for(get_client(ctx))

    @mcp.tool(annotations=READ_ONLY_TOOL_ANNOTATIONS)
    async def get_starred_courses(ctx: Context) -> list[CourseSummary]:
        """Get this account's starred/favourited courses, if any."""
        return get_starred_courses_for(get_client(ctx))
