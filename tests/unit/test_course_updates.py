"""Unit tests for issue #102: get_course_updates_since.

Fixture shape is taken verbatim from a real live response against this
account's real assignment (course 5968, cmid 85415, after the #84 test
submission) -- see tests/integration/README.md.
"""

import pytest

from plato_mcp.tools.course_updates import get_course_updates_since_for


@pytest.fixture
def mock_client(mocker):
    client = mocker.Mock()
    return client


_REAL_UPDATES_RESPONSE = {
    "instances": [
        {
            "contextlevel": "module",
            "id": 85415,
            "updates": [
                {"name": "configuration", "timeupdated": 1790986952},
                {"name": "completion"},
                {"name": "gradeitems", "itemids": [56201]},
                {"name": "submissions", "itemids": [110787]},
                {"name": "grades", "itemids": [83479]},
            ],
        }
    ],
    "warnings": [
        {
            "item": "module",
            "itemid": 31637,
            "warningcode": "missingcallback",
            "message": "This module does not implement the check_updates_since callback: module",
        }
    ],
}


def test_get_course_updates_since_for_real_response_shape(mock_client):
    mock_client.call.return_value = _REAL_UPDATES_RESPONSE

    updates = get_course_updates_since_for(mock_client, course_id=5968, since=1790000000)

    assert len(updates) == 1
    assert updates[0].id == 85415
    names = {u.name for u in updates[0].updates}
    assert names == {"configuration", "completion", "gradeitems", "submissions", "grades"}
    submissions_update = next(u for u in updates[0].updates if u.name == "submissions")
    assert submissions_update.itemids == [110787]
    mock_client.call.assert_called_once_with(
        "core_course_get_updates_since", courseid=5968, since=1790000000
    )


def test_get_course_updates_since_for_ignores_missingcallback_warnings(mock_client):
    # Custom modules (ubfile/ubboard/vod) report missingcallback as a
    # warning, not an error -- confirmed this is NOT surfaced as an
    # exception, just silently absent from `instances`.
    mock_client.call.return_value = {
        "instances": [],
        "warnings": _REAL_UPDATES_RESPONSE["warnings"],
    }

    updates = get_course_updates_since_for(mock_client, course_id=6253, since=1790000000)

    assert updates == []
