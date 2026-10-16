"""Tool: get_unread_messages (issue #17).

Issues #87/#104/#105 (Phase 7 epic #83) set out to build real
person-to-person conversation reading/sending/contacts on top of
`core_message_*`. Live testing found PLATO has **real-time messaging
disabled site-wide** -- confirmed via direct errors (not empty results)
from `core_message_get_conversations`, `get_conversation_counts`,
`get_self_conversation`, `get_member_info`,
`data_for_messagearea_search_messages`, `send_instant_messages`, and
`get_user_contacts`, all returning
`{"errorcode": "disabled", "message": "이 사이트에서는 소식 전달이 안 됨"}`
("message delivery is not enabled on this site"). This is a site
administration setting (Moodle's `messaging` config), not a per-course or
per-account restriction -- nothing built on `core_message_*` conversation
functions can work here regardless of what account calls it.

What DOES still work, confirmed live: `core_message_get_messages`
(notifications, already used by get_unread_messages below) and
`core_message_get_unread_notification_count` (returned a real count, 2,
live) -- these are the separate *notifications* system, not conversations,
and aren't affected by the messaging-disabled setting.

No new tools were built for #87/#104/#105 as a result -- there is nothing
to build. If PLATO ever enables site messaging, this finding should be
re-verified before resuming that work.
"""

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


def get_unread_notification_count_for(client: MoodleClient) -> int:
    userid = get_userid(client)
    return client.call("core_message_get_unread_notification_count", useridto=userid)


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

    @mcp.tool(annotations=READ_ONLY_TOOL_ANNOTATIONS)
    async def get_unread_notification_count(ctx: Context) -> int:
        """Get a count of this account's unread notifications (a cheaper
        check than get_unread_messages when you don't need the content).
        Note: PLATO has person-to-person messaging disabled site-wide, so
        this counts notifications only, not conversation messages."""
        return get_unread_notification_count_for(get_client(ctx))
