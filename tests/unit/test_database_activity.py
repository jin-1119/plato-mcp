"""Unit tests for issue #110: list_database_activities.

No real mod_data exists on this account -- the empty-list path is
verified live (see tests/integration/README.md).
"""

import pytest

from plato_mcp.tools.database_activity import list_database_activities_for


@pytest.fixture
def mock_client(mocker):
    client = mocker.Mock()
    return client


def test_list_database_activities_for_empty_result_live_shape(mock_client):
    mock_client.call.return_value = {"databases": [], "warnings": []}

    result = list_database_activities_for(mock_client, [6253])

    assert result == []
    mock_client.call.assert_called_once_with("mod_data_get_databases_by_courses", courseids=[6253])
