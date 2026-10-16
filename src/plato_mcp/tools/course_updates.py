"""Tool: get_course_updates_since (issue #102).

This is the primitive the deferred proactive-notifications design spike
(#33, under #7 Phase 6) would need -- "what changed in this course since
timestamp X" -- researched and built now even though #33 itself stays
deferred, so that work can start from real findings instead of guessing.

Live-verified finding (findings cross-posted to #33): Moodle's
check_updates_since callback only works for modules that implement it.
The real `assign` module on this account DOES (and reports rich detail --
configuration/completion/gradeitems/submissions/grades changes, each with
itemids identifying the specific changed record). This account's custom
PNU modules (`ubfile`, `ubboard`, `vod`) do NOT implement it at all --
Moodle reports `missingcallback` for every one of them, which is an
expected outcome (not every module supports this), not an error. In
practice: this tool is only useful for standard Moodle activities
(assign, quiz, forum, etc.), not PLATO's own custom content modules --
if the goal is "notify me about a new lecture file", this specific
primitive won't see it; `ubboard`/`ubfile` would need their own polling
approach, same caveat #33's description already carried.

`core_course_check_updates` (the per-module-id sibling function) was also
verified live and returns identical data to the per-course
core_course_get_updates_since for the one module tested -- no separate
tool built for it; call get_course_updates_since for the whole course
instead of building a per-module tocheck array by hand.
"""

from typing import Annotated

from mcp.server.mcpserver import Context
from pydantic import Field

from plato_mcp.context import get_client
from plato_mcp.models import CourseModuleUpdates
from plato_mcp.moodle_client import MoodleClient
from plato_mcp.tool_annotations import READ_ONLY_TOOL_ANNOTATIONS


def get_course_updates_since_for(
    client: MoodleClient, course_id: int, since: int
) -> list[CourseModuleUpdates]:
    result = client.call("core_course_get_updates_since", courseid=course_id, since=since)
    return [CourseModuleUpdates(**i) for i in result.get("instances", [])]


def register(mcp) -> None:
    @mcp.tool(annotations=READ_ONLY_TOOL_ANNOTATIONS)
    async def get_course_updates_since(
        course_id: Annotated[
            int, Field(description="PLATO/Moodle numeric course id, e.g. from list_courses.")
        ],
        since: Annotated[
            int, Field(description="Unix timestamp -- report changes after this point in time.")
        ],
        ctx: Context,
    ) -> list[CourseModuleUpdates]:
        """Get what changed in a course since a given time -- configuration,
        completion, grades, submissions, etc. Only reports modules that
        implement Moodle's change-tracking (confirmed: the standard `assign`
        module does; this platform's own custom lecture-file/board/video
        modules do not, so this won't catch a new ubfile lecture or ubboard
        post -- use get_course_contents/list_notices to check those instead."""
        return get_course_updates_since_for(get_client(ctx), course_id, since)
