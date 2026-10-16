"""Unit tests for issue #89: get_upcoming_action_events, get_courses_by_timeline,
get_grades_overview.

Fixture shapes are taken verbatim from real live responses against this
account's real courses -- see tests/integration/README.md.
"""

import pytest

from plato_mcp.tools.dashboard import (
    get_courses_by_timeline_for,
    get_grades_overview_for,
    get_upcoming_action_events_for,
)


@pytest.fixture
def mock_client(mocker):
    client = mocker.Mock()
    return client


# Real response shape from core_calendar_get_action_events_by_timesort (issue #89).
_REAL_ACTION_EVENTS_RESPONSE = {
    "events": [
        {
            "id": 17867,
            "name": "칼 포퍼식 토론의 이해 - 부산대학교 모형 - ",
            "description": "<div>...</div>",
            "component": "mod_vod",
            "modulename": "vod",
            "activitystr": "동영상에 대한 조치가 필요합니다.",
            "eventtype": "due",
            "timestart": 1678978800,
            "timesort": 2531746740,
            "overdue": False,
            "course": {
                "id": 10502,
                "fullname": "교양교육원 비교과프로그램 영상 아카이브",
                "shortname": "48458f6c1eebb90422c8395c9cf425ed",
                "courseimage": "data:image/svg+xml;base64,AAAA...",  # dropped by ActionEventCourse
            },
        }
    ],
    "firstid": 17867,
    "lastid": 17867,
}


def test_get_upcoming_action_events_for_real_response_shape(mock_client):
    mock_client.call.return_value = _REAL_ACTION_EVENTS_RESPONSE

    events = get_upcoming_action_events_for(mock_client, limit=5)

    assert len(events) == 1
    assert events[0].eventtype == "due"
    assert events[0].activitystr == "동영상에 대한 조치가 필요합니다."
    assert events[0].course.id == 10502
    assert events[0].timesort.year == 2050  # far-future sentinel, no overflow
    mock_client.call.assert_called_once()
    assert mock_client.call.call_args.args[0] == "core_calendar_get_action_events_by_timesort"
    assert mock_client.call.call_args.kwargs["limitnum"] == 5


def test_get_upcoming_action_events_for_uses_now_as_default_timesortfrom(mock_client):
    mock_client.call.return_value = {"events": []}

    get_upcoming_action_events_for(mock_client)

    assert "timesortfrom" in mock_client.call.call_args.kwargs
    assert mock_client.call.call_args.kwargs["timesortfrom"] > 0


# Real response shape from core_course_get_enrolled_courses_by_timeline_classification.
_REAL_TIMELINE_RESPONSE = {
    "courses": [
        {
            "id": 12633,
            "fullname": "[25.동계] 영어연수 단기파견",
            "shortname": "38ca905a51666d3f8e5bbcf55321a3cf",
            "visible": True,
            "startdate": 1764082800,
            "enddate": 0,
            "courseimage": "data:image/svg+xml;base64,AAAA...",
        }
    ]
}


def test_get_courses_by_timeline_for_real_response_shape(mock_client):
    mock_client.call.return_value = _REAL_TIMELINE_RESPONSE

    courses = get_courses_by_timeline_for(mock_client, "inprogress")

    assert len(courses) == 1
    assert courses[0].fullname == "[25.동계] 영어연수 단기파견"
    assert courses[0].enddate is None  # enddate=0 means "no end date" (see CourseSummary)
    mock_client.call.assert_called_once_with(
        "core_course_get_enrolled_courses_by_timeline_classification", classification="inprogress"
    )


def test_get_courses_by_timeline_for_defaults_to_inprogress(mock_client):
    mock_client.call.return_value = {"courses": []}
    get_courses_by_timeline_for(mock_client)
    assert mock_client.call.call_args.kwargs["classification"] == "inprogress"


# Real response shape from gradereport_overview_get_course_grades.
_REAL_GRADES_OVERVIEW_RESPONSE = {
    "grades": [
        {"courseid": 6253, "grade": "-", "rawgrade": None},
        {"courseid": 5968, "grade": "85.00", "rawgrade": 85.0},
    ],
    "warnings": [],
}


def test_get_grades_overview_for_real_response_shape(mock_client):
    def fake_call(fn, **kw):
        if fn == "core_webservice_get_site_info":
            return {"userid": 448520}
        if fn == "gradereport_overview_get_course_grades":
            assert kw["userid"] == 448520
            return _REAL_GRADES_OVERVIEW_RESPONSE
        raise AssertionError(fn)

    mock_client.call.side_effect = fake_call

    grades = get_grades_overview_for(mock_client)

    assert len(grades) == 2
    assert grades[0].grade == "-"
    assert grades[1].rawgrade == 85.0
