"""Unit tests for issue #91: list_video_conferences.

No real BBB/Zoom module exists on this account -- the empty-list path is
verified live (see tests/integration/README.md).
"""

import pytest

from plato_mcp.tools.video_conference import list_video_conferences_for


@pytest.fixture
def mock_client(mocker):
    client = mocker.Mock()
    return client


def test_list_video_conferences_for_empty_result_live_shape(mock_client):
    mock_client.call.return_value = {"bigbluebuttonbns": [], "warnings": []}

    result = list_video_conferences_for(mock_client, [6253])

    assert result == []
    mock_client.call.assert_called_once_with(
        "mod_bigbluebuttonbn_get_bigbluebuttonbns_by_courses", courseids=[6253]
    )


def test_list_video_conferences_for_parses_documented_schema(mock_client):
    mock_client.call.return_value = {
        "bigbluebuttonbns": [{"id": 1, "course": 6253, "name": "Weekly Lecture", "intro": ""}]
    }

    result = list_video_conferences_for(mock_client, [6253])

    assert result[0].name == "Weekly Lecture"
