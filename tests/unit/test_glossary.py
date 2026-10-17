"""Unit tests for issue #109: list_glossaries.

No real mod_glossary exists on this account -- the empty-list path is
verified live (see tests/integration/README.md).
"""

import pytest

from plato_mcp.tools.glossary import list_glossaries_for


@pytest.fixture
def mock_client(mocker):
    client = mocker.Mock()
    return client


def test_list_glossaries_for_empty_result_live_shape(mock_client):
    mock_client.call.return_value = {"glossaries": [], "warnings": []}

    result = list_glossaries_for(mock_client, [6253])

    assert result == []
    mock_client.call.assert_called_once_with(
        "mod_glossary_get_glossaries_by_courses", courseids=[6253]
    )
