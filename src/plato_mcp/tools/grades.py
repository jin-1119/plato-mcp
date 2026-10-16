"""Tool: get_grades (issue #15), get_grades_access_info (issue #95).

Issue #95 audited the rest of the grades-related function family against
this real account and compared each to what get_grades/get_assignment_detail
already return. Decisions, all confirmed live against course 5968:

- `core_grades_get_gradeitems` -- errored `invalidparameter` on a minimal
  (courseid, userid) call; the exact required parameter shape wasn't
  worth reverse-engineering given get_grades already covers this via
  gradereport_user_get_grade_items. Skipped.
- `core_grades_get_gradable_users` -- errored `nopermissions` (lists
  *all* students in a course for grading -- a teacher capability a
  student account doesn't have). Skipped, confirmed admin/teacher-only.
- `gradereport_user_get_grades_table` -- returns a fully-rendered HTML
  grade table (every cell is an HTML/CSS fragment meant for a browser),
  not structured data. Strictly worse for programmatic use than the
  clean GradeItem list get_grades already returns. Skipped as redundant
  and wrong-shaped for an API consumer.
- `gradereport_user_get_access_information` -- small, genuinely new,
  clean JSON (canviewusergradereport/canviewmygrades/canviewallgrades).
  Wired below as get_grades_access_info.
- `mod_assign_get_grades` -- errored "No access rights in module context"
  against the one real assignment on this account. Skipped, confirmed
  not accessible to a student account (teacher-side grading detail).
"""

from typing import Annotated

from mcp.server.mcpserver import Context
from pydantic import Field

from plato_mcp.context import get_client, get_userid
from plato_mcp.errors import MoodleAPIError
from plato_mcp.models import GradeAccessInfo, GradeItem, GradesResult
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


def get_grades_access_info_for(client: MoodleClient, course_id: int) -> GradeAccessInfo:
    result = client.call("gradereport_user_get_access_information", courseid=course_id)
    return GradeAccessInfo(**result)


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

    @mcp.tool(annotations=READ_ONLY_TOOL_ANNOTATIONS)
    async def get_grades_access_info(
        course_id: Annotated[
            int, Field(description="PLATO/Moodle numeric course id, e.g. from list_courses.")
        ],
        ctx: Context,
    ) -> GradeAccessInfo:
        """Check what grade-related permissions this account has in a
        course -- e.g. whether it can see its own grades vs. (as a
        teacher/TA) everyone's grades. Most student accounts will see
        canviewallgrades=False."""
        return get_grades_access_info_for(get_client(ctx), course_id)
