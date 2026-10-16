"""Tools: get_course_completion_status, get_activity_completion_status (issue #88).

Also where `vod` (course video lecture) progress metadata gets surfaced --
see models.VodProgress's docstring for why the actual video stream is
intentionally never exposed (DRM/ToS, decided during the Phase 7 epic's
planning, #83).
"""

from typing import Annotated

from mcp.server.mcpserver import Context
from pydantic import Field

from plato_mcp.context import get_client, get_userid
from plato_mcp.errors import MoodleAPIError
from plato_mcp.models import ActivityCompletionStatus, CourseCompletionResult
from plato_mcp.moodle_client import MoodleClient
from plato_mcp.tool_annotations import READ_ONLY_TOOL_ANNOTATIONS

_COURSE_ID_FIELD = Field(description="PLATO/Moodle numeric course id, e.g. from list_courses.")


def get_course_completion_status_for(
    client: MoodleClient, course_id: int
) -> CourseCompletionResult:
    userid = get_userid(client)
    try:
        result = client.call(
            "core_completion_get_course_completion_status", courseid=course_id, userid=userid
        )
    except MoodleAPIError as e:
        if e.errorcode == "nocriteriaset":
            return CourseCompletionResult(
                courseid=course_id,
                available=False,
                message="This course has no course-level completion criteria set "
                "(nocriteriaset) -- most courses on this account don't enable it. "
                "Try get_activity_completion_status for per-activity progress instead.",
            )
        raise

    status = result.get("completionstatus") or {}
    return CourseCompletionResult(
        courseid=course_id,
        available=True,
        completed=status.get("completed"),
        criteria=status.get("completions", []),
    )


def get_activity_completion_status_for(
    client: MoodleClient, course_id: int
) -> list[ActivityCompletionStatus]:
    userid = get_userid(client)
    result = client.call(
        "core_completion_get_activities_completion_status", courseid=course_id, userid=userid
    )
    return [ActivityCompletionStatus(**s) for s in result.get("statuses", [])]


def register(mcp) -> None:
    @mcp.tool(annotations=READ_ONLY_TOOL_ANNOTATIONS)
    async def get_course_completion_status(
        course_id: Annotated[int, _COURSE_ID_FIELD],
        ctx: Context,
    ) -> CourseCompletionResult:
        """Get this account's overall course-completion status, if the course
        has course-level completion criteria configured. Most courses on
        this platform don't (available=False, with a message explaining
        why) -- try get_activity_completion_status for per-activity
        progress instead, or get_course_contents's per-module `completed`
        flag."""
        return get_course_completion_status_for(get_client(ctx), course_id)

    @mcp.tool(annotations=READ_ONLY_TOOL_ANNOTATIONS)
    async def get_activity_completion_status(
        course_id: Annotated[int, _COURSE_ID_FIELD],
        ctx: Context,
    ) -> list[ActivityCompletionStatus]:
        """Get this account's completion status for every activity/module in
        a course -- richer than get_course_contents's per-module `completed`
        flag (includes tracking rules, e.g. 'must view' vs 'must spend N
        minutes'). For `vod` (video lecture) modules specifically, prefer
        get_course_contents, whose per-module `vod_progress` field also
        includes watch-percentage and deadline info this function doesn't
        return."""
        return get_activity_completion_status_for(get_client(ctx), course_id)
