"""Tools: list_wikis, list_chats (issue #111).

Neither mod_wiki nor mod_chat is present in any of the 11
currently-enrolled real courses (live scan, 2026-10-17) -- forward-looking
coverage only. `mod_wiki_get_wikis_by_courses` and
`mod_chat_get_chats_by_courses` are both live-verified (correctly empty).
Everything else in both families -- wiki pages/subwikis, chat sessions/
messages, and especially the writes (new_page, edit_page,
send_chat_message) -- needs a real wikiid/chatid to call meaningfully,
and there is no real instance on this account to verify any of it
against. None of it is built here. Re-check once a real wiki/chat
activity exists.
"""

from typing import Annotated

from mcp.server.mcpserver import Context
from pydantic import Field

from plato_mcp.context import get_client
from plato_mcp.models import ChatSummary, WikiSummary
from plato_mcp.moodle_client import MoodleClient
from plato_mcp.tool_annotations import READ_ONLY_TOOL_ANNOTATIONS


def list_wikis_for(client: MoodleClient, course_ids: list[int]) -> list[WikiSummary]:
    result = client.call("mod_wiki_get_wikis_by_courses", courseids=course_ids)
    return [WikiSummary(**w) for w in result.get("wikis", [])]


def list_chats_for(client: MoodleClient, course_ids: list[int]) -> list[ChatSummary]:
    result = client.call("mod_chat_get_chats_by_courses", courseids=course_ids)
    return [ChatSummary(**c) for c in result.get("chats", [])]


def register(mcp) -> None:
    @mcp.tool(annotations=READ_ONLY_TOOL_ANNOTATIONS)
    async def list_wikis(
        course_ids: Annotated[
            list[int], Field(description="One or more course ids to list wikis for.")
        ],
        ctx: Context,
    ) -> list[WikiSummary]:
        """List Wiki activities across one or more courses. Reading/
        editing pages is not supported by this server -- this tool is
        read-only coverage only."""
        return list_wikis_for(get_client(ctx), course_ids)

    @mcp.tool(annotations=READ_ONLY_TOOL_ANNOTATIONS)
    async def list_chats(
        course_ids: Annotated[
            list[int], Field(description="One or more course ids to list chat rooms for.")
        ],
        ctx: Context,
    ) -> list[ChatSummary]:
        """List Chat (real-time chat room) activities across one or more
        courses. Reading/sending chat messages is not supported by this
        server -- this tool is read-only coverage only."""
        return list_chats_for(get_client(ctx), course_ids)
