"""Unit tests for issue #103: get_course_module, search_courses, get_recent_courses.

Fixture shapes taken verbatim from real live responses -- see
tests/integration/README.md.
"""

import pytest

from plato_mcp.tools.course_lookup import (
    get_course_module_for,
    get_recent_courses_for,
    search_courses_for,
)


@pytest.fixture
def mock_client(mocker):
    client = mocker.Mock()
    return client


def test_get_course_module_for_real_response_shape(mock_client):
    mock_client.call.return_value = {
        "cm": {
            "id": 31637,
            "course": 6253,
            "module": 29,
            "name": "Lecture 1",
            "modname": "ubfile",
            "instance": 2744,
            "section": 105671,
            "sectionnum": 1,
        },
        "warnings": [],
    }

    result = get_course_module_for(mock_client, cmid=31637)

    assert result.name == "Lecture 1"
    assert result.modname == "ubfile"
    mock_client.call.assert_called_once_with("core_course_get_course_module", cmid=31637)


def test_search_courses_for_real_response_shape(mock_client):
    mock_client.call.return_value = {
        "total": 180,
        "courses": [
            {
                "id": 7318,
                "fullname": "ON213.데이터 기반 교수학습지원 사업 질 관리 고도화를 위한 제안",
                "shortname": "ON213",
                "courseimage": "https://example.com/x.svg",
            }
        ],
        "warnings": [],
    }

    results = search_courses_for(mock_client, "관리")

    assert len(results) == 1
    assert results[0].shortname == "ON213"
    mock_client.call.assert_called_once_with(
        "core_course_search_courses", criterianame="search", criteriavalue="관리"
    )


def test_get_recent_courses_for_real_response_shape(mock_client):
    mock_client.call.return_value = [
        {
            "id": 5968,
            "fullname": "관리회계",
            "shortname": "관리회계 (2026-0020, DB3000927_005)",
            "visible": True,
            "startdate": 1788188400,
            "enddate": 1797865199,
        }
    ]

    results = get_recent_courses_for(mock_client)

    assert len(results) == 1
    assert results[0].id == 5968
    mock_client.call.assert_called_once_with("core_course_get_recent_courses")
