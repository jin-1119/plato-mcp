"""Unit tests for issue #93: list_lessons.

No real mod_lesson exists on this account -- the empty-list path is
verified live (see tests/integration/README.md).
"""

import pytest

from plato_mcp.tools.lesson import list_lessons_for


@pytest.fixture
def mock_client(mocker):
    client = mocker.Mock()
    return client


def test_list_lessons_for_empty_result_live_shape(mock_client):
    mock_client.call.return_value = {"lessons": [], "warnings": []}

    result = list_lessons_for(mock_client, [6253])

    assert result == []
    mock_client.call.assert_called_once_with("mod_lesson_get_lessons_by_courses", courseids=[6253])


def test_list_lessons_for_parses_documented_schema(mock_client):
    mock_client.call.return_value = {
        "lessons": [{"id": 1, "course": 6253, "name": "Chapter 1 Lesson", "timelimit": 0}]
    }

    result = list_lessons_for(mock_client, [6253])

    assert result[0].name == "Chapter 1 Lesson"
