"""Unit tests for issue #106: list_feedbacks.

No real mod_feedback exists on this account -- the empty-list path is
verified live (see tests/integration/README.md).
"""

import pytest

from plato_mcp.tools.feedback import list_feedbacks_for


@pytest.fixture
def mock_client(mocker):
    client = mocker.Mock()
    return client


def test_list_feedbacks_for_empty_result_live_shape(mock_client):
    mock_client.call.return_value = {"feedbacks": [], "warnings": []}

    result = list_feedbacks_for(mock_client, [6253])

    assert result == []
    mock_client.call.assert_called_once_with(
        "mod_feedback_get_feedbacks_by_courses", courseids=[6253]
    )


def test_list_feedbacks_for_parses_documented_schema(mock_client):
    mock_client.call.return_value = {
        "feedbacks": [{"id": 1, "course": 6253, "name": "Course Survey", "anonymous": 1}]
    }

    result = list_feedbacks_for(mock_client, [6253])

    assert result[0].name == "Course Survey"
