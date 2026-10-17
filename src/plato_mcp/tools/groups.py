"""Tools: get_my_course_groups, get_enrolled_users (issue #97).

Audited all 7 functions in scope against the real account. Decisions:

- `core_group_get_course_user_groups` -- wired as get_my_course_groups.
  Confirmed live (empty -- no groups configured in this account's real
  courses, a valid result, not an error).
- `core_enrol_get_enrolled_users` -- wired as get_enrolled_users.
  Confirmed live: returns real classmate names and roles. This is the
  same participant-list data already visible in PLATO's own course UI to
  any enrolled student (not a new exposure), but is still real personal
  data about other people -- see docs/pii_review.md for the same care
  already applied to classmate-content fields elsewhere in this repo.
- `core_group_get_course_groups` -- NOT wired. Confirmed live:
  `nopermissions` ("팀 관리" = team management, a teacher capability).
- `core_group_get_activity_allowed_groups` -- NOT wired. Only meaningful
  for group-restricted activities, none of which exist in any real
  course on this account.
- `core_enrol_get_course_enrolment_methods` -- NOT wired. Confirmed live:
  returns `[]` for this account (enrolment method detail visibility
  appears to need a management capability a student account doesn't
  have) -- no data to expose.
- `core_enrol_search_users` -- NOT wired. Confirmed live: errored on a
  minimal call, not pursued further -- this is a free-text user search
  across the course, the same privacy-scope concern as #96's decision
  not to wire the global core_user_get_users_by_field.
- `enrol_guest_get_instance_info` -- NOT wired. Low standalone value
  (guest-access metadata for a course, relevant only to configuring
  guest access, not a student concern) and no real guest-enrolment
  instance on this account to verify a live response against.
- `enrol_self_enrol_user` (self-enrolling into a NEW course) -- NOT
  wired, per explicit user decision during this issue: this changes the
  account's real enrolment and the user did not see a clear use case for
  an AI assistant to use their own judgment on which courses to enrol
  them into.
"""

from typing import Annotated

from mcp.server.mcpserver import Context
from pydantic import Field

from plato_mcp.context import get_client, get_userid
from plato_mcp.models import CourseGroup, EnrolledUser
from plato_mcp.moodle_client import MoodleClient
from plato_mcp.tool_annotations import READ_ONLY_TOOL_ANNOTATIONS

_COURSE_ID_FIELD = Field(description="PLATO/Moodle numeric course id, e.g. from list_courses.")


def get_my_course_groups_for(client: MoodleClient, course_id: int) -> list[CourseGroup]:
    userid = get_userid(client)
    result = client.call("core_group_get_course_user_groups", courseid=course_id, userid=userid)
    return [CourseGroup(**g) for g in result.get("groups", [])]


def get_enrolled_users_for(client: MoodleClient, course_id: int) -> list[EnrolledUser]:
    result = client.call("core_enrol_get_enrolled_users", courseid=course_id)
    return [EnrolledUser(**u) for u in result]


def register(mcp) -> None:
    @mcp.tool(annotations=READ_ONLY_TOOL_ANNOTATIONS)
    async def get_my_course_groups(
        course_id: Annotated[int, _COURSE_ID_FIELD],
        ctx: Context,
    ) -> list[CourseGroup]:
        """Get the groups this account belongs to within a course, if any."""
        return get_my_course_groups_for(get_client(ctx), course_id)

    @mcp.tool(annotations=READ_ONLY_TOOL_ANNOTATIONS)
    async def get_enrolled_users(
        course_id: Annotated[int, _COURSE_ID_FIELD],
        ctx: Context,
    ) -> list[EnrolledUser]:
        """Get the list of users enrolled in a course (classmates and
        instructors), with their role. Same data visible in PLATO's own
        participant list to any enrolled student."""
        return get_enrolled_users_for(get_client(ctx), course_id)
