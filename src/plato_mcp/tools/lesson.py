"""Tool: list_lessons (issue #93).

mod_lesson is not present in any of the 11 currently-enrolled real courses
(live scan, 2026-10-17) -- forward-looking coverage only.
`mod_lesson_get_lessons_by_courses` is live-verified (correctly returns
an empty list). Everything else in the 17-function mod_lesson family --
get_lesson, get_lesson_access_information, get_pages, get_user_attempt/
grade/timers, get_attempts_overview, and especially the attempt-flow
writes (launch_attempt, process_page, finish_attempt) -- needs a real
lessonid/attempt to call meaningfully, and there is no real lesson on
this account to verify any of it against. None of it is built here,
rather than guessing at an unverified multi-step write flow (same
reasoning as mod_quiz in issue #85). Re-check once a real lesson exists.
"""

from typing import Annotated

from mcp.server.mcpserver import Context
from pydantic import Field

from plato_mcp.context import get_client
from plato_mcp.models import LessonSummary
from plato_mcp.moodle_client import MoodleClient
from plato_mcp.tool_annotations import READ_ONLY_TOOL_ANNOTATIONS


def list_lessons_for(client: MoodleClient, course_ids: list[int]) -> list[LessonSummary]:
    result = client.call("mod_lesson_get_lessons_by_courses", courseids=course_ids)
    return [LessonSummary(**lesson) for lesson in result.get("lessons", [])]


def register(mcp) -> None:
    @mcp.tool(annotations=READ_ONLY_TOOL_ANNOTATIONS)
    async def list_lessons(
        course_ids: Annotated[
            list[int], Field(description="One or more course ids to list lessons for.")
        ],
        ctx: Context,
    ) -> list[LessonSummary]:
        """List Lesson activities across one or more courses. Taking a
        lesson (answering pages) is not supported by this server -- this
        tool is read-only coverage only."""
        return list_lessons_for(get_client(ctx), course_ids)
