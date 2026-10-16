"""Unit tests for issue #85: list_quizzes, get_quiz_attempts, get_quiz_best_grade.

No real quiz exists on the test account -- list_quizzes_for's empty-list
path is verified live (see tests/integration/README.md); everything
needing a real quizid is schema-only, built from Moodle 4.5 source.
"""

import pytest

from plato_mcp.tools.quiz import (
    get_quiz_attempts_for,
    get_quiz_best_grade_for,
    list_quizzes_for,
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
