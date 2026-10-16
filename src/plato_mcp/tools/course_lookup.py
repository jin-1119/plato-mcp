"""Tools: get_course_module, search_courses, get_recent_courses (issue #103).

Audited the rest of the core_course_* family against the real account.
Decisions, all confirmed live:

- `core_course_get_course_module`/`get_course_module_by_instance` -- wired
  below as get_course_module. Confirmed to return the exact same module
  data as filtering a full get_course_contents response, which is how
  ubboard/scraper.py:find_board_id currently has to resolve a module id
  (fetches the whole course, loops every module). This tool is a direct
  one-call replacement for that pattern, though the existing scraper
  wasn't changed in this issue -- that's a separate refactor, not new
  coverage.
- `core_course_search_courses` -- wired below as search_courses. Confirmed
  live: searches PLATO's entire course catalog (180 results for one test
  term), not just this account's enrolled courses -- genuinely different
  from list_courses.
- `core_course_get_recent_courses` -- wired below. NOTE: likely overlaps
  with `block_recentlyaccesseditems_get_recent_items` (scoped to #116,
  not yet built as of this issue) -- not deduplicated here since #116
  hasn't landed; revisit once it has.
- `core_course_get_categories` -- skipped. Admin/catalog taxonomy
  (category tree), not a student-facing concept with a clear AI use case.
- `core_course_get_user_navigation_options`/`get_user_administration_options`
  -- skipped. These return UI show/hide booleans for Moodle's own web
  interface (e.g. "show the backup button"), not data -- confirmed live,
  every administration option was `false` for this student account, and
  there's no AI-assistant equivalent of "should a button be shown".
- `core_course_set_favourite_courses` -- skipped. No real use case
  surfaced during this audit (starring a course in Moodle's own UI isn't
  something an AI assistant acting on a user's behalf has an obvious
  reason to do unprompted); revisit if a real request comes up.
- `core_course_view_course` -- NOT wired, deliberately, same reasoning as
  the other `view_*` logging functions (#100): it mutates server-side
  viewed/recent-access state as a side effect, which a tool call
  shouldn't pretend to be a real user visit.

Also audited a full, untruncated core_course_get_contents response
(course 5968) against CourseSection/CourseModule for dropped fields:
`section.summary` and `module.description` exist in the schema but were
empty/None for every section and module checked on this account -- not
worth adding fields that have never been observed to carry real data.
"""

from typing import Annotated

from mcp.server.mcpserver import Context
from pydantic import Field

from plato_mcp.context import get_client
from plato_mcp.models import CourseModuleInfo, CourseSummary
from plato_mcp.moodle_client import MoodleClient
from plato_mcp.tool_annotations import READ_ONLY_TOOL_ANNOTATIONS


def get_course_module_for(client: MoodleClient, cmid: int) -> CourseModuleInfo:
    result = client.call("core_course_get_course_module", cmid=cmid)
    return CourseModuleInfo(**result["cm"])


def search_courses_for(client: MoodleClient, search_text: str) -> list[CourseSummary]:
    result = client.call(
        "core_course_search_courses", criterianame="search", criteriavalue=search_text
    )
    return [CourseSummary(**c) for c in result.get("courses", [])]


def get_recent_courses_for(client: MoodleClient) -> list[CourseSummary]:
    result = client.call("core_course_get_recent_courses")
    return [CourseSummary(**c) for c in result]


def register(mcp) -> None:
    @mcp.tool(annotations=READ_ONLY_TOOL_ANNOTATIONS)
    async def get_course_module(
        cmid: Annotated[int, Field(description="Course module id (cmid).")],
        ctx: Context,
    ) -> CourseModuleInfo:
        """Resolve a single course module by its id directly, without
        fetching and filtering the whole course's contents."""
        return get_course_module_for(get_client(ctx), cmid)

    @mcp.tool(annotations=READ_ONLY_TOOL_ANNOTATIONS)
    async def search_courses(
        search_text: Annotated[str, Field(description="Text to search for in course names.")],
        ctx: Context,
    ) -> list[CourseSummary]:
        """Search PLATO's entire course catalog by name -- not limited to
        this account's enrolled courses (use list_courses for that)."""
        return search_courses_for(get_client(ctx), search_text)

    @mcp.tool(annotations=READ_ONLY_TOOL_ANNOTATIONS)
    async def get_recent_courses(ctx: Context) -> list[CourseSummary]:
        """Get this account's recently-accessed courses, most recent first."""
        return get_recent_courses_for(get_client(ctx))
