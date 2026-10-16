"""Tools: list_forums, get_forum_discussions, get_discussion_posts (read),
add_discussion_post (write) -- issue #86.

IMPORTANT: standard Moodle forums (`mod_forum`) are a DIFFERENT module from
this repo's custom `ubboard` scraper (PNU's own notice/Q&A board -- not
open source, not a Moodle core module, handled entirely by
`plato_mcp.ubboard`). No course on this account currently uses `mod_forum`
(confirmed live, 2026-10-17: `mod_forum_get_forums_by_courses` returns an
empty list against real courses). This file exists purely so a course
that *does* use a standard forum is covered -- if you're looking for
notices/Q&A on PLATO itself, that's `list_notices`/`list_qna`, not here.

Subscription/pin/favourite/lock-state functions (mod_forum_set_lock_state,
set_pin_state, set_subscription_state, toggle_favourite_state) are NOT
wired to tools: set_lock_state/set_pin_state are moderator-only actions a
student account cannot perform (and there's no real forum to confirm the
exact permission error against); set_subscription_state/
toggle_favourite_state are plausible student actions but there's no real
discussion to verify the write against, so building them now would be
guessing. Revisit once a real forum exists.
"""

from typing import Annotated

from mcp.server.mcpserver import Context
from pydantic import Field

from plato_mcp.context import get_client
from plato_mcp.models import ForumDiscussion, ForumPost, ForumSummary
from plato_mcp.moodle_client import MoodleClient
from plato_mcp.tool_annotations import READ_ONLY_TOOL_ANNOTATIONS
from plato_mcp.write_tools import (
    WRITE_TOOL_ANNOTATIONS,
    WriteResult,
    default_preview_tracker,
    executed_result,
    preview_result,
)

ACTION_ADD_DISCUSSION = "add_discussion"
ACTION_ADD_DISCUSSION_POST = "add_discussion_post"

_FORUM_ID_FIELD = Field(description="Forum id, e.g. from list_forums.")
_DISCUSSION_ID_FIELD = Field(description="Discussion id, e.g. from get_forum_discussions.")


def list_forums_for(client: MoodleClient, course_ids: list[int]) -> list[ForumSummary]:
    result = client.call("mod_forum_get_forums_by_courses", courseids=course_ids)
    return [ForumSummary(**f) for f in result]


def get_forum_discussions_for(client: MoodleClient, forum_id: int) -> list[ForumDiscussion]:
    result = client.call("mod_forum_get_forum_discussions", forumid=forum_id)
    return [ForumDiscussion(**d) for d in result.get("discussions", [])]


def get_discussion_posts_for(client: MoodleClient, discussion_id: int) -> list[ForumPost]:
    result = client.call("mod_forum_get_discussion_posts", discussionid=discussion_id)
    return [ForumPost(**p) for p in result.get("posts", [])]


def add_discussion_for(
    client: MoodleClient,
    forum_id: int,
    subject: str,
    message: str,
    dry_run: bool = True,
) -> WriteResult:
    """Start a new discussion thread in a forum. IRREVERSIBLE once
    dry_run=False -- same preview/confirm pattern as add_discussion_post."""
    action_params = {"forum_id": forum_id, "subject": subject, "message": message}
    preview = {**action_params}

    if dry_run:
        default_preview_tracker.record_preview(
            client.session_key, ACTION_ADD_DISCUSSION, action_params
        )
        return preview_result(preview, f"New discussion in forum #{forum_id}")

    default_preview_tracker.require_previewed(
        client.session_key, ACTION_ADD_DISCUSSION, action_params
    )
    client.call(
        "mod_forum_add_discussion", forumid=forum_id, subject=subject, message=message
    )
    return executed_result(preview, f"New discussion in forum #{forum_id}")


def add_discussion_post_for(
    client: MoodleClient,
    discussion_id: int,
    message: str,
    subject: str | None = None,
    dry_run: bool = True,
) -> WriteResult:
    """Reply to an existing forum discussion. IRREVERSIBLE once dry_run=False
    -- same preview/confirm pattern as submit_assignment/post_qna_question
    (docs/write_confirmation_pattern.md)."""
    action_params = {"discussion_id": discussion_id, "message": message, "subject": subject}
    preview = {**action_params}

    if dry_run:
        default_preview_tracker.record_preview(
            client.session_key, ACTION_ADD_DISCUSSION_POST, action_params
        )
        return preview_result(preview, f"Reply to discussion #{discussion_id}")

    default_preview_tracker.require_previewed(
        client.session_key, ACTION_ADD_DISCUSSION_POST, action_params
    )
    params = {"discussionid": discussion_id, "message": message}
    if subject:
        params["subject"] = subject
    client.call("mod_forum_add_discussion_post", **params)
    return executed_result(preview, f"Reply to discussion #{discussion_id}")


def register(mcp) -> None:
    @mcp.tool(annotations=READ_ONLY_TOOL_ANNOTATIONS)
    async def list_forums(
        course_ids: Annotated[
            list[int], Field(description="One or more course ids to list forums for.")
        ],
        ctx: Context,
    ) -> list[ForumSummary]:
        """List standard Moodle forums across one or more courses. NOT the
        same as PLATO's notice/Q&A board (use list_notices/list_qna for
        that) -- this covers the separate, less-commonly-used mod_forum
        module."""
        return list_forums_for(get_client(ctx), course_ids)

    @mcp.tool(annotations=READ_ONLY_TOOL_ANNOTATIONS)
    async def get_forum_discussions(
        forum_id: Annotated[int, _FORUM_ID_FIELD],
        ctx: Context,
    ) -> list[ForumDiscussion]:
        """List discussion threads in one standard Moodle forum."""
        return get_forum_discussions_for(get_client(ctx), forum_id)

    @mcp.tool(annotations=READ_ONLY_TOOL_ANNOTATIONS)
    async def get_discussion_posts(
        discussion_id: Annotated[int, _DISCUSSION_ID_FIELD],
        ctx: Context,
    ) -> list[ForumPost]:
        """Get all posts in one forum discussion thread."""
        return get_discussion_posts_for(get_client(ctx), discussion_id)

    @mcp.tool(annotations=WRITE_TOOL_ANNOTATIONS)
    async def add_discussion(
        forum_id: Annotated[int, _FORUM_ID_FIELD],
        subject: Annotated[str, Field(description="Thread subject/title.")],
        message: Annotated[str, Field(description="Thread body content.")],
        ctx: Context,
        dry_run: Annotated[
            bool,
            Field(
                description="If True (default), only preview the new discussion without "
                "posting it. Call again with dry_run=False (same parameters) to actually post."
            ),
        ] = True,
    ) -> WriteResult:
        """Start a new discussion thread in a forum. IRREVERSIBLE once dry_run=False.

        Call with dry_run=True (default) first, show the preview to the user,
        and only call again with dry_run=False after they explicitly confirm.
        """
        return add_discussion_for(get_client(ctx), forum_id, subject, message, dry_run)

    @mcp.tool(annotations=WRITE_TOOL_ANNOTATIONS)
    async def add_discussion_post(
        discussion_id: Annotated[int, _DISCUSSION_ID_FIELD],
        message: Annotated[str, Field(description="Reply content.")],
        ctx: Context,
        subject: Annotated[
            str | None, Field(description="Optional subject override for the reply.")
        ] = None,
        dry_run: Annotated[
            bool,
            Field(
                description="If True (default), only preview the reply without sending it. "
                "Call again with dry_run=False (same parameters) to actually post it."
            ),
        ] = True,
    ) -> WriteResult:
        """Reply to a forum discussion thread. IRREVERSIBLE once dry_run=False.

        Call with dry_run=True (default) first, show the preview to the user,
        and only call again with dry_run=False after they explicitly confirm.
        """
        return add_discussion_post_for(get_client(ctx), discussion_id, message, subject, dry_run)
