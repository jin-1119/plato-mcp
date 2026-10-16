"""Tools: list_assignments, get_assignment_detail (issue #14), submit_assignment (issue #25,
file-submission support added in issue #84)."""

from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

from mcp.server.mcpserver import Context
from pydantic import Field

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
    ".pdf", ".ppt", ".pptx", ".doc", ".docx", ".xls", ".xlsx",
    ".hwp", ".zip", ".txt", ".png", ".jpg", ".jpeg", ".gif",
}


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
        submission = SubmissionStatus(
            submitted=submission_raw.get("status") == "submitted",
            status=submission_raw.get("status"),
            late=late,
            timemodified=timemodified,
            cansubmit=lastattempt.get("cansubmit"),
            locked=lastattempt.get("locked"),
            extensionduedate=lastattempt.get("extensionduedate"),
            gradingstatus=lastattempt.get("gradingstatus"),
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


def _validate_file_paths(match: AssignmentSummary, file_paths: list[str]) -> list[Path]:
    """Check file_paths against this assignment's real, live-fetched
    submission-plugin config (issue #84) before anything is uploaded.
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
            "or omit file_paths."
        )
    if file_cfg.max_files is not None and len(file_paths) > file_cfg.max_files:
        raise PlatoMCPError(
            f"Assignment '{match.name}' allows at most {file_cfg.max_files} "
            f"file(s); {len(file_paths)} were given."
        )

    allowed_extensions = (
        {ext.lower() for ext in file_cfg.allowed_extensions}
        if file_cfg.allowed_extensions
        else DEFAULT_ALLOWED_UPLOAD_EXTENSIONS
    )

    resolved: list[Path] = []
    for raw_path in file_paths:
        path = Path(raw_path)
        if not path.is_file():
            raise PlatoMCPError(f"File not found: {raw_path!r}")
        if path.suffix.lower() not in allowed_extensions:
            raise PlatoMCPError(
                f"File extension {path.suffix!r} not allowed for this assignment "
                f"(allowed: {sorted(allowed_extensions)})."
            )
        size = path.stat().st_size
        if file_cfg.max_size_bytes is not None and size > file_cfg.max_size_bytes:
            raise PlatoMCPError(
                f"File {raw_path!r} is {size} bytes, exceeding this assignment's "
                f"max_size_bytes={file_cfg.max_size_bytes}."
            )
        resolved.append(path)
    return resolved


def submit_assignment_for(
    client: MoodleClient,
    course_id: int,
    assignment_id: int,
    text: str = "",
    file_paths: list[str] | None = None,
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

    Only the stdio transport (local file paths) is supported here -- under
    streamable-http (remote/Smithery) there is no local filesystem for
    file_paths to point at. That mirrors download_course_file's own
    stdio-vs-remote split (issue #55); the remote-transport upload story
    (e.g. accepting inline base64 content instead of a path) is deliberately
    deferred to a follow-up rather than guessed at here.

    dry_run=False is only allowed after a matching dry_run=True preview (same
    session, course_id, assignment_id, text, and file_paths) -- see
    write_tools.PreviewTracker (issue #37). This is enforced server-side, not
    just a docstring convention.
    """
    if not text and not file_paths:
        raise PlatoMCPError("Provide text and/or file_paths -- an empty submission is not valid.")

    assignments = list_assignments_for(client, [course_id])
    match = next((a for a in assignments if a.id == assignment_id), None)
    if match is None:
        raise ValueError(f"Assignment {assignment_id} not found in course {course_id}")

    resolved_paths: list[Path] = []
    if file_paths:
        resolved_paths = _validate_file_paths(match, file_paths)

    # Fail-open here, unlike the file-submission check above: text submission
    # predates issue #84 and has always been sent unconditionally, so only
    # block it on an *explicit* "disabled" from the API, not merely because
    # `configs` is empty/unknown (older/incomplete responses, or tests that
    # don't set it) -- preserves pre-#84 behavior for the common case.
    text_cfg = match.onlinetext_submission
    if text and text_cfg.known and not text_cfg.enabled:
        raise PlatoMCPError(
            f"Assignment '{match.name}' does not accept online text submissions "
            "(assignsubmission_onlinetext is disabled for it) -- use file_paths instead, "
            "or omit text."
        )

    action_params = {
        "course_id": course_id,
        "assignment_id": assignment_id,
        "text": text,
        "file_paths": sorted(file_paths) if file_paths else [],
    }
    preview = {
        **action_params,
        "assignment_name": match.name,
        "due_date": match.duedate.isoformat() if match.duedate else None,
        "cutoff_date": match.cutoffdate.isoformat() if match.cutoffdate else None,
        "file_sizes_bytes": {p.name: p.stat().st_size for p in resolved_paths},
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
    if resolved_paths:
        itemid = client.get_unused_draft_itemid()
        for path in resolved_paths:
            client.upload_file(itemid, path.name, path.read_bytes())
        plugindata["plugindata[files_filemanager]"] = itemid

    client.call("mod_assign_save_submission", assignmentid=assignment_id, **plugindata)
    return executed_result(preview, f"Submission for '{match.name}'")


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
                "works when this server is running locally (stdio) -- not supported over "
                "a remote/streamable-http connection. Rejected if this assignment doesn't "
                "accept file submissions, exceeds its max file count/size, or uses a "
                "disallowed extension -- check get_assignment_detail's file_submission "
                "(enabled/max_files/max_size_bytes/allowed_extensions) first."
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
        only call again with dry_run=False (same text/file_paths) after they
        explicitly confirm. Provide text, file_paths, or both -- whichever this
        assignment actually accepts (see get_assignment_detail).
        """
        return submit_assignment_for(
            get_client(ctx), course_id, assignment_id, text, file_paths, dry_run
        )
