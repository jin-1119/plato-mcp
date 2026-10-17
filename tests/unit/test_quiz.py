"""Unit tests for issue #85: list_quizzes, get_quiz_attempts, get_quiz_best_grade,
and the attempt-taking flow (reopened per explicit user decision).

No real quiz exists on the test account -- list_quizzes_for's empty-list
path is verified live (see tests/integration/README.md); everything
needing a real quizid/attemptid is schema-only, built from Moodle 4.5
source, UNVERIFIED against a live response.
"""

import pytest

from plato_mcp.errors import WriteConfirmationError
from plato_mcp.tools.quiz import (
    get_quiz_access_information_for,
    get_quiz_attempt_data_for,
    get_quiz_attempt_review_for,
    get_quiz_attempt_summary_for,
    get_quiz_attempts_for,
    get_quiz_best_grade_for,
    get_quiz_combined_review_options_for,
    get_quiz_feedback_for_grade_for,
    get_quiz_required_qtypes_for,
    list_quizzes_for,
    process_quiz_attempt_for,
    save_quiz_attempt_responses_for,
    start_quiz_attempt_for,
)


@pytest.fixture
def mock_client(mocker):
    client = mocker.Mock()
    return client


def test_list_quizzes_for_empty_result_live_shape(mock_client):
    # Real live response shape against a real course with no quiz (issue #85).
    mock_client.call.return_value = {"quizzes": [], "warnings": []}

    quizzes = list_quizzes_for(mock_client, [6253])

    assert quizzes == []
    mock_client.call.assert_called_once_with("mod_quiz_get_quizzes_by_courses", courseids=[6253])


def test_list_quizzes_for_parses_documented_schema(mock_client):
    mock_client.call.return_value = {
        "quizzes": [
            {
                "id": 1,
                "course": 6253,
                "name": "Midterm Quiz",
                "intro": "<p>Covers chapters 1-3</p>",
                "timeopen": 1790000000,
                "timeclose": 1790100000,
                "timelimit": 3600,
                "attempts": 2,
                "grademethod": 1,
                "sumgrades": 20.0,
                "grade": 100.0,
            }
        ]
    }

    quizzes = list_quizzes_for(mock_client, [6253])

    assert len(quizzes) == 1
    assert quizzes[0].name == "Midterm Quiz"
    assert quizzes[0].attempts == 2
    assert quizzes[0].timeopen is not None


def test_get_quiz_attempts_for_parses_documented_schema(mock_client):
    def fake_call(fn, **kw):
        if fn == "core_webservice_get_site_info":
            return {"userid": 448520}
        if fn == "mod_quiz_get_user_attempts":
            assert kw == {"quizid": 1, "userid": 448520}
            return {
                "attempts": [
                    {
                        "id": 100,
                        "quiz": 1,
                        "attempt": 1,
                        "state": "finished",
                        "timestart": 1790000000,
                        "timefinish": 1790003600,
                        "sumgrades": 18.0,
                    }
                ]
            }
        raise AssertionError(fn)

    mock_client.call.side_effect = fake_call

    attempts = get_quiz_attempts_for(mock_client, quiz_id=1)

    assert len(attempts) == 1
    assert attempts[0].state == "finished"
    assert attempts[0].sumgrades == 18.0


def test_get_quiz_best_grade_for_parses_documented_schema(mock_client):
    def fake_call(fn, **kw):
        if fn == "core_webservice_get_site_info":
            return {"userid": 448520}
        if fn == "mod_quiz_get_user_best_grade":
            return {"hasgrade": True, "grade": 18.0, "gradetopass": 12.0}
        raise AssertionError(fn)

    mock_client.call.side_effect = fake_call

    result = get_quiz_best_grade_for(mock_client, quiz_id=1)

    assert result.hasgrade is True
    assert result.grade == 18.0


def test_get_quiz_access_information_for_parses_documented_schema(mock_client):
    mock_client.call.return_value = {
        "canattempt": True,
        "canmanage": False,
        "canpreview": False,
        "canreviewmyattempts": True,
        "canviewreports": False,
        "accessrules": [],
        "preventaccessreasons": [],
    }

    result = get_quiz_access_information_for(mock_client, quiz_id=1)

    assert result.canattempt is True
    assert result.preventaccessreasons == []


def test_get_quiz_required_qtypes_for_parses_documented_schema(mock_client):
    mock_client.call.return_value = {"questiontypes": ["multichoice", "truefalse"]}

    result = get_quiz_required_qtypes_for(mock_client, quiz_id=1)

    assert result == ["multichoice", "truefalse"]


def test_get_quiz_feedback_for_grade_for_parses_documented_schema(mock_client):
    mock_client.call.return_value = {
        "feedbacktext": "<p>Great job!</p>",
        "feedbacktextformat": 1,
    }

    result = get_quiz_feedback_for_grade_for(mock_client, quiz_id=1, grade=90.0)

    assert result.feedbacktext == "<p>Great job!</p>"
    mock_client.call.assert_called_once_with(
        "mod_quiz_get_quiz_feedback_for_grade", quizid=1, grade=90.0
    )


def test_get_quiz_combined_review_options_for_flattens_alloptions(mock_client):
    mock_client.call.return_value = {
        "someoptions": [],
        "alloptions": [
            {"name": "marks", "value": "1"},
            {"name": "feedback", "value": "1"},
            {"name": "generalfeedback", "value": "0"},
            {"name": "rightanswer", "value": "0"},
            {"name": "overallfeedback", "value": "1"},
        ],
    }

    result = get_quiz_combined_review_options_for(mock_client, quiz_id=1)

    assert result.marks is True
    assert result.generalfeedback is False
    assert result.overallfeedback is True


def test_start_quiz_attempt_for_dry_run_does_not_call(mock_client):
    result = start_quiz_attempt_for(mock_client, quiz_id=1)
    assert result.dry_run is True
    mock_client.call.assert_not_called()


def test_start_quiz_attempt_for_real_run_requires_preview_then_calls(mock_client):
    mock_client.call.return_value = {
        "attempt": {"id": 500, "quiz": 1, "attempt": 1, "state": "inprogress"}
    }

    start_quiz_attempt_for(mock_client, quiz_id=1)
    result = start_quiz_attempt_for(mock_client, quiz_id=1, dry_run=False)

    assert result.executed is True
    assert result.preview["attempt_id"] == 500
    mock_client.call.assert_called_once_with("mod_quiz_start_attempt", quizid=1)


def test_start_quiz_attempt_for_without_preview_raises(mock_client):
    with pytest.raises(WriteConfirmationError):
        start_quiz_attempt_for(mock_client, quiz_id=1, dry_run=False)


def test_get_quiz_attempt_data_for_parses_documented_schema(mock_client):
    mock_client.call.return_value = {
        "questions": [
            {
                "slot": 1,
                "type": "multichoice",
                "page": 0,
                "html": "<div>...</div>",
                "sequencecheck": 1,
            }
        ],
        "nextpage": -1,
    }

    result = get_quiz_attempt_data_for(mock_client, attempt_id=500)

    assert result.questions[0].type == "multichoice"
    mock_client.call.assert_called_once_with(
        "mod_quiz_get_attempt_data", attemptid=500, page=0
    )


def test_get_quiz_attempt_summary_for_parses_documented_schema(mock_client):
    mock_client.call.return_value = {"questions": [], "totalunanswered": 0}

    result = get_quiz_attempt_summary_for(mock_client, attempt_id=500)

    assert result.totalunanswered == 0


def test_get_quiz_attempt_review_for_parses_documented_schema(mock_client):
    mock_client.call.return_value = {"grade": "18.00", "questions": []}

    result = get_quiz_attempt_review_for(mock_client, attempt_id=500)

    assert result.grade == "18.00"
    mock_client.call.assert_called_once_with(
        "mod_quiz_get_attempt_review", attemptid=500, page=-1
    )


def test_save_quiz_attempt_responses_for_dry_run_does_not_call(mock_client):
    result = save_quiz_attempt_responses_for(mock_client, attempt_id=500, responses={"q1": "A"})
    assert result.dry_run is True
    mock_client.call.assert_not_called()


def test_save_quiz_attempt_responses_for_real_run_builds_data_array(mock_client):
    mock_client.call.return_value = {"status": True}

    save_quiz_attempt_responses_for(mock_client, attempt_id=500, responses={"q1": "A"})
    result = save_quiz_attempt_responses_for(
        mock_client, attempt_id=500, responses={"q1": "A"}, dry_run=False
    )

    assert result.executed is True
    mock_client.call.assert_called_once_with(
        "mod_quiz_save_attempt",
        attemptid=500,
        page=0,
        **{"data[0][name]": "q1", "data[0][value]": "A"},
    )


def test_process_quiz_attempt_for_dry_run_does_not_call(mock_client):
    result = process_quiz_attempt_for(mock_client, attempt_id=500, responses={"q1": "A"})
    assert result.dry_run is True
    mock_client.call.assert_not_called()


def test_process_quiz_attempt_for_real_run_with_finish_attempt(mock_client):
    mock_client.call.return_value = {"state": "finished"}

    process_quiz_attempt_for(
        mock_client, attempt_id=500, responses={"q1": "A"}, finish_attempt=True
    )
    result = process_quiz_attempt_for(
        mock_client, attempt_id=500, responses={"q1": "A"}, finish_attempt=True, dry_run=False
    )

    assert result.executed is True
    mock_client.call.assert_called_once_with(
        "mod_quiz_process_attempt",
        attemptid=500,
        finishattempt=1,
        **{"data[0][name]": "q1", "data[0][value]": "A"},
    )


def test_process_quiz_attempt_for_without_preview_raises(mock_client):
    with pytest.raises(WriteConfirmationError):
        process_quiz_attempt_for(mock_client, attempt_id=500, responses={"q1": "A"}, dry_run=False)
