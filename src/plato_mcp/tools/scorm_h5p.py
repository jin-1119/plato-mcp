"""Tools: list_scorms, list_h5p_activities (issue #108).

Neither mod_scorm nor mod_h5pactivity is present in any of the 11
currently-enrolled real courses (live scan, 2026-10-17) -- forward-looking
coverage only. `mod_scorm_get_scorms_by_courses` and
`mod_h5pactivity_get_h5pactivities_by_courses` are both live-verified
(correctly empty). Everything else in both families -- SCOs/tracks/
attempts, results, and especially the tracking-data writes
(insert_scorm_tracks, launch_sco) -- needs a real scormid/h5pactivityid
to call meaningfully, and there is no real instance on this account to
verify any of it against. None of it is built here, deliberately --
guessing at unverified attempt/tracking-data writes is worse than not
building them. Re-check once a real SCORM or H5P activity exists.
"""

from typing import Annotated

from mcp.server.mcpserver import Context
from pydantic import Field

from plato_mcp.context import get_client
from plato_mcp.models import H5pActivitySummary, ScormSummary
from plato_mcp.moodle_client import MoodleClient
from plato_mcp.tool_annotations import READ_ONLY_TOOL_ANNOTATIONS


def list_scorms_for(client: MoodleClient, course_ids: list[int]) -> list[ScormSummary]:
    result = client.call("mod_scorm_get_scorms_by_courses", courseids=course_ids)
    return [ScormSummary(**s) for s in result.get("scorms", [])]


def list_h5p_activities_for(
    client: MoodleClient, course_ids: list[int]
) -> list[H5pActivitySummary]:
    result = client.call("mod_h5pactivity_get_h5pactivities_by_courses", courseids=course_ids)
    return [H5pActivitySummary(**a) for a in result.get("h5pactivities", [])]


def register(mcp) -> None:
    @mcp.tool(annotations=READ_ONLY_TOOL_ANNOTATIONS)
    async def list_scorms(
        course_ids: Annotated[
            list[int], Field(description="One or more course ids to list SCORM packages for.")
        ],
        ctx: Context,
    ) -> list[ScormSummary]:
        """List SCORM packaged-content activities across one or more
        courses. Launching/tracking a SCORM attempt is not supported by
        this server -- this tool is read-only coverage only."""
        return list_scorms_for(get_client(ctx), course_ids)

    @mcp.tool(annotations=READ_ONLY_TOOL_ANNOTATIONS)
    async def list_h5p_activities(
        course_ids: Annotated[
            list[int], Field(description="One or more course ids to list H5P activities for.")
        ],
        ctx: Context,
    ) -> list[H5pActivitySummary]:
        """List H5P interactive-content activities across one or more
        courses. Attempt results are not supported by this server -- this
        tool is read-only coverage only."""
        return list_h5p_activities_for(get_client(ctx), course_ids)
