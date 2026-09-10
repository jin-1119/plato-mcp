"""Tool: get_grades (issue #15)."""

from typing import Annotated

from mcp.server.mcpserver import Context
from pydantic import Field

from plato_mcp.context import get_client, get_userid
from plato_mcp.errors import MoodleAPIError
from plato_mcp.models import GradeItem, GradesResult
from plato_mcp.moodle_client import MoodleClient
from plato_mcp.tool_annotations import READ_ONLY_TOOL_ANNOTATIONS


def get_grades_for(client: MoodleClient, course_id: int) -> GradesResult:
    userid = get_userid(client)
    try:
        result = client.call(
            "gradereport_user_get_grade_items", courseid=course_id, userid=userid
        )
    except MoodleAPIError as e:
        if e.errorcode == "nopermissiontoviewgrades":
            return GradesResult(
                courseid=course_id,
                available=False,
                message="Grades are not available for this course (nopermissiontoviewgrades).",
            )
        raise

    usergrades = result.get("usergrades") or []
    if not usergrades:
        return GradesResult(courseid=course_id, available=False, message="No grade data returned.")

    items = [GradeItem(**item) for item in usergrades[0].get("gradeitems", [])]
    return GradesResult(courseid=course_id, available=True, gradeitems=items)


def register(mcp) -> None:
    @mcp.tool(annotations=READ_ONLY_TOOL_ANNOTATIONS)
    async def get_grades(
        course_id: Annotated[
            int, Field(description="PLATO/Moodle numeric course id, e.g. from list_courses.")
        ],
        ctx: Context,
    ) -> GradesResult:
        """Get this account's grade items for a course, if visible."""
        return get_grades_for(get_client(ctx), course_id)
