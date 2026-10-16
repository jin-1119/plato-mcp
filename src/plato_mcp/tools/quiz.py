"""Tools: list_quizzes, get_quiz_attempts, get_quiz_best_grade (issue #85).

No course on this account has ever had a real quiz (confirmed via a live
scan of all 11 enrolled courses, 2026-10-17) -- `mod_quiz_get_quizzes_by_courses`
itself was verified live (returns `{"quizzes": [], "warnings": []}` against
a real course, the correct empty-list shape), but everything needing a
real quizid/attemptid (access info, attempts, grades, feedback, and
especially attempt-taking: start/answer/submit) has never been exercised
against a live response. `QuizSummary`/`QuizAttempt`/`QuizBestGrade` are
schema-only, read from Moodle 4.5 source, same caveat as `AssignmentSummary`
before a real assignment existed (see tests/integration/README.md).

Attempt-taking (mod_quiz_start_attempt/get_attempt_data/process_attempt/
save_attempt/get_attempt_review/get_attempt_summary/
get_combined_review_options) is explicitly deferred -- guessing at an
unverified multi-step write flow (answer formats per question type,
sequence-checking tokens, etc.) is a worse outcome than not building it.
Pick this up once a real quiz exists on the test account.
"""

from typing import Annotated

from mcp.server.mcpserver import Context
from pydantic import Field

from plato_mcp.context import get_client, get_userid
from plato_mcp.models import QuizAttempt, QuizBestGrade, QuizSummary
from plato_mcp.moodle_client import MoodleClient
from plato_mcp.tool_annotations import READ_ONLY_TOOL_ANNOTATIONS

_QUIZ_ID_FIELD = Field(description="Quiz id, e.g. from list_quizzes.")


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


def register(mcp) -> None:
    @mcp.tool(annotations=READ_ONLY_TOOL_ANNOTATIONS)
    async def list_quizzes(
        course_ids: Annotated[
            list[int], Field(description="One or more course ids to list quizzes for.")
        ],
        ctx: Context,
    ) -> list[QuizSummary]:
        """List quizzes across one or more courses. Quiz attempt-taking is
        not supported by this server -- this tool is read-only coverage
        only."""
        return list_quizzes_for(get_client(ctx), course_ids)

    @mcp.tool(annotations=READ_ONLY_TOOL_ANNOTATIONS)
    async def get_quiz_attempts(
        quiz_id: Annotated[int, _QUIZ_ID_FIELD],
        ctx: Context,
    ) -> list[QuizAttempt]:
        """Get this account's past attempts at one quiz. Starting a new
        attempt is not supported by this server."""
        return get_quiz_attempts_for(get_client(ctx), quiz_id)

    @mcp.tool(annotations=READ_ONLY_TOOL_ANNOTATIONS)
    async def get_quiz_best_grade(
        quiz_id: Annotated[int, _QUIZ_ID_FIELD],
        ctx: Context,
    ) -> QuizBestGrade:
        """Get this account's best grade on one quiz, if any attempt has
        been graded."""
        return get_quiz_best_grade_for(get_client(ctx), quiz_id)
