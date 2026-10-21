"""Tools: list_assignments, get_assignment_detail (issue #14), submit_assignment (issue #25,
file-submission support added in issue #84, remote-transport upload added in issue #153),
remove_submission (issue #100).

Issue #100 audited the rest of the mod_assign student-side function family
against the real assignment (id 4975, course 5968):
- `mod_assign_get_user_flags` -- errored "No access rights in module
  context" live, same as mod_assign_get_grades in #95. Skipped, confirmed
  not accessible to a student account (these are teacher-set grading
  workflow flags -- locked/mailed/extension -- not student data).
- `mod_assign_view_assign`/`view_submission_status` -- NOT wired to any
  tool, deliberately. These are Moodle's own "mark as viewed" logging
  calls: calling them as a side effect of an AI read would mutate
  server-side completion/viewed state the student didn't actually
  trigger themselves. A tool call is not the same as a student opening
  the page in their browser, and plato-mcp should not pretend otherwise.
"""

import base64
import binascii
import hashlib
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

from mcp.server.mcpserver import Context
from pydantic import BaseModel, Field

from plato_mcp.context import get_client, get_userid
from plato_mcp.errors import PlatoMCPError
from plato_mcp.models import (
    AssignmentDetail,
    AssignmentExtraData,
    AssignmentSummary,
    PreviousAttempt,
    SubmissionFeedback,
    SubmissionStatus,
)
from plato_mcp.moodle_client import MoodleClient
from plato_mcp.tool_annotations import READ_ONLY_TOOL_ANNOTATIONS
from plato_mcp.write_tools import (
    WRITE_TOOL_ANNOTATIONS,
    WriteResult,
    default_preview_tracker,
    executed_result,
    preview_result,
)

ACTION_SUBMIT_ASSIGNMENT = "submit_assignment"
ACTION_REMOVE_SUBMISSION = "remove_submission"

_COURSE_ID_FIELD = Field(description="PLATO/Moodle numeric course id, e.g. from list_courses.")
_ASSIGNMENT_ID_FIELD = Field(description="Assignment id, e.g. from list_assignments.")

# Moodle's FORMAT_PLAIN -- avoids any HTML-escaping ambiguity for a plain text submission.
FORMAT_PLAIN = 2

# Same conservative course-material allowlist files.py uses for downloads --
# applied here too when the assignment's own `filetypeslist` config doesn't
# restrict extensions (PLATO's real assignment, course 5968, left this
# empty -- "no restriction" -- so without our own floor, an AI caller could
# upload anything, including an executable).
DEFAULT_ALLOWED_UPLOAD_EXTENSIONS = {
    ".pdf",
    ".ppt",
    ".pptx",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".hwp",
    ".zip",
    ".txt",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
}

# Separate from any assignment-specific max_size_bytes (a Moodle-side setting):
# this caps how much base64-inflated payload a single remote-transport upload
# can push through a tool call/MCP context at all (issue #153). Mirrors the
# role files.py's INLINE_BASE64_MAX_MB plays for downloads, but kept as its
# own constant -- the two numbers mean different things and aren't coupled.
INLINE_UPLOAD_MAX_MB = 5


class InlineFileUpload(BaseModel):
    """One file's content, handed to the server directly over remote
    (streamable-http) transport -- there's no local filesystem for the
    server to read from there, so the client must send the bytes itself
    (issue #153). The upload-direction counterpart to files.py's
    DownloadContentResult."""

    filename: str
    content_base64: str


@dataclass
class _PendingUpload:
    """A file ready to upload, normalized from either transport so the rest
    of submit_assignment_for (validation, then the actual upload) never has
    to branch on where the bytes came from.

    `read` is a callable rather than plain `bytes` so the stdio path can
    keep its existing lazy-read behavior -- dry_run only needs the file's
    size (via `stat()`), not its content, so the preview path never reads a
    file's bytes off disk. For the remote path the bytes are already in
    memory by this point, so `read` is just a closure over them.
    """

    filename: str
    size_bytes: int
    read: Callable[[], bytes]


def _pending_uploads_from_paths(file_paths: list[str]) -> list[_PendingUpload]:
    uploads: list[_PendingUpload] = []
    for raw_path in file_paths:
        path = Path(raw_path)
        if not path.is_file():
            raise PlatoMCPError(f"File not found: {raw_path!r}")
        uploads.append(_PendingUpload(path.name, path.stat().st_size, path.read_bytes))
    return uploads


def _pending_uploads_from_contents(items: list[InlineFileUpload]) -> list[_PendingUpload]:
    uploads: list[_PendingUpload] = []
    for item in items:
        safe_name = Path(item.filename).name
        if not safe_name or safe_name != item.filename:
            raise PlatoMCPError(
                f"filename must be a plain file name with no path separators: {item.filename!r}"
            )
        try:
            data = base64.b64decode(item.content_base64, validate=True)
        except binascii.Error:
            raise PlatoMCPError(f"content_base64 for {safe_name!r} is not valid base64.") from None
        if len(data) > INLINE_UPLOAD_MAX_MB * 1024 * 1024:
            raise PlatoMCPError(
                f"File {safe_name!r} is {len(data)} bytes, exceeding the "
                f"{INLINE_UPLOAD_MAX_MB}MB inline-upload cap for remote transport."
            )
        uploads.append(_PendingUpload(safe_name, len(data), (lambda d=data: d)))
    return uploads


def list_assignments_for(client: MoodleClient, course_ids: list[int]) -> list[AssignmentSummary]:
    result = client.call("mod_assign_get_assignments", courseids=course_ids)
    summaries: list[AssignmentSummary] = []
    for course in result.get("courses", []):
        for assignment in course.get("assignments", []):
            summaries.append(AssignmentSummary(**{**assignment, "courseid": course.get("id")}))
    return summaries


def get_assignment_detail_for(
    client: MoodleClient, course_id: int, assignment_id: int
) -> AssignmentDetail:
    assignments = list_assignments_for(client, [course_id])
    match = next((a for a in assignments if a.id == assignment_id), None)
    if match is None:
        raise ValueError(f"Assignment {assignment_id} not found in course {course_id}")

    userid = get_userid(client)
    status = client.call("mod_assign_get_submission_status", assignid=assignment_id, userid=userid)

    lastattempt = status.get("lastattempt") or {}
    submission_raw = lastattempt.get("submission")

    submission = None
    if submission_raw:
        timemodified = submission_raw.get("timemodified")
        late = bool(
            timemodified
            and match.duedate
            and datetime.fromtimestamp(timemodified, tz=UTC) > match.duedate
        )
        submitted_files = []
        for plugin in submission_raw.get("plugins", []):
            if plugin.get("type") != "file":
                continue
            for filearea in plugin.get("fileareas", []):
                submitted_files.extend(filearea.get("files", []))
        submission = SubmissionStatus(
            submitted=submission_raw.get("status") == "submitted",
            status=submission_raw.get("status"),
            late=late,
            timemodified=timemodified,
            cansubmit=lastattempt.get("cansubmit"),
            locked=lastattempt.get("locked"),
            extensionduedate=lastattempt.get("extensionduedate"),
            gradingstatus=lastattempt.get("gradingstatus"),
            submitted_files=submitted_files,
        )

    feedback_raw = status.get("feedback")
    feedback = SubmissionFeedback(**feedback_raw) if feedback_raw else None

    previousattempts = [
        PreviousAttempt(**attempt) for attempt in (status.get("previousattempts") or [])
    ]

    assignmentdata_raw = status.get("assignmentdata")
    extra = AssignmentExtraData(**assignmentdata_raw) if assignmentdata_raw else None

    return AssignmentDetail(
        assignment=match,
        submission=submission,
        feedback=feedback,
        previousattempts=previousattempts,
        extra=extra,
    )


def _check_upload_rules(match: AssignmentSummary, uploads: list[_PendingUpload]) -> None:
    """Check pending uploads against this assignment's real, live-fetched
    submission-plugin config (issue #84), regardless of which transport they
    came from (issue #153 unified file_paths and file_contents onto the same
    _PendingUpload shape so this validation can't drift between the two).
    Raises PlatoMCPError with a specific reason on any violation."""
    file_cfg = match.file_submission
    if not file_cfg.known:
        raise PlatoMCPError(
            f"Assignment '{match.name}' did not report whether it accepts file "
            "submissions (no assignsubmission_file config in the API response) -- "
            "refusing to guess. Check get_assignment_detail's file_submission field, "
            "or use text instead."
        )
    if not file_cfg.enabled:
        raise PlatoMCPError(
            f"Assignment '{match.name}' does not accept file submissions "
            "(assignsubmission_file is disabled for it) -- use text instead, "
            "or omit file_paths/file_contents."
        )
    if file_cfg.max_files is not None and len(uploads) > file_cfg.max_files:
        raise PlatoMCPError(
            f"Assignment '{match.name}' allows at most {file_cfg.max_files} "
            f"file(s); {len(uploads)} were given."
        )

    allowed_extensions = (
        {ext.lower() for ext in file_cfg.allowed_extensions}
        if file_cfg.allowed_extensions
        else DEFAULT_ALLOWED_UPLOAD_EXTENSIONS
    )

    for upload in uploads:
        ext = Path(upload.filename).suffix.lower()
        if ext not in allowed_extensions:
            raise PlatoMCPError(
                f"File extension {ext!r} not allowed for this assignment "
                f"(allowed: {sorted(allowed_extensions)})."
            )
        if file_cfg.max_size_bytes is not None and upload.size_bytes > file_cfg.max_size_bytes:
            raise PlatoMCPError(
                f"File {upload.filename!r} is {upload.size_bytes} bytes, exceeding "
                f"this assignment's max_size_bytes={file_cfg.max_size_bytes}."
            )


def submit_assignment_for(
    client: MoodleClient,
    headers: Mapping[str, str] | None,
    course_id: int,
    assignment_id: int,
    text: str = "",
    file_paths: list[str] | None = None,
    file_contents: list[InlineFileUpload] | None = None,
    dry_run: bool = True,
) -> WriteResult:
    """Submit text and/or file content for an assignment (see
    docs/write_confirmation_pattern.md).

    File support (issue #84): the real Moodle file-submission flow is a
    draft-area itemid (`core_files_get_unused_draft_itemid`) + a separate
    multipart upload to `/webservice/upload.php` (NOT a wsfunction -- see
    MoodleClient.upload_file) per file, then `mod_assign_save_submission`
    referencing that itemid via `plugindata[files_filemanager]`. Confirmed
    working live against this account's real draft area during planning;
    confirmed live end-to-end (including the actual assignment) as part of
    this issue's verification.

    Transport determines whether `file_paths` is usable (issue #153, mirroring
    download_course_file's stdio-vs-remote split from issue #55, detected the
    same way via `headers is None`):
      - stdio (Claude Code/Desktop): the server runs on the user's own
        machine, so `file_paths` (local filesystem paths) works.
      - streamable-http (Smithery/remote): the server's disk is not the end
        user's, so `file_paths` is rejected with a clear transport error
        instead of a misleading "File not found".
    `file_contents` (filename + base64-encoded bytes) works over *either*
    transport -- there's no reason to refuse it locally, it's simply the only
    option remotely -- capped at INLINE_UPLOAD_MAX_MB per file.

    dry_run=False is only allowed after a matching dry_run=True preview (same
    session, course_id, assignment_id, text, file_paths, and file_contents) --
    see write_tools.PreviewTracker (issue #37). This is enforced server-side,
    not just a docstring convention. The preview/confirm matching key for
    file_contents uses each file's sha256 (not its raw base64) so a multi-MB
    upload's bytes never have to be echoed back in the preview response or
    re-hashed by the caller.
    """
    if not text and not file_paths and not file_contents:
        raise PlatoMCPError(
            "Provide text, file_paths, and/or file_contents -- an empty submission is not valid."
        )
    if file_paths and file_contents:
        raise PlatoMCPError("Provide file_paths or file_contents, not both.")

    if headers is not None and file_paths:
        raise PlatoMCPError(
            "file_paths is only supported over stdio (local) transport -- this "
            "connection is remote, so there's no local filesystem for a path to "
            "point at. Use file_contents (filename + base64-encoded bytes) instead."
        )

    assignments = list_assignments_for(client, [course_id])
    match = next((a for a in assignments if a.id == assignment_id), None)
    if match is None:
        raise ValueError(f"Assignment {assignment_id} not found in course {course_id}")

    uploads: list[_PendingUpload] = []
    if file_paths:
        uploads = _pending_uploads_from_paths(file_paths)
    elif file_contents:
        uploads = _pending_uploads_from_contents(file_contents)
    if uploads:
        _check_upload_rules(match, uploads)

    # Fail-open here, unlike the file-submission check above: text submission
    # predates issue #84 and has always been sent unconditionally, so only
    # block it on an *explicit* "disabled" from the API, not merely because
    # `configs` is empty/unknown (older/incomplete responses, or tests that
    # don't set it) -- preserves pre-#84 behavior for the common case.
    text_cfg = match.onlinetext_submission
    if text and text_cfg.known and not text_cfg.enabled:
        raise PlatoMCPError(
            f"Assignment '{match.name}' does not accept online text submissions "
            "(assignsubmission_onlinetext is disabled for it) -- use file_paths/"
            "file_contents instead, or omit text."
        )

    action_params = {
        "course_id": course_id,
        "assignment_id": assignment_id,
        "text": text,
        "file_paths": sorted(file_paths) if file_paths else [],
        "file_contents": sorted(
            (
                {"filename": u.filename, "sha256": hashlib.sha256(u.read()).hexdigest()}
                for u in (uploads if file_contents else [])
            ),
            key=lambda d: d["filename"],
        ),
    }
    preview = {
        **action_params,
        "assignment_name": match.name,
        "due_date": match.duedate.isoformat() if match.duedate else None,
        "cutoff_date": match.cutoffdate.isoformat() if match.cutoffdate else None,
        "file_sizes_bytes": {u.filename: u.size_bytes for u in uploads},
    }

    if dry_run:
        default_preview_tracker.record_preview(
            client.session_key, ACTION_SUBMIT_ASSIGNMENT, action_params
        )
        return preview_result(preview, f"Submission for '{match.name}'")

    default_preview_tracker.require_previewed(
        client.session_key, ACTION_SUBMIT_ASSIGNMENT, action_params
    )

    plugindata: dict = {}
    if text:
        plugindata.update(
            {
                "plugindata[onlinetext_editor][text]": text,
                "plugindata[onlinetext_editor][format]": FORMAT_PLAIN,
                "plugindata[onlinetext_editor][itemid]": 0,
            }
        )
    if uploads:
        itemid = client.get_unused_draft_itemid()
        for upload in uploads:
            client.upload_file(itemid, upload.filename, upload.read())
        plugindata["plugindata[files_filemanager]"] = itemid

    client.call("mod_assign_save_submission", assignmentid=assignment_id, **plugindata)
    return executed_result(preview, f"Submission for '{match.name}'")


def remove_submission_for(
    client: MoodleClient, course_id: int, assignment_id: int, dry_run: bool = True
) -> WriteResult:
    """Withdraw/clear this account's own submission for an assignment
    (issue #100). IRREVERSIBLE and DESTRUCTIVE once dry_run=False -- this
    discards already-submitted work (any files/text sent via
    submit_assignment), not just a draft. Same preview/confirm pattern as
    submit_assignment (docs/write_confirmation_pattern.md).

    **KNOWN UNVERIFIED, live-tested and failing as of issue #100**: calling
    `mod_assign_remove_submission` with `assignmentid` (the parameter name
    Moodle 4.5 source documents) against the real assignment on this
    account returns `invalidparameter` every time -- also tried
    `assignid`, `+userid`, `+plugin=''`, zero params, and GET instead of
    POST, all with the identical generic error (no field-specific detail
    in the error message). The real required parameter shape could not be
    determined empirically. The call is kept here (rather than removed)
    because it's still the most plausible shape from source, dry_run=True
    costs nothing, and a future session with a different test assignment
    may have better luck -- but do not assume dry_run=False actually works
    until it's been seen to succeed live. The real test submission (#84)
    was NOT removed by any of these failed attempts -- an erroring call
    makes no server-side change.
    """
    assignments = list_assignments_for(client, [course_id])
    match = next((a for a in assignments if a.id == assignment_id), None)
    if match is None:
        raise ValueError(f"Assignment {assignment_id} not found in course {course_id}")

    action_params = {"course_id": course_id, "assignment_id": assignment_id}
    preview = {**action_params, "assignment_name": match.name}

    if dry_run:
        default_preview_tracker.record_preview(
            client.session_key, ACTION_REMOVE_SUBMISSION, action_params
        )
        return preview_result(preview, f"Removal of submission for '{match.name}'")

    default_preview_tracker.require_previewed(
        client.session_key, ACTION_REMOVE_SUBMISSION, action_params
    )
    client.call("mod_assign_remove_submission", assignmentid=assignment_id)
    return executed_result(preview, f"Removal of submission for '{match.name}'")


def register(mcp) -> None:
    @mcp.tool(annotations=READ_ONLY_TOOL_ANNOTATIONS)
    async def list_assignments(
        course_ids: Annotated[
            list[int], Field(description="One or more course ids to list assignments for.")
        ],
        ctx: Context,
    ) -> list[AssignmentSummary]:
        """List assignments across one or more courses, with due dates."""
        return list_assignments_for(get_client(ctx), course_ids)

    @mcp.tool(annotations=READ_ONLY_TOOL_ANNOTATIONS)
    async def get_assignment_detail(
        course_id: Annotated[int, _COURSE_ID_FIELD],
        assignment_id: Annotated[int, _ASSIGNMENT_ID_FIELD],
        ctx: Context,
    ) -> AssignmentDetail:
        """Get one assignment's details and this account's submission status."""
        return get_assignment_detail_for(get_client(ctx), course_id, assignment_id)

    @mcp.tool(annotations=WRITE_TOOL_ANNOTATIONS)
    async def submit_assignment(
        course_id: Annotated[int, _COURSE_ID_FIELD],
        assignment_id: Annotated[int, _ASSIGNMENT_ID_FIELD],
        ctx: Context,
        text: Annotated[
            str,
            Field(
                description="Plain-text submission content. Omit (empty string) for a "
                "file-only submission. Rejected if this assignment doesn't accept online "
                "text -- check get_assignment_detail's onlinetext_submission.enabled first."
            ),
        ] = "",
        file_paths: Annotated[
            list[str] | None,
            Field(
                description="Local filesystem paths to upload as file attachments. Only "
                "works when this server is running locally (stdio) -- rejected with a clear "
                "error over a remote/streamable-http connection (use file_contents there "
                "instead). Rejected if this assignment doesn't accept file submissions, "
                "exceeds its max file count/size, or uses a disallowed extension -- check "
                "get_assignment_detail's file_submission (enabled/max_files/max_size_bytes/"
                "allowed_extensions) first."
            ),
        ] = None,
        file_contents: Annotated[
            list[InlineFileUpload] | None,
            Field(
                description="File attachments as {filename, content_base64} -- works over "
                "either transport, and is the only way to attach files when this server is "
                "running remotely (streamable-http), since it has no local filesystem to "
                "read a path from there. Each file is capped at "
                f"{INLINE_UPLOAD_MAX_MB}MB decoded, in addition to this assignment's own "
                "max file count/size/extension rules (see get_assignment_detail's "
                "file_submission)."
            ),
        ] = None,
        dry_run: Annotated[
            bool,
            Field(
                description="If True (default), only preview the submission without sending "
                "it. Call again with dry_run=False (same parameters) to actually submit it."
            ),
        ] = True,
    ) -> WriteResult:
        """Submit text and/or file attachments for an assignment. IRREVERSIBLE once dry_run=False.

        Call with dry_run=True (default) first, show the preview to the user, and
        only call again with dry_run=False (same parameters) after they explicitly
        confirm. Provide text, file_paths/file_contents, or both -- whichever this
        assignment actually accepts (see get_assignment_detail).

        file_paths works only when this server is running locally (stdio, e.g.
        Claude Code/Desktop) -- rejected with a clear error over a remote
        (streamable-http, e.g. a Claude.ai Connector) connection, mirroring
        download_course_file's own stdio-vs-remote split. file_contents works
        over either transport and is the only option remotely, since this
        server's disk is not reachable by you there.
        """
        return submit_assignment_for(
            get_client(ctx),
            ctx.headers,
            course_id,
            assignment_id,
            text,
            file_paths,
            file_contents,
            dry_run,
        )

    @mcp.tool(annotations=WRITE_TOOL_ANNOTATIONS)
    async def remove_submission(
        course_id: Annotated[int, _COURSE_ID_FIELD],
        assignment_id: Annotated[int, _ASSIGNMENT_ID_FIELD],
        ctx: Context,
        dry_run: Annotated[
            bool,
            Field(
                description="If True (default), only preview the removal without doing it. "
                "Call again with dry_run=False (same parameters) to actually remove it."
            ),
        ] = True,
    ) -> WriteResult:
        """Withdraw/clear this account's own submission for an assignment.
        IRREVERSIBLE and DESTRUCTIVE once dry_run=False -- this discards
        already-submitted work (files/text), not a draft.

        KNOWN ISSUE: live testing found dry_run=False currently fails with
        an "invalid parameter" error from PLATO every time (the real
        required parameter shape wasn't determined -- see
        remove_submission_for's docstring). dry_run=True (preview) works
        and is safe to call. Do not rely on dry_run=False actually working
        until this is fixed.

        Call with dry_run=True (default) first, show the preview to the user,
        and only call again with dry_run=False after they explicitly confirm.
        """
        return remove_submission_for(get_client(ctx), course_id, assignment_id, dry_run)
