"""Unit tests for issue #107: list_choices, list_surveys.

Neither mod_choice nor mod_survey exists on this account -- the
empty-list paths are verified live (see tests/integration/README.md).
"""

import pytest

from plato_mcp.tools.choice_survey import list_choices_for, list_surveys_for


@pytest.fixture
def mock_client(mocker):
    client = mocker.Mock()
    return client


def test_list_choices_for_empty_result_live_shape(mock_client):
    mock_client.call.return_value = {"choices": [], "warnings": []}

    result = list_choices_for(mock_client, [6253])

    assert result == []
    mock_client.call.assert_called_once_with("mod_choice_get_choices_by_courses", courseids=[6253])


def test_list_surveys_for_empty_result_live_shape(mock_client):
    mock_client.call.return_value = {"surveys": [], "warnings": []}

    result = list_surveys_for(mock_client, [6253])

    assert result == []
    mock_client.call.assert_called_once_with("mod_survey_get_surveys_by_courses", courseids=[6253])
