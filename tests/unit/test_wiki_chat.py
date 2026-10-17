"""Unit tests for issue #111: list_wikis, list_chats.

Neither mod_wiki nor mod_chat exists on this account -- the empty-list
paths are verified live (see tests/integration/README.md).
"""

import pytest

from plato_mcp.tools.wiki_chat import list_chats_for, list_wikis_for


@pytest.fixture
def mock_client(mocker):
    client = mocker.Mock()
    return client


def test_list_wikis_for_empty_result_live_shape(mock_client):
    mock_client.call.return_value = {"wikis": [], "warnings": []}

    result = list_wikis_for(mock_client, [6253])

    assert result == []
    mock_client.call.assert_called_once_with("mod_wiki_get_wikis_by_courses", courseids=[6253])


def test_list_chats_for_empty_result_live_shape(mock_client):
    mock_client.call.return_value = {"chats": [], "warnings": []}

    result = list_chats_for(mock_client, [6253])

    assert result == []
    mock_client.call.assert_called_once_with("mod_chat_get_chats_by_courses", courseids=[6253])
