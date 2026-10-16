"""Unit tests for issue #86: list_forums, get_forum_discussions, get_discussion_posts,
add_discussion, add_discussion_post.

No real mod_forum exists on this account -- list_forums_for's empty-list
path is verified live (see tests/integration/README.md); everything else
is schema-only.
"""

import pytest

from plato_mcp.tools.forum import (
    add_discussion_for,
    add_discussion_post_for,
    get_discussion_posts_for,
    get_forum_discussions_for,
    list_forums_for,
)


@pytest.fixture
def mock_client(mocker):
    client = mocker.Mock()
    return client


def test_list_forums_for_empty_result_live_shape(mock_client):
    # Real live response shape against a real course with no forum (issue #86).
    mock_client.call.return_value = []

    forums = list_forums_for(mock_client, [6253])

    assert forums == []
    mock_client.call.assert_called_once_with("mod_forum_get_forums_by_courses", courseids=[6253])


def test_list_forums_for_parses_documented_schema(mock_client):
    mock_client.call.return_value = [
        {"id": 1, "course": 6253, "name": "General", "type": "general", "numdiscussions": 3}
    ]
    forums = list_forums_for(mock_client, [6253])
    assert forums[0].name == "General"
    assert forums[0].numdiscussions == 3


def test_get_forum_discussions_for_parses_documented_schema(mock_client):
    mock_client.call.return_value = {
        "discussions": [
            {
                "id": 10,
                "name": "Welcome thread",
                "userfullname": "강사",
                "created": 1790000000,
                "numreplies": 2,
                "pinned": True,
                "locked": False,
            }
        ]
    }
    discussions = get_forum_discussions_for(mock_client, forum_id=1)
    assert discussions[0].name == "Welcome thread"
    assert discussions[0].pinned is True


def test_get_discussion_posts_for_parses_documented_schema(mock_client):
    mock_client.call.return_value = {
        "posts": [
            {"id": 100, "subject": "Re: Welcome", "message": "hi", "userfullname": "학생A"}
        ]
    }
    posts = get_discussion_posts_for(mock_client, discussion_id=10)
    assert posts[0].message == "hi"


def test_add_discussion_for_dry_run_does_not_call(mock_client):
    result = add_discussion_for(mock_client, forum_id=1, subject="Q", message="body")
    assert result.dry_run is True
    mock_client.call.assert_not_called()


def test_add_discussion_for_real_run_requires_preview_then_calls(mock_client):
    mock_client.call.return_value = []
    add_discussion_for(mock_client, forum_id=1, subject="Q", message="body")
    result = add_discussion_for(
        mock_client, forum_id=1, subject="Q", message="body", dry_run=False
    )
    assert result.executed is True
    mock_client.call.assert_called_once_with(
        "mod_forum_add_discussion", forumid=1, subject="Q", message="body"
    )


def test_add_discussion_post_for_dry_run_does_not_call(mock_client):
    result = add_discussion_post_for(mock_client, discussion_id=10, message="reply")
    assert result.dry_run is True
    mock_client.call.assert_not_called()


def test_add_discussion_post_for_real_run_requires_preview_then_calls(mock_client):
    mock_client.call.return_value = []
    add_discussion_post_for(mock_client, discussion_id=10, message="reply")
    result = add_discussion_post_for(
        mock_client, discussion_id=10, message="reply", dry_run=False
    )
    assert result.executed is True
    mock_client.call.assert_called_once_with(
        "mod_forum_add_discussion_post", discussionid=10, message="reply"
    )


def test_add_discussion_post_without_preview_raises(mock_client):
    from plato_mcp.errors import WriteConfirmationError

    with pytest.raises(WriteConfirmationError):
        add_discussion_post_for(mock_client, discussion_id=99, message="x", dry_run=False)
