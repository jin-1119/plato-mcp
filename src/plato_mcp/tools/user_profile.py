"""Tools: get_user_profile, get_private_files_info, get_user_preferences,
add_private_file (issue #96).

Audited all 16 core_user_* functions against the real account. Decisions:

- `core_user_get_course_user_profiles` -- wired as get_user_profile.
  Deliberately NOT `core_user_get_users_by_field` (which can look up
  *any* user by email/username/etc, not just classmates sharing a
  course) -- the course-scoped function is the privacy-appropriate one,
  same reasoning as the existing docs/pii_review.md classmate-content
  caveats.
- `core_user_get_private_files_info` -- wired as get_private_files_info.
  Confirmed live (0 files/folders for this account).
- `core_user_add_user_private_files` -- wired as add_private_file,
  reusing #84's multipart upload helper (MoodleClient.upload_file +
  get_unused_draft_itemid) rather than writing a second uploader. Only
  the dry_run=True (preview) path has been exercised live -- dry_run=False
  was deliberately NOT executed during this issue's research, because
  there is no delete tool for private files on this account yet; leaving
  a permanent live test artifact needs the user's own go-ahead, not
  routine automated verification (same gate as #100's remove_submission).
- `core_user_get_user_preferences` -- wired as get_user_preferences.
  Confirmed live, but the returned values are mostly Moodle's own
  internal UI state (e.g. `myCourseHideThumbnail`, `pw_nav`), not
  information meaningful to surface to an end user on its own merit --
  exposed anyway per this issue's acceptance criteria, with that caveat
  in the tool's docstring.
- `core_user_set_user_preferences`/`update_user_preferences` -- NOT
  wired. No real use case for an AI assistant to mutate Moodle's own UI
  state on a user's behalf.
- `core_user_get_users_by_field`/`view_user_profile`/`view_user_list` --
  NOT wired (privacy scope / view-logging, respectively -- same
  reasoning as the other `view_*` decisions in #100/#103).
- Device registration (`add_user_device`/`remove_user_device`/
  `update_user_device_public_key`) -- NOT wired. These register a
  physical device for native mobile push notifications; no meaning for
  an MCP server.
- `update_picture` -- NOT wired. No real use case for an AI to change a
  user's profile picture unprompted.
- `agree_site_policy` -- NOT wired, deliberately. An AI should not accept
  legal/site policies on a user's behalf -- same reasoning as #115's
  tool_policy_set_acceptances_status decision.
- `prepare_private_files_for_edition`/`update_private_files` -- part of
  the same private-files write flow as add_user_private_files; not
  separately wired (no second write path needed for this scope).
"""

from pathlib import Path
from typing import Annotated

from mcp.server.mcpserver import Context
from pydantic import Field

from plato_mcp.context import get_client, get_userid
from plato_mcp.errors import PlatoMCPError
from plato_mcp.models import PrivateFilesInfo, UserPreference, UserProfile
from plato_mcp.moodle_client import MoodleClient
from plato_mcp.tool_annotations import READ_ONLY_TOOL_ANNOTATIONS
from plato_mcp.write_tools import (
    WRITE_TOOL_ANNOTATIONS,
    WriteResult,
    default_preview_tracker,
    executed_result,
    preview_result,
)

ACTION_ADD_PRIVATE_FILE = "add_private_file"


def get_user_profile_for(client: MoodleClient, course_id: int, userid: int) -> UserProfile:
    result = client.call(
        "core_user_get_course_user_profiles",
        **{"userlist[0][userid]": userid, "userlist[0][courseid]": course_id},
    )
    return UserProfile(**result[0])


def get_private_files_info_for(client: MoodleClient, userid: int) -> PrivateFilesInfo:
    result = client.call("core_user_get_private_files_info", userid=userid)
    return PrivateFilesInfo(**result)


def get_user_preferences_for(client: MoodleClient) -> list[UserPreference]:
    result = client.call("core_user_get_user_preferences")
    return [UserPreference(**p) for p in result.get("preferences", [])]


def add_private_file_for(client: MoodleClient, file_path: str, dry_run: bool = True) -> WriteResult:
    """Upload a file into this account's Moodle private files area.
    IRREVERSIBLE once dry_run=False -- there is currently no delete tool
    for private files, so this permanently adds the file until the user
    removes it themselves via PLATO's own UI."""
    action_params = {"file_path": file_path}
    path = Path(file_path)
    preview = {**action_params, "exists": path.is_file()}

    if dry_run:
        default_preview_tracker.record_preview(
            client.session_key, ACTION_ADD_PRIVATE_FILE, action_params
        )
        return preview_result(preview, f"Private file upload for '{path.name}'")

    default_preview_tracker.require_previewed(
        client.session_key, ACTION_ADD_PRIVATE_FILE, action_params
    )
    if not path.is_file():
        raise PlatoMCPError(f"File not found: {file_path!r}")

    itemid = client.get_unused_draft_itemid()
    client.upload_file(itemid, path.name, path.read_bytes())
    client.call("core_user_add_user_private_files", draftid=itemid)
    return executed_result(preview, f"Private file upload for '{path.name}'")


def register(mcp) -> None:
    @mcp.tool(annotations=READ_ONLY_TOOL_ANNOTATIONS)
    async def get_user_profile(
        course_id: Annotated[
            int, Field(description="PLATO/Moodle numeric course id both accounts share.")
        ],
        ctx: Context,
        userid: Annotated[
            int | None,
            Field(description="User id to look up. Omit to get this account's own profile."),
        ] = None,
    ) -> UserProfile:
        """Get a user's profile, scoped to a shared course (not a global
        user search -- see docs/pii_review.md)."""
        client = get_client(ctx)
        target_userid = userid if userid is not None else get_userid(client)
        return get_user_profile_for(client, course_id, target_userid)

    @mcp.tool(annotations=READ_ONLY_TOOL_ANNOTATIONS)
    async def get_private_files_info(ctx: Context) -> PrivateFilesInfo:
        """Get a summary (file/folder count, total size) of this account's
        Moodle private files area."""
        client = get_client(ctx)
        return get_private_files_info_for(client, get_userid(client))

    @mcp.tool(annotations=READ_ONLY_TOOL_ANNOTATIONS)
    async def get_user_preferences(ctx: Context) -> list[UserPreference]:
        """Get this account's Moodle user preferences. Note: most of these
        are internal UI state (e.g. which dashboard sections are
        collapsed), not information meaningful on its own."""
        return get_user_preferences_for(get_client(ctx))

    @mcp.tool(annotations=WRITE_TOOL_ANNOTATIONS)
    async def add_private_file(
        file_path: Annotated[str, Field(description="Local file path to upload.")],
        ctx: Context,
        dry_run: Annotated[
            bool,
            Field(
                description="If True (default), only preview the upload without doing it. "
                "Call again with dry_run=False (same parameters) to actually upload it."
            ),
        ] = True,
    ) -> WriteResult:
        """Upload a file to this account's Moodle private files area.
        IRREVERSIBLE once dry_run=False -- no delete tool exists for
        private files yet, so this permanently adds the file until the
        user removes it via PLATO's own UI. Only works when this server
        is running locally (stdio).

        Call with dry_run=True (default) first, show the preview to the
        user, and only call again with dry_run=False after they explicitly
        confirm.
        """
        return add_private_file_for(get_client(ctx), file_path, dry_run)
