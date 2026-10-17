"""Tools: list_quizzes, get_quiz_attempts, get_quiz_best_grade, and the
full attempt-taking flow (issue #85).

No course on this account has ever had a real quiz (confirmed via a live
scan of all 11 enrolled courses, 2026-10-17). `mod_quiz_get_quizzes_by_courses`
itself was verified live (returns `{"quizzes": [], "warnings": []}` against
a real course, the correct empty-list shape).

**Attempt-taking was originally deferred** (no real quiz to verify an
unverified multi-step write flow against), but reopened by explicit user
decision: even though nobody in this account's *current* courses uses
quizzes, other PNU professors plausibly do in other courses/semesters, so
having the flow ready is worth it rather than waiting indefinitely for a
real instance that may never appear on this specific account.

**Every function below is schema-only and UNVERIFIED against a live
response** -- built from Moodle 4.5's mod_quiz external API source, same
caveat pattern this repo already used for `AssignmentSummary` before a
real assignment existed. The central risk, inherited rather than solved:
`mod_quiz_get_attempt_data` returns each question as Moodle's own
server-rendered HTML question form, not a clean structured "question +
answer options" shape -- an AI caller has to parse that HTML to figure
out the actual form-field names before it can build a `responses` dict
for `process_quiz_attempt`/`save_quiz_attempt_responses`. Whether that
parsing approach actually works has never been tested against a real
quiz. The moment a real quiz appears anywhere reachable from this
account, re-verify this entire flow end to end before trusting it for
something that matters (a graded attempt).

Attempt-affecting writes (`start_quiz_attempt`, `save_quiz_attempt_responses`,
`process_quiz_attempt`) follow the dry_run preview/confirm pattern --
starting an attempt consumes one of the quiz's limited attempts, and
`process_quiz_attempt` with `finish_attempt=True` is the final,
irreversible submission.
"""

from typing import Annotated

from mcp.server.mcpserver import Context
from pydantic import Field

from plato_mcp.context import get_client, get_userid
from plato_mcp.models import (
    QuizAccessInformation,
    QuizAttempt,
    QuizAttemptData,
    QuizAttemptHandle,
    QuizAttemptReview,
    QuizAttemptSummary,
    QuizBestGrade,
    QuizFeedbackForGrade,
    QuizReviewOptions,
    QuizSummary,
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

ACTION_START_QUIZ_ATTEMPT = "start_quiz_attempt"
ACTION_SAVE_QUIZ_ATTEMPT = "save_quiz_attempt_responses"
ACTION_PROCESS_QUIZ_ATTEMPT = "process_quiz_attempt"

_QUIZ_ID_FIELD = Field(description="Quiz id, e.g. from list_quizzes.")
_ATTEMPT_ID_FIELD = Field(description="Attempt id, e.g. from start_quiz_attempt.")


def list_quizzes_for(client: MoodleClient, course_ids: list[int]) -> list[QuizSummary]:
    result = client.call("mod_quiz_get_quizzes_by_courses", courseids=course_ids)
    return [QuizSummary(**q) for q in result.get("quizzes", [])]


def get_quiz_attempts_for(client: MoodleClient, quiz_id: int) -> list[QuizAttempt]:
    userid = get_userid(client)
    result = client.call("mod_quiz_get_user_attempts", quizid=quiz_id, userid=userid)
    return [QuizAttempt(**a) for a in result.get("attempts", [])]


def get_quiz_best_grade_for(client: MoodleClient, quiz_id: int) -> QuizBestGrade:
    userid = get_userid(client)
    result = client.call("mod_quiz_get_user_best_grade", quizid=quiz_id, userid=userid)
    return QuizBestGrade(**result)


def get_quiz_access_information_for(client: MoodleClient, quiz_id: int) -> QuizAccessInformation:
    result = client.call("mod_quiz_get_quiz_access_information", quizid=quiz_id)
    return QuizAccessInformation(**result)


def get_quiz_required_qtypes_for(client: MoodleClient, quiz_id: int) -> list[str]:
    result = client.call("mod_quiz_get_quiz_required_qtypes", quizid=quiz_id)
    return result.get("questiontypes", [])


def get_quiz_feedback_for_grade_for(
    client: MoodleClient, quiz_id: int, grade: float
) -> QuizFeedbackForGrade:
    result = client.call("mod_quiz_get_quiz_feedback_for_grade", quizid=quiz_id, grade=grade)
    return QuizFeedbackForGrade(**result)


def get_quiz_combined_review_options_for(
    client: MoodleClient, quiz_id: int, attempt_id: int | None = None
) -> QuizReviewOptions:
    params = {"quizid": quiz_id}
    if attempt_id is not None:
        params["attemptid"] = attempt_id
    result = client.call("mod_quiz_get_combined_review_options", **params)
    flat = {o["name"]: o["value"] for o in result.get("alloptions", [])}
    return QuizReviewOptions(
        marks=bool(int(flat.get("marks", 0))),
        feedback=bool(int(flat.get("feedback", 0))),
        generalfeedback=bool(int(flat.get("generalfeedback", 0))),
        rightanswer=bool(int(flat.get("rightanswer", 0))),
        overallfeedback=bool(int(flat.get("overallfeedback", 0))),
    )


def start_quiz_attempt_for(client: MoodleClient, quiz_id: int, dry_run: bool = True) -> WriteResult:
    """Start a new attempt at a quiz. IRREVERSIBLE once dry_run=False --
    this consumes one of the quiz's limited attempts (if it has a max
    attempts setting). UNVERIFIED (see module docstring)."""
    action_params = {"quiz_id": quiz_id}
    preview = {**action_params}

    if dry_run:
        default_preview_tracker.record_preview(
            client.session_key, ACTION_START_QUIZ_ATTEMPT, action_params
        )
        return preview_result(preview, f"New attempt at quiz #{quiz_id}")

    default_preview_tracker.require_previewed(
        client.session_key, ACTION_START_QUIZ_ATTEMPT, action_params
    )
    result = client.call("mod_quiz_start_attempt", quizid=quiz_id)
    attempt = QuizAttemptHandle(**result["attempt"])
    preview["attempt_id"] = attempt.id
    return executed_result(preview, f"New attempt at quiz #{quiz_id}")


def get_quiz_attempt_data_for(
    client: MoodleClient, attempt_id: int, page: int = 0
) -> QuizAttemptData:
    result = client.call("mod_quiz_get_attempt_data", attemptid=attempt_id, page=page)
    return QuizAttemptData(**result)


def get_quiz_attempt_summary_for(client: MoodleClient, attempt_id: int) -> QuizAttemptSummary:
    result = client.call("mod_quiz_get_attempt_summary", attemptid=attempt_id)
    return QuizAttemptSummary(**result)


def get_quiz_attempt_review_for(
    client: MoodleClient, attempt_id: int, page: int = -1
) -> QuizAttemptReview:
    result = client.call("mod_quiz_get_attempt_review", attemptid=attempt_id, page=page)
    return QuizAttemptReview(**result)


def save_quiz_attempt_responses_for(
    client: MoodleClient,
    attempt_id: int,
    responses: dict[str, str],
    page: int = 0,
    dry_run: bool = True,
) -> WriteResult:
    """Save in-progress answers for a quiz attempt WITHOUT finishing it
    (can still be changed later). `responses` is a flat dict of Moodle
    question-form field name -> value, parsed by the caller from
    get_quiz_attempt_data's returned HTML. UNVERIFIED (see module docstring)."""
    action_params = {"attempt_id": attempt_id, "responses": responses, "page": page}
    preview = {**action_params}

    if dry_run:
        default_preview_tracker.record_preview(
            client.session_key, ACTION_SAVE_QUIZ_ATTEMPT, action_params
        )
        return preview_result(preview, f"Saved responses for attempt #{attempt_id}")

    default_preview_tracker.require_previewed(
        client.session_key, ACTION_SAVE_QUIZ_ATTEMPT, action_params
    )
    data = [{"name": k, "value": v} for k, v in responses.items()]
    params: dict = {"attemptid": attempt_id, "page": page}
    for i, item in enumerate(data):
        params[f"data[{i}][name]"] = item["name"]
        params[f"data[{i}][value]"] = item["value"]
    client.call("mod_quiz_save_attempt", **params)
    return executed_result(preview, f"Saved responses for attempt #{attempt_id}")


def process_quiz_attempt_for(
    client: MoodleClient,
    attempt_id: int,
    responses: dict[str, str],
    finish_attempt: bool = False,
    dry_run: bool = True,
) -> WriteResult:
    """Submit answers for a quiz attempt, optionally finishing it.
    IRREVERSIBLE once dry_run=False AND finish_attempt=True -- that locks
    in the final submission. `responses` is a flat dict of Moodle
    question-form field name -> value, parsed by the caller from
    get_quiz_attempt_data's returned HTML. UNVERIFIED (see module docstring)."""
    action_params = {
        "attempt_id": attempt_id,
        "responses": responses,
        "finish_attempt": finish_attempt,
    }
    preview = {**action_params}

    if dry_run:
        default_preview_tracker.record_preview(
            client.session_key, ACTION_PROCESS_QUIZ_ATTEMPT, action_params
        )
        return preview_result(preview, f"Processed responses for attempt #{attempt_id}")

    default_preview_tracker.require_previewed(
        client.session_key, ACTION_PROCESS_QUIZ_ATTEMPT, action_params
    )
    data = [{"name": k, "value": v} for k, v in responses.items()]
    params: dict = {"attemptid": attempt_id, "finishattempt": int(finish_attempt)}
    for i, item in enumerate(data):
        params[f"data[{i}][name]"] = item["name"]
        params[f"data[{i}][value]"] = item["value"]
    client.call("mod_quiz_process_attempt", **params)
    return executed_result(preview, f"Processed responses for attempt #{attempt_id}")


def register(mcp) -> None:
    @mcp.tool(annotations=READ_ONLY_TOOL_ANNOTATIONS)
    async def list_quizzes(
        course_ids: Annotated[
            list[int], Field(description="One or more course ids to list quizzes for.")
        ],
        ctx: Context,
    ) -> list[QuizSummary]:
        """List quizzes across one or more courses."""
        return list_quizzes_for(get_client(ctx), course_ids)

    @mcp.tool(annotations=READ_ONLY_TOOL_ANNOTATIONS)
    async def get_quiz_attempts(
        quiz_id: Annotated[int, _QUIZ_ID_FIELD],
        ctx: Context,
    ) -> list[QuizAttempt]:
        """Get this account's past attempts at one quiz."""
        return get_quiz_attempts_for(get_client(ctx), quiz_id)

    @mcp.tool(annotations=READ_ONLY_TOOL_ANNOTATIONS)
    async def get_quiz_best_grade(
        quiz_id: Annotated[int, _QUIZ_ID_FIELD],
        ctx: Context,
    ) -> QuizBestGrade:
        """Get this account's best grade on one quiz, if any attempt has
        been graded."""
        return get_quiz_best_grade_for(get_client(ctx), quiz_id)

    @mcp.tool(annotations=READ_ONLY_TOOL_ANNOTATIONS)
    async def get_quiz_access_information(
        quiz_id: Annotated[int, _QUIZ_ID_FIELD],
        ctx: Context,
    ) -> QuizAccessInformation:
        """Check whether this account can currently attempt a quiz, and
        why not if blocked (e.g. time window, password, previous
        attempts exhausted). UNVERIFIED against a real quiz -- call this
        before start_quiz_attempt and sanity-check the result."""
        return get_quiz_access_information_for(get_client(ctx), quiz_id)

    @mcp.tool(annotations=READ_ONLY_TOOL_ANNOTATIONS)
    async def get_quiz_required_qtypes(
        quiz_id: Annotated[int, _QUIZ_ID_FIELD],
        ctx: Context,
    ) -> list[str]:
        """List the question types used in a quiz (e.g. 'multichoice',
        'truefalse', 'essay') -- useful to know what kind of answers
        to expect before starting an attempt."""
        return get_quiz_required_qtypes_for(get_client(ctx), quiz_id)

    @mcp.tool(annotations=READ_ONLY_TOOL_ANNOTATIONS)
    async def get_quiz_feedback_for_grade(
        quiz_id: Annotated[int, _QUIZ_ID_FIELD],
        grade: Annotated[float, Field(description="A grade value to look up feedback text for.")],
        ctx: Context,
    ) -> QuizFeedbackForGrade:
        """Get the grade-boundary feedback text configured for a quiz at
        a given grade (e.g. 'You passed!' / 'Please review chapter 3')."""
        return get_quiz_feedback_for_grade_for(get_client(ctx), quiz_id, grade)

    @mcp.tool(annotations=READ_ONLY_TOOL_ANNOTATIONS)
    async def get_quiz_combined_review_options(
        quiz_id: Annotated[int, _QUIZ_ID_FIELD],
        ctx: Context,
        attempt_id: Annotated[
            int | None, Field(description="Optional: a specific attempt id to check options for.")
        ] = None,
    ) -> QuizReviewOptions:
        """Check which review details (marks, feedback, right answers) this
        account is allowed to see for a quiz's attempts."""
        return get_quiz_combined_review_options_for(get_client(ctx), quiz_id, attempt_id)

    @mcp.tool(annotations=WRITE_TOOL_ANNOTATIONS)
    async def start_quiz_attempt(
        quiz_id: Annotated[int, _QUIZ_ID_FIELD],
        ctx: Context,
        dry_run: Annotated[
            bool,
            Field(
                description="If True (default), only preview starting the attempt. Call "
                "again with dry_run=False (same parameters) to actually start it."
            ),
        ] = True,
    ) -> WriteResult:
        """Start a new attempt at a quiz. IRREVERSIBLE once dry_run=False --
        consumes one of the quiz's limited attempts. UNVERIFIED against a
        real quiz -- call get_quiz_access_information first and check
        canattempt/preventaccessreasons.

        Call with dry_run=True (default) first, show the preview to the
        user, and only call again with dry_run=False after they explicitly
        confirm.
        """
        return start_quiz_attempt_for(get_client(ctx), quiz_id, dry_run)

    @mcp.tool(annotations=READ_ONLY_TOOL_ANNOTATIONS)
    async def get_quiz_attempt_data(
        attempt_id: Annotated[int, _ATTEMPT_ID_FIELD],
        ctx: Context,
        page: Annotated[int, Field(description="Quiz page number, 0-indexed.")] = 0,
    ) -> QuizAttemptData:
        """Get the questions for one page of an in-progress quiz attempt.
        Each question's `html` is Moodle's own rendered question form --
        parse it for the actual answer-field names before calling
        save_quiz_attempt_responses/process_quiz_attempt. UNVERIFIED
        against a real quiz."""
        return get_quiz_attempt_data_for(get_client(ctx), attempt_id, page)

    @mcp.tool(annotations=READ_ONLY_TOOL_ANNOTATIONS)
    async def get_quiz_attempt_summary(
        attempt_id: Annotated[int, _ATTEMPT_ID_FIELD],
        ctx: Context,
    ) -> QuizAttemptSummary:
        """Get a summary of all questions in an attempt (answered/
        unanswered), across all pages. UNVERIFIED against a real quiz."""
        return get_quiz_attempt_summary_for(get_client(ctx), attempt_id)

    @mcp.tool(annotations=READ_ONLY_TOOL_ANNOTATIONS)
    async def get_quiz_attempt_review(
        attempt_id: Annotated[int, _ATTEMPT_ID_FIELD],
        ctx: Context,
        page: Annotated[
            int, Field(description="Page number, 0-indexed, or -1 for all pages.")
        ] = -1,
    ) -> QuizAttemptReview:
        """Get the grade and per-question review for a finished quiz
        attempt. UNVERIFIED against a real quiz."""
        return get_quiz_attempt_review_for(get_client(ctx), attempt_id, page)

    @mcp.tool(annotations=WRITE_TOOL_ANNOTATIONS)
    async def save_quiz_attempt_responses(
        attempt_id: Annotated[int, _ATTEMPT_ID_FIELD],
        responses: Annotated[
            dict[str, str],
            Field(
                description="Moodle question-form field name -> answer value, parsed from "
                "get_quiz_attempt_data's returned HTML."
            ),
        ],
        ctx: Context,
        page: Annotated[int, Field(description="Quiz page number these responses are for.")] = 0,
        dry_run: Annotated[
            bool,
            Field(
                description="If True (default), only preview saving without doing it. Call "
                "again with dry_run=False (same parameters) to actually save it."
            ),
        ] = True,
    ) -> WriteResult:
        """Save in-progress answers WITHOUT finishing the attempt -- can
        still be changed later. UNVERIFIED against a real quiz.

        Call with dry_run=True (default) first, show the preview to the
        user, and only call again with dry_run=False after they explicitly
        confirm.
        """
        return save_quiz_attempt_responses_for(
            get_client(ctx), attempt_id, responses, page, dry_run
        )

    @mcp.tool(annotations=WRITE_TOOL_ANNOTATIONS)
    async def process_quiz_attempt(
        attempt_id: Annotated[int, _ATTEMPT_ID_FIELD],
        responses: Annotated[
            dict[str, str],
            Field(
                description="Moodle question-form field name -> answer value, parsed from "
                "get_quiz_attempt_data's returned HTML."
            ),
        ],
        ctx: Context,
        finish_attempt: Annotated[
            bool,
            Field(
                description="If True, this is the FINAL submission -- the attempt is locked "
                "and graded. If False, this just records answers for the current page."
            ),
        ] = False,
        dry_run: Annotated[
            bool,
            Field(
                description="If True (default), only preview without doing it. Call again "
                "with dry_run=False (same parameters) to actually submit it."
            ),
        ] = True,
    ) -> WriteResult:
        """Submit answers for a quiz attempt. IRREVERSIBLE once
        dry_run=False AND finish_attempt=True -- that is the final,
        graded submission and cannot be undone. UNVERIFIED against a
        real quiz.

        Call with dry_run=True (default) first, show the preview to the
        user -- especially before finish_attempt=True -- and only call
        again with dry_run=False after they explicitly confirm.
        """
        return process_quiz_attempt_for(
            get_client(ctx), attempt_id, responses, finish_attempt, dry_run
        )
