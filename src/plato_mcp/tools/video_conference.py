"""Tool: list_video_conferences (issue #91).

Neither mod_bigbluebuttonbn nor mod_zoom appears in any of the 11
currently-enrolled real courses (live scan, 2026-10-17) -- forward-looking
coverage, not a fix for an observed gap.

`mod_bigbluebuttonbn_get_bigbluebuttonbns_by_courses` is live-verified
(correctly returns an empty list against a real course). Everything else
in scope -- `get_join_url`, `can_join`, `meeting_info` (BBB), and
`mod_zoom_get_state` -- needs a real module instance id to call
meaningfully; a minimal `mod_zoom_get_state` call against a fake id
returned `invalidparameter` (the real required parameter shape wasn't
determined, same as a few other "no real instance to test against"
functions elsewhere in this epic). No get_join_url tool was built: a join
URL is only meaningful for a real meeting, and guessing at the
unverified request/response shape for both module types in one function
is worse than not building it. Re-check once a course with either module
exists.
"""

from typing import Annotated

from mcp.server.mcpserver import Context
from pydantic import Field

from plato_mcp.context import get_client
from plato_mcp.models import VideoConference
from plato_mcp.moodle_client import MoodleClient
from plato_mcp.tool_annotations import READ_ONLY_TOOL_ANNOTATIONS


def list_video_conferences_for(
    client: MoodleClient, course_ids: list[int]
) -> list[VideoConference]:
    result = client.call(
        "mod_bigbluebuttonbn_get_bigbluebuttonbns_by_courses", courseids=course_ids
    )
    return [VideoConference(**b) for b in result.get("bigbluebuttonbns", [])]


def register(mcp) -> None:
    @mcp.tool(annotations=READ_ONLY_TOOL_ANNOTATIONS)
    async def list_video_conferences(
        course_ids: Annotated[
            list[int], Field(description="One or more course ids to list video conferences for.")
        ],
        ctx: Context,
    ) -> list[VideoConference]:
        """List BigBlueButton video-conference activities across one or
        more courses. Joining a meeting is not supported by this server --
        this tool is read-only coverage only. Zoom activities (mod_zoom)
        are not covered -- no real instance has existed to verify against."""
        return list_video_conferences_for(get_client(ctx), course_ids)
