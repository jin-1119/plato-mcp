"""Tool: list_glossaries (issue #109).

mod_glossary is not present in any of the 11 currently-enrolled real
courses (live scan, 2026-10-17) -- forward-looking coverage only.
`mod_glossary_get_glossaries_by_courses` is live-verified (correctly
empty). Everything else in the 18-function mod_glossary family --
entries by letter/date/author/category/search/term, categories, authors,
and the entry-writes (add_entry, update_entry, delete_entry) -- needs a
real glossaryid/entryid to call meaningfully, and there is no real
glossary on this account to verify any of it against. None of it is
built here. Re-check once a real glossary exists.
"""

from typing import Annotated

from mcp.server.mcpserver import Context
from pydantic import Field

from plato_mcp.context import get_client
from plato_mcp.models import GlossarySummary
from plato_mcp.moodle_client import MoodleClient
from plato_mcp.tool_annotations import READ_ONLY_TOOL_ANNOTATIONS


def list_glossaries_for(client: MoodleClient, course_ids: list[int]) -> list[GlossarySummary]:
    result = client.call("mod_glossary_get_glossaries_by_courses", courseids=course_ids)
    return [GlossarySummary(**g) for g in result.get("glossaries", [])]


def register(mcp) -> None:
    @mcp.tool(annotations=READ_ONLY_TOOL_ANNOTATIONS)
    async def list_glossaries(
        course_ids: Annotated[
            list[int], Field(description="One or more course ids to list glossaries for.")
        ],
        ctx: Context,
    ) -> list[GlossarySummary]:
        """List Glossary activities across one or more courses. Reading/
        adding entries is not supported by this server -- this tool is
        read-only coverage only."""
        return list_glossaries_for(get_client(ctx), course_ids)
