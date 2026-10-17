"""Unit tests for issue #94: list_workshops.

No real mod_workshop exists on this account -- the empty-list path is
verified live (see tests/integration/README.md).
"""

import pytest

from plato_mcp.tools.workshop import list_workshops_for


@pytest.fixture
def mock_client(mocker):
    client = mocker.Mock()
    return client


def test_list_workshops_for_empty_result_live_shape(mock_client):
    mock_client.call.return_value = {"workshops": [], "warnings": []}

    result = list_workshops_for(mock_client, [6253])

    assert result == []
    mock_client.call.assert_called_once_with(
        "mod_workshop_get_workshops_by_courses", courseids=[6253]
    )


def test_list_workshops_for_parses_documented_schema(mock_client):
    mock_client.call.return_value = {
        "workshops": [{"id": 1, "course": 6253, "name": "Peer Review 1", "phase": 2}]
    }

    result = list_workshops_for(mock_client, [6253])

    assert result[0].name == "Peer Review 1"
