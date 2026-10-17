"""Unit tests for issue #108: list_scorms, list_h5p_activities.

Neither mod_scorm nor mod_h5pactivity exists on this account -- the
empty-list paths are verified live (see tests/integration/README.md).
"""

import pytest

from plato_mcp.tools.scorm_h5p import list_h5p_activities_for, list_scorms_for


@pytest.fixture
def mock_client(mocker):
    client = mocker.Mock()
    return client


def test_list_scorms_for_empty_result_live_shape(mock_client):
    mock_client.call.return_value = {
        "scorms": [],
        "options": [{"name": "scormstandard", "value": "0"}],
        "warnings": [],
    }

    result = list_scorms_for(mock_client, [6253])

    assert result == []
    mock_client.call.assert_called_once_with("mod_scorm_get_scorms_by_courses", courseids=[6253])


def test_list_h5p_activities_for_empty_result_live_shape(mock_client):
    mock_client.call.return_value = {
        "h5pactivities": [],
        "h5pglobalsettings": {"enablesavestate": True, "savestatefreq": 60},
        "warnings": [],
    }

    result = list_h5p_activities_for(mock_client, [6253])

    assert result == []
    mock_client.call.assert_called_once_with(
        "mod_h5pactivity_get_h5pactivities_by_courses", courseids=[6253]
    )
