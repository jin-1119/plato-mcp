"""Tool: get_unread_messages (issue #17)."""

from typing import Annotated

from mcp.server.mcpserver import Context
from pydantic import Field

from plato_mcp.context import get_client, get_userid
from plato_mcp.models import MessageItem
from plato_mcp.moodle_client import MoodleClient
from plato_mcp.tool_annotations import READ_ONLY_TOOL_ANNOTATIONS

DEFAULT_LIMIT = 20


def get_unread_messages_for(client: MoodleClient, limit: int = DEFAULT_LIMIT) -> list[MessageItem]:
    userid = get_userid(client)
    result = client.call(
        "core_message_get_messages",
        useridto=userid,
        useridfrom=0,
        type="notifications",
        read=0,
        newestfirst=1,
        limitfrom=0,
        limitnum=limit,
    )
    return [MessageItem(**m) for m in result.get("messages", [])]


def register(mcp) -> None:
    @mcp.tool(annotations=READ_ONLY_TOOL_ANNOTATIONS)
    async def get_unread_messages(
        ctx: Context,
        limit: Annotated[
            int, Field(description="Maximum number of unread notifications to return.")
        ] = DEFAULT_LIMIT,
    ) -> list[MessageItem]:
        """Get this account's unread PLATO notifications."""
        return get_unread_messages_for(get_client(ctx), limit)
