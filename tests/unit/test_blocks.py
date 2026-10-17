"""Unit tests for issue #116: get_recent_items, get_starred_courses.

Fixture shapes taken verbatim from real live responses -- see
tests/integration/README.md.
"""

import pytest

from plato_mcp.tools.blocks import get_recent_items_for, get_starred_courses_for


@pytest.fixture
def mock_client(mocker):
    client = mocker.Mock()
    return client


def test_get_recent_items_for_real_response_shape(mock_client):
    mock_client.call.return_value = [
        {
            "id": 2445854,
            "courseid": 5982,
            "cmid": 91538,
            "userid": 448520,
            "modname": "ubfile",
            "name": "Chapter 11 slides",
            "coursename": "인적자원관리",
            "timeaccess": 1792213482,
            "viewurl": "https://plato.pusan.ac.kr/mod/ubfile/view.php?id=91538",
            "courseviewurl": "https://plato.pusan.ac.kr/course/view.php?id=5982",
        }
    ]

    items = get_recent_items_for(mock_client)

    assert len(items) == 1
    assert items[0].name == "Chapter 11 slides"
    assert items[0].coursename == "인적자원관리"
    mock_client.call.assert_called_once_with("block_recentlyaccesseditems_get_recent_items")


def test_get_starred_courses_for_empty_result_live_shape(mock_client):
    # Real live response shape against the real account (issue #116) -- no starred courses.
    mock_client.call.return_value = []

    courses = get_starred_courses_for(mock_client)

    assert courses == []
    mock_client.call.assert_called_once_with("block_starredcourses_get_starred_courses")
