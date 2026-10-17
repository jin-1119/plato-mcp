"""Tools: list_choices, list_surveys (issue #107).

Neither mod_choice nor mod_survey is present in any of the 11
currently-enrolled real courses (live scan, 2026-10-17) -- forward-looking
coverage only. `mod_choice_get_choices_by_courses` and
`mod_survey_get_surveys_by_courses` are both live-verified (correctly
empty). Everything else in both families -- options/questions, results,
and especially the response-submission writes (submit_choice_response,
submit_answers) -- needs a real choiceid/surveyid to call meaningfully,
and there is no real instance on this account to verify any of it
against. None of it is built here. Re-check once a real choice/survey
activity exists.
"""

from typing import Annotated

from mcp.server.mcpserver import Context
from pydantic import Field

from plato_mcp.context import get_client
from plato_mcp.models import ChoiceSummary, SurveySummary
from plato_mcp.moodle_client import MoodleClient
from plato_mcp.tool_annotations import READ_ONLY_TOOL_ANNOTATIONS


def list_choices_for(client: MoodleClient, course_ids: list[int]) -> list[ChoiceSummary]:
    result = client.call("mod_choice_get_choices_by_courses", courseids=course_ids)
    return [ChoiceSummary(**c) for c in result.get("choices", [])]


def list_surveys_for(client: MoodleClient, course_ids: list[int]) -> list[SurveySummary]:
    result = client.call("mod_survey_get_surveys_by_courses", courseids=course_ids)
    return [SurveySummary(**s) for s in result.get("surveys", [])]


def register(mcp) -> None:
    @mcp.tool(annotations=READ_ONLY_TOOL_ANNOTATIONS)
    async def list_choices(
        course_ids: Annotated[
            list[int], Field(description="One or more course ids to list choice activities for.")
        ],
        ctx: Context,
    ) -> list[ChoiceSummary]:
        """List Choice (single-question poll) activities across one or
        more courses. Voting is not supported by this server -- this
        tool is read-only coverage only."""
        return list_choices_for(get_client(ctx), course_ids)

    @mcp.tool(annotations=READ_ONLY_TOOL_ANNOTATIONS)
    async def list_surveys(
        course_ids: Annotated[
            list[int], Field(description="One or more course ids to list survey activities for.")
        ],
        ctx: Context,
    ) -> list[SurveySummary]:
        """List Survey activities across one or more courses. Answering is
        not supported by this server -- this tool is read-only coverage
        only."""
        return list_surveys_for(get_client(ctx), course_ids)
