"""Unit tests for issue #88: get_course_completion_status, get_activity_completion_status,
and vod_progress parsing on CourseModule.

Fixture shapes are taken verbatim from real live responses against this
account's actual courses (course 13518, "26-2 대학생활원 온라인 OT") -- see
tests/integration/README.md.
"""

import pytest

from plato_mcp.errors import MoodleAPIError
from plato_mcp.models import CourseModule, CourseSection
from plato_mcp.tools.completion import (
    get_activity_completion_status_for,
    get_course_completion_status_for,
)


@pytest.fixture
def mock_client(mocker):
    client = mocker.Mock()
    return client


def _site_info_call(fn, **kw):
    if fn == "core_webservice_get_site_info":
        return {"userid": 448520}
    raise AssertionError(f"unexpected call: {fn}")


def test_get_course_completion_status_for_no_criteria_set(mock_client):
    def fake_call(fn, **kw):
        if fn == "core_webservice_get_site_info":
            return {"userid": 448520}
        if fn == "core_completion_get_course_completion_status":
            raise MoodleAPIError("No completion criteria set", errorcode="nocriteriaset")
        raise AssertionError(fn)

    mock_client.call.side_effect = fake_call

    result = get_course_completion_status_for(mock_client, course_id=6253)

    assert result.available is False
    assert result.completed is None
    assert "nocriteriaset" in result.message or "no course-level completion" in result.message


def test_get_course_completion_status_for_other_error_propagates(mock_client):
    def fake_call(fn, **kw):
        if fn == "core_webservice_get_site_info":
            return {"userid": 448520}
        if fn == "core_completion_get_course_completion_status":
            raise MoodleAPIError("nope", errorcode="someothererror")
        raise AssertionError(fn)

    mock_client.call.side_effect = fake_call

    with pytest.raises(MoodleAPIError):
        get_course_completion_status_for(mock_client, course_id=6253)


# Real response shape from course 13518, confirmed live (issue #88).
_REAL_COURSE_COMPLETION_RESPONSE = {
    "completionstatus": {
        "completed": True,
        "aggregation": 2,
        "completions": [
            {
                "type": 4,
                "title": "활동 완료",
                "status": "예",
                "complete": True,
                "timecompleted": 1790600877,
                "details": {
                    "type": "활동 완료",
                    "criteria": '<a href="https://plato.pusan.ac.kr/mod/vod/view.php?id=46037">'
                    "2026학년도 2학기 대학생활원 OT(한)</a>",
                    "requirement": "동영상 를 보기",
                    "status": "",
                },
            }
        ],
    }
}


def test_get_course_completion_status_for_real_response_shape(mock_client):
    def fake_call(fn, **kw):
        if fn == "core_webservice_get_site_info":
            return {"userid": 448520}
        if fn == "core_completion_get_course_completion_status":
            return _REAL_COURSE_COMPLETION_RESPONSE
        raise AssertionError(fn)

    mock_client.call.side_effect = fake_call

    result = get_course_completion_status_for(mock_client, course_id=13518)

    assert result.available is True
    assert result.completed is True
    assert len(result.criteria) == 1
    assert result.criteria[0].complete is True
    assert result.criteria[0].details.requirement == "동영상 를 보기"


# Real response shape from course 13518, confirmed live (issue #88).
_REAL_ACTIVITY_COMPLETION_RESPONSE = {
    "statuses": [
        {
            "cmid": 46037,
            "modname": "vod",
            "instance": 7832,
            "state": 1,
            "timecompleted": 1790600877,
            "tracking": 2,
            "overrideby": None,
            "valueused": False,
            "hascompletion": True,
            "isautomatic": True,
            "istrackeduser": True,
            "uservisible": True,
            "details": [
                {"rulename": "completionview", "rulevalue": {"status": 1, "description": "보기"}},
                {
                    "rulename": "completiontimeenabled",
                    "rulevalue": {"status": 1, "description": "Must spend time studying."},
                },
            ],
            "isoverallcomplete": True,
        }
    ],
    "warnings": [],
}


def test_get_activity_completion_status_for_real_response_shape(mock_client):
    def fake_call(fn, **kw):
        if fn == "core_webservice_get_site_info":
            return {"userid": 448520}
        if fn == "core_completion_get_activities_completion_status":
            return _REAL_ACTIVITY_COMPLETION_RESPONSE
        raise AssertionError(fn)

    mock_client.call.side_effect = fake_call

    statuses = get_activity_completion_status_for(mock_client, course_id=13518)

    assert len(statuses) == 1
    assert statuses[0].modname == "vod"
    assert statuses[0].isoverallcomplete is True
    assert statuses[0].details[0].rulename == "completionview"
    assert statuses[0].details[0].status == 1
    assert statuses[0].details[0].description == "보기"


# Real vod module customdata, confirmed live (issue #88 -- course 13518).
_REAL_VOD_MODULE = {
    "id": 46037,
    "name": "2026학년도 2학기 대학생활원 OT(한)",
    "modname": "vod",
    "customdata": (
        '{"playtime":"461","timeopen":1788483600,"timeclose":1790607540,'
        '"timelateness":1790607540,"completionprogress":95,"latenessprogress":50,'
        '"progress":"1","useattend":"1","autograde":"0","restricted":"1",'
        '"add_grade_item":"0","details":"","isOpenTimeCheck":false,'
        '"customcompletionrules":{"completiontimeenabled":"1"}}'
    ),
}


def test_course_module_parses_vod_progress_from_real_customdata():
    module = CourseModule(**_REAL_VOD_MODULE)

    assert module.vod_progress is not None
    assert module.vod_progress.playtime_seconds == 461
    assert module.vod_progress.completion_progress_percent == 95
    assert module.vod_progress.lateness_progress_percent == 50
    assert module.vod_progress.attendance_required is True
    assert module.vod_progress.time_open is not None
    assert module.vod_progress.time_close is not None


def test_course_module_vod_progress_is_none_for_non_vod_module():
    module = CourseModule(id=1, name="Lecture 1", modname="ubfile")
    assert module.vod_progress is None


def test_course_module_vod_progress_is_none_when_customdata_missing():
    module = CourseModule(id=1, name="Some vod", modname="vod")
    assert module.vod_progress is None


def test_course_module_vod_progress_tolerates_malformed_customdata():
    module = CourseModule(id=1, name="Some vod", modname="vod", customdata="not valid json{{{")
    assert module.vod_progress is None


def test_course_section_round_trips_vod_module():
    section = CourseSection(id=1, name="Week 1", modules=[_REAL_VOD_MODULE])
    assert section.modules[0].vod_progress.completion_progress_percent == 95
