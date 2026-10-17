"""Tool: list_workshops (issue #94).

mod_workshop (peer assessment) is not present in any of the 11
currently-enrolled real courses (live scan, 2026-10-17) -- forward-looking
coverage only. `mod_workshop_get_workshops_by_courses` is live-verified
(correctly returns an empty list). Everything else in the 19-function
mod_workshop family -- submissions, assessments, grades, and especially
the submission/assessment writes (add_submission, update_submission,
evaluate_submission/assessment) -- needs a real workshopid/submissionid
to call meaningfully, and there is no real workshop on this account to
verify any of it against. None of it is built here. Re-check once a
real workshop exists.
"""

from typing import Annotated

from mcp.server.mcpserver import Context
from pydantic import Field

from plato_mcp.context import get_client
from plato_mcp.models import WorkshopSummary
from plato_mcp.moodle_client import MoodleClient
from plato_mcp.tool_annotations import READ_ONLY_TOOL_ANNOTATIONS


def list_workshops_for(client: MoodleClient, course_ids: list[int]) -> list[WorkshopSummary]:
    result = client.call("mod_workshop_get_workshops_by_courses", courseids=course_ids)
    return [WorkshopSummary(**w) for w in result.get("workshops", [])]


def register(mcp) -> None:
    @mcp.tool(annotations=READ_ONLY_TOOL_ANNOTATIONS)
    async def list_workshops(
        course_ids: Annotated[
            list[int], Field(description="One or more course ids to list workshops for.")
        ],
        ctx: Context,
    ) -> list[WorkshopSummary]:
        """List Workshop (peer assessment) activities across one or more
        courses. Submitting or assessing work is not supported by this
        server -- this tool is read-only coverage only."""
        return list_workshops_for(get_client(ctx), course_ids)
