"""Tools: get_upcoming_action_events, get_courses_by_timeline, get_grades_overview
(issue #89).

These wrap Moodle's own aggregate/dashboard functions, which answer "what
do I need to do soon" and "how am I doing overall" in one call each,
instead of combining list_courses + list_assignments + get_calendar_events
(or per-course get_grades) client-side.

`core_calendar_get_action_events_by_course` was also live-verified during
this issue but deliberately did NOT get its own tool -- it returned an
empty result against a real course with real calendar events, and its
result shape is a strict subset of what get_upcoming_action_events already
returns (just pre-filtered to one course, which a caller can do themselves
by checking `.course.id` on the results). Not worth a second tool for
that filtering.
"""

from datetime import UTC, datetime
from typing import Annotated, Literal

from mcp.server.mcpserver import Context
from pydantic import Field

from plato_mcp.context import get_client, get_userid
from plato_mcp.models import ActionEvent, CourseGradeOverview, CourseSummary
from plato_mcp.moodle_client import MoodleClient
from plato_mcp.tool_annotations import READ_ONLY_TOOL_ANNOTATIONS

TimelineClassification = Literal["inprogress", "future", "past"]


def get_upcoming_action_events_for(
    client: MoodleClient, limit: int = 20, timesort_from: int | None = None
) -> list[ActionEvent]:
    params = {
        "timesortfrom": timesort_from if timesort_from is not None else int(
            datetime.now(UTC).timestamp()
        ),
        "limitnum": limit,
    }
    result = client.call("core_calendar_get_action_events_by_timesort", **params)
    return [ActionEvent(**e) for e in result.get("events", [])]


def get_courses_by_timeline_for(
    client: MoodleClient, classification: TimelineClassification = "inprogress"
) -> list[CourseSummary]:
    result = client.call(
        "core_course_get_enrolled_courses_by_timeline_classification",
        classification=classification,
    )
    return [CourseSummary(**c) for c in result.get("courses", [])]


def get_grades_overview_for(client: MoodleClient) -> list[CourseGradeOverview]:
    userid = get_userid(client)
    result = client.call("gradereport_overview_get_course_grades", userid=userid)
    return [CourseGradeOverview(**g) for g in result.get("grades", [])]


def register(mcp) -> None:
    @mcp.tool(annotations=READ_ONLY_TOOL_ANNOTATIONS)
    async def get_upcoming_action_events(
        ctx: Context,
        limit: Annotated[
            int, Field(description="Maximum number of upcoming events to return.")
        ] = 20,
    ) -> list[ActionEvent]:
        """Get Moodle's own "what needs action soon" feed -- assignments due,
        video lectures with a watch deadline, etc. -- sorted by urgency, from
        now onward. Unlike combining list_assignments + get_calendar_events,
        this is Moodle's own cross-activity prioritized view and may surface
        activity types (e.g. vod watch deadlines) those tools don't."""
        return get_upcoming_action_events_for(get_client(ctx), limit)

    @mcp.tool(annotations=READ_ONLY_TOOL_ANNOTATIONS)
    async def get_courses_by_timeline(
        ctx: Context,
        classification: Annotated[
            TimelineClassification,
            Field(
                description="'inprogress' (currently running, the default), 'future' "
                "(not started yet), or 'past' (ended)."
            ),
        ] = "inprogress",
    ) -> list[CourseSummary]:
        """List enrolled courses filtered by Moodle's own timeline
        classification (in-progress/future/past), based on course start/end
        dates. Unlike list_courses (which returns everything unfiltered),
        this answers "what am I actually taking right now" directly."""
        return get_courses_by_timeline_for(get_client(ctx), classification)

    @mcp.tool(annotations=READ_ONLY_TOOL_ANNOTATIONS)
    async def get_grades_overview(ctx: Context) -> list[CourseGradeOverview]:
        """Get this account's overall grade for every enrolled course in one
        call. For the individual grade *items* within one course (e.g. each
        assignment's score), use get_grades instead -- this tool only
        returns one summary grade per course."""
        return get_grades_overview_for(get_client(ctx))
