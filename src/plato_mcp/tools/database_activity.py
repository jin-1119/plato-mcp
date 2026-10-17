"""Tool: list_database_activities (issue #110).

mod_data ("Database" activity) is not present in any of the 11
currently-enrolled real courses (live scan, 2026-10-17) -- forward-looking
coverage only. `mod_data_get_databases_by_courses` is live-verified
(correctly empty). Everything else in the 11-function mod_data family --
fields, entries, search, and the entry-writes (add_entry, update_entry,
delete_entry, approve_entry) -- needs a real databaseid/entryid to call
meaningfully, and there is no real database activity on this account to
verify any of it against. None of it is built here. Re-check once a real
database activity exists.
"""

from typing import Annotated

from mcp.server.mcpserver import Context
from pydantic import Field

from plato_mcp.context import get_client
from plato_mcp.models import DatabaseActivitySummary
from plato_mcp.moodle_client import MoodleClient
from plato_mcp.tool_annotations import READ_ONLY_TOOL_ANNOTATIONS


def list_database_activities_for(
    client: MoodleClient, course_ids: list[int]
) -> list[DatabaseActivitySummary]:
    result = client.call("mod_data_get_databases_by_courses", courseids=course_ids)
    return [DatabaseActivitySummary(**d) for d in result.get("databases", [])]


def register(mcp) -> None:
    @mcp.tool(annotations=READ_ONLY_TOOL_ANNOTATIONS)
    async def list_database_activities(
        course_ids: Annotated[
            list[int], Field(description="One or more course ids to list database activities for.")
        ],
        ctx: Context,
    ) -> list[DatabaseActivitySummary]:
        """List Database ("mod_data") activities across one or more
        courses. Reading/adding entries is not supported by this server --
        this tool is read-only coverage only."""
        return list_database_activities_for(get_client(ctx), course_ids)
