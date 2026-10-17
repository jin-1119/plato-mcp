"""Unit tests for issue #97: get_my_course_groups, get_enrolled_users.

Fixture shapes taken verbatim from real live responses -- see
tests/integration/README.md.
"""

import pytest

from plato_mcp.tools.groups import get_enrolled_users_for, get_my_course_groups_for


@pytest.fixture
def mock_client(mocker):
    client = mocker.Mock()
    return client


def test_get_my_course_groups_for_empty_result_live_shape(mock_client):
    def fake_call(fn, **kw):
        if fn == "core_webservice_get_site_info":
            return {"userid": 448520}
        if fn == "core_group_get_course_user_groups":
            assert kw == {"courseid": 5968, "userid": 448520}
            return {"groups": [], "warnings": []}
        raise AssertionError(fn)

    mock_client.call.side_effect = fake_call

    result = get_my_course_groups_for(mock_client, course_id=5968)

    assert result == []


def test_get_enrolled_users_for_real_response_shape(mock_client):
    mock_client.call.return_value = [
        {
            "id": 99068,
            "firstname": "이윤건",
            "fullname": "이윤건",
            "roles": [{"roleid": 5, "name": "", "shortname": "student", "sortorder": 0}],
        }
    ]

    result = get_enrolled_users_for(mock_client, course_id=5968)

    assert len(result) == 1
    assert result[0].fullname == "이윤건"
    assert result[0].roles[0].shortname == "student"
    mock_client.call.assert_called_once_with("core_enrol_get_enrolled_users", courseid=5968)
