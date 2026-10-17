"""Tool: list_feedbacks (issue #106).

mod_feedback (surveys) is not present in any of the 11
currently-enrolled real courses (live scan, 2026-10-17) -- forward-looking
coverage only. `mod_feedback_get_feedbacks_by_courses` is live-verified
(correctly returns an empty list). Everything else in the 14-function
mod_feedback family -- items, analysis, responses, and especially the
response-submission writes (launch_feedback, process_page) -- needs a
real feedbackid/response to call meaningfully, and there is no real
feedback activity on this account to verify any of it against. None of
it is built here. Re-check once a real feedback activity exists.
"""

from typing import Annotated

from mcp.server.mcpserver import Context
from pydantic import Field

from plato_mcp.context import get_client
from plato_mcp.models import FeedbackSummary
from plato_mcp.moodle_client import MoodleClient
from plato_mcp.tool_annotations import READ_ONLY_TOOL_ANNOTATIONS


def list_feedbacks_for(client: MoodleClient, course_ids: list[int]) -> list[FeedbackSummary]:
    result = client.call("mod_feedback_get_feedbacks_by_courses", courseids=course_ids)
    return [FeedbackSummary(**f) for f in result.get("feedbacks", [])]


def register(mcp) -> None:
    @mcp.tool(annotations=READ_ONLY_TOOL_ANNOTATIONS)
    async def list_feedbacks(
        course_ids: Annotated[
            list[int], Field(description="One or more course ids to list feedback activities for.")
        ],
        ctx: Context,
    ) -> list[FeedbackSummary]:
        """List Feedback (survey) activities across one or more courses.
        Responding to a survey is not supported by this server -- this
        tool is read-only coverage only."""
        return list_feedbacks_for(get_client(ctx), course_ids)
