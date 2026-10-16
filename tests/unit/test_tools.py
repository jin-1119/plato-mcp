"""Unit tests for Phase 1 tool logic functions.

These test the `*_for(client, ...)` functions directly against a mocked
MoodleClient, bypassing the MCP Context entirely -- the Context is just
plumbing for the session key (see context.py) and isn't part of the
business logic being tested here.
"""

from datetime import UTC, datetime, timedelta

import pytest

from plato_mcp.errors import MoodleAPIError, PlatoMCPError
from plato_mcp.tools.assignments import (
    get_assignment_detail_for,
    list_assignments_for,
    submit_assignment_for,
)
from plato_mcp.tools.calendar import list_calendar_events_for
from plato_mcp.tools.courses import get_course_contents_for, list_courses_for
from plato_mcp.tools.grades import get_grades_access_info_for, get_grades_for
from plato_mcp.tools.messages import get_unread_messages_for


@pytest.fixture
def mock_client(mocker):
    client = mocker.Mock()
    return client


def _epoch(dt: datetime) -> int:
    return int(dt.timestamp())


def test_list_courses_for(mock_client):
    start = datetime(2026, 9, 1, tzinfo=UTC)
    end = datetime(2026, 12, 20, tzinfo=UTC)
    mock_client.call.side_effect = lambda fn, **kw: (
        {"userid": 448520}
        if fn == "core_webservice_get_site_info"
        else [
            {
                "id": 6253,
                "fullname": "거시경제학",
                "shortname": "MACRO",
                "visible": 1,
                "startdate": _epoch(start),
                "enddate": _epoch(end),
                "extra": "ignored",
            },
            {
                "id": 12633,
                "fullname": "[25.동계] 영어연수 단기파견",
                "shortname": "WINTER",
                "visible": 1,
                "startdate": _epoch(datetime(2025, 12, 1, tzinfo=UTC)),
                "enddate": 0,  # Moodle's "no end date set"
            },
        ]
    )
    result = list_courses_for(mock_client)
    assert len(result) == 2
    assert result[0].id == 6253
    assert result[0].fullname == "거시경제학"
    assert result[0].startdate == start
    assert result[0].enddate == end
    assert result[1].enddate is None  # 0 -> None, not epoch-zero datetime


def test_get_course_contents_for(mock_client):
    mock_client.call.return_value = [
        {
            "id": 1,
            "name": "Week 1",
            "modules": [
                {
                    "id": 100,
                    "name": "Syllabus",
                    "modname": "resource",
                    "url": "https://plato.pusan.ac.kr/mod/resource/view.php?id=100",
                    "completiondata": {"isoverallcomplete": True},
                    "contents": [
                        {
                            "filename": "syllabus.pdf",
                            "fileurl": "https://x/f.pdf",
                            "filesize": 1000,
                            "mimetype": "application/pdf",
                            "author": "안영빈",
                            "timemodified": _epoch(datetime(2026, 9, 1, tzinfo=UTC)),
                        }
                    ],
                }
            ],
        }
    ]
    result = get_course_contents_for(mock_client, course_id=6253)
    assert len(result) == 1
    file_entry = result[0].modules[0].contents[0]
    assert file_entry.filename == "syllabus.pdf"
    assert file_entry.needs_token is True
    assert file_entry.mimetype == "application/pdf"
    assert file_entry.author == "안영빈"
    assert file_entry.timemodified == datetime(2026, 9, 1, tzinfo=UTC)
    assert result[0].modules[0].completed is True


def test_get_course_contents_for_completed_missing_when_no_completiondata(mock_client):
    mock_client.call.return_value = [
        {
            "id": 1,
            "name": "Week 1",
            "modules": [{"id": 100, "name": "Syllabus", "modname": "resource", "contents": []}],
        }
    ]
    result = get_course_contents_for(mock_client, course_id=6253)
    assert result[0].modules[0].completed is None


def test_list_assignments_for_flattens_courses(mock_client):
    mock_client.call.return_value = {
        "courses": [
            {
                "id": 6253,
                "assignments": [
                    {"id": 1, "name": "HW1", "duedate": _epoch(datetime(2026, 10, 1, tzinfo=UTC))},
                ],
            }
        ],
        "warnings": [],
    }
    result = list_assignments_for(mock_client, [6253])
    assert len(result) == 1
    assert result[0].courseid == 6253
    assert result[0].duedate == datetime(2026, 10, 1, tzinfo=UTC)


def test_list_assignments_for_full_schema(mock_client):
    due = datetime(2026, 10, 1, tzinfo=UTC)
    cutoff = datetime(2026, 10, 3, tzinfo=UTC)
    mock_client.call.return_value = {
        "courses": [
            {
                "id": 6253,
                "assignments": [
                    {
                        "id": 1,
                        "cmid": 999,
                        "name": "HW1",
                        "duedate": _epoch(due),
                        "cutoffdate": _epoch(cutoff),
                        "intro": "<p>Do the thing</p>",
                        "introattachments": [
                            {"filename": "spec.pdf", "fileurl": "https://x/spec.pdf"}
                        ],
                        "teamsubmission": 1,
                        "requireallteammemberssubmit": 0,
                        "maxattempts": -1,
                    },
                ],
            }
        ],
    }
    result = list_assignments_for(mock_client, [6253])
    a = result[0]
    assert a.cmid == 999
    assert a.cutoffdate == cutoff
    assert a.intro == "<p>Do the thing</p>"
    assert a.introattachments[0].filename == "spec.pdf"
    assert a.teamsubmission is True
    assert a.requireallteammemberssubmit is False
    assert a.maxattempts == -1


def test_get_assignment_detail_for_not_submitted(mock_client):
    due = datetime(2026, 10, 1, tzinfo=UTC)

    def fake_call(fn, **kw):
        if fn == "mod_assign_get_assignments":
            return {
                "courses": [
                    {"id": 6253, "assignments": [{"id": 1, "name": "HW1", "duedate": _epoch(due)}]}
                ]
            }
        if fn == "core_webservice_get_site_info":
            return {"userid": 448520}
        if fn == "mod_assign_get_submission_status":
            return {"lastattempt": {"submission": None}}
        raise AssertionError(f"unexpected call: {fn}")

    mock_client.call.side_effect = fake_call
    detail = get_assignment_detail_for(mock_client, course_id=6253, assignment_id=1)
    assert detail.assignment.name == "HW1"
    assert detail.submission is None


def test_get_assignment_detail_for_late_submission(mock_client):
    due = datetime(2026, 10, 1, tzinfo=UTC)
    submitted_late = datetime(2026, 10, 2, tzinfo=UTC)

    def fake_call(fn, **kw):
        if fn == "mod_assign_get_assignments":
            return {
                "courses": [
                    {"id": 6253, "assignments": [{"id": 1, "name": "HW1", "duedate": _epoch(due)}]}
                ]
            }
        if fn == "core_webservice_get_site_info":
            return {"userid": 448520}
        if fn == "mod_assign_get_submission_status":
            return {
                "lastattempt": {
                    "submission": {"status": "submitted", "timemodified": _epoch(submitted_late)}
                }
            }
        raise AssertionError(f"unexpected call: {fn}")

    mock_client.call.side_effect = fake_call
    detail = get_assignment_detail_for(mock_client, course_id=6253, assignment_id=1)
    assert detail.submission.submitted is True
    assert detail.submission.late is True


def test_get_assignment_detail_for_full_feedback_and_history(mock_client):
    due = datetime(2026, 10, 1, tzinfo=UTC)
    graded_at = datetime(2026, 10, 5, tzinfo=UTC)

    def fake_call(fn, **kw):
        if fn == "mod_assign_get_assignments":
            return {
                "courses": [
                    {"id": 6253, "assignments": [{"id": 1, "name": "HW1", "duedate": _epoch(due)}]}
                ]
            }
        if fn == "core_webservice_get_site_info":
            return {"userid": 448520}
        if fn == "mod_assign_get_submission_status":
            return {
                "lastattempt": {
                    "submission": {"status": "submitted", "timemodified": _epoch(due)},
                    "cansubmit": False,
                    "locked": True,
                    "extensionduedate": _epoch(due + timedelta(days=2)),
                    "gradingstatus": "graded",
                },
                "feedback": {
                    "grade": {"grade": "85.00000", "gradefordisplay": "85 / 100"},
                    "gradefordisplay": "85 / 100",
                    "gradeddate": _epoch(graded_at),
                    "plugins": [
                        {
                            "type": "comments",
                            "name": "Feedback comments",
                            "editorfields": [
                                {"name": "comments", "text": "잘 했습니다", "format": 1}
                            ],
                        }
                    ],
                },
                "previousattempts": [
                    {
                        "attemptnumber": 0,
                        "submission": {"status": "submitted", "timemodified": _epoch(due)},
                        "grade": {"grade": "70.00000"},
                    }
                ],
                "assignmentdata": {
                    "activity": "<p>extra info</p>",
                    "attachments": {
                        "intro": [{"filename": "spec.pdf", "fileurl": "https://x/spec.pdf"}],
                        "activity": [],
                    },
                },
            }
        raise AssertionError(f"unexpected call: {fn}")

    mock_client.call.side_effect = fake_call
    detail = get_assignment_detail_for(mock_client, course_id=6253, assignment_id=1)

    assert detail.submission.cansubmit is False
    assert detail.submission.locked is True
    assert detail.submission.extensionduedate == due + timedelta(days=2)
    assert detail.submission.gradingstatus == "graded"

    assert detail.feedback.grade.grade == "85.00000"
    assert detail.feedback.gradefordisplay == "85 / 100"
    assert detail.feedback.gradeddate == graded_at
    assert detail.feedback.plugins[0].editorfields[0].text == "잘 했습니다"

    assert len(detail.previousattempts) == 1
    assert detail.previousattempts[0].grade.grade == "70.00000"

    assert detail.extra.activity == "<p>extra info</p>"
    assert detail.extra.attachments_intro[0].filename == "spec.pdf"
    assert detail.extra.attachments_activity == []


def test_get_assignment_detail_for_unknown_id_raises(mock_client):
    mock_client.call.return_value = {"courses": [{"id": 6253, "assignments": []}]}
    with pytest.raises(ValueError):
        get_assignment_detail_for(mock_client, course_id=6253, assignment_id=999)


def test_submit_assignment_for_dry_run_does_not_call_save_submission(mock_client):
    mock_client.call.return_value = {
        "courses": [{"id": 6253, "assignments": [{"id": 1, "name": "HW1"}]}]
    }

    result = submit_assignment_for(mock_client, course_id=6253, assignment_id=1, text="my answer")

    assert result.dry_run is True
    assert result.executed is False
    assert result.preview["text"] == "my answer"
    assert result.preview["assignment_name"] == "HW1"
    mock_client.call.assert_called_once_with("mod_assign_get_assignments", courseids=[6253])


def test_submit_assignment_for_real_run_calls_save_submission(mock_client):
    def fake_call(fn, **kw):
        if fn == "mod_assign_get_assignments":
            return {"courses": [{"id": 6253, "assignments": [{"id": 1, "name": "HW1"}]}]}
        if fn == "mod_assign_save_submission":
            return []
        raise AssertionError(f"unexpected call: {fn}")

    mock_client.call.side_effect = fake_call

    # dry_run=False now requires a matching preview first (issue #37).
    submit_assignment_for(mock_client, course_id=6253, assignment_id=1, text="my answer")
    result = submit_assignment_for(
        mock_client, course_id=6253, assignment_id=1, text="my answer", dry_run=False
    )

    assert result.dry_run is False
    assert result.executed is True

    save_call = next(
        c for c in mock_client.call.call_args_list if c.args[0] == "mod_assign_save_submission"
    )
    assert save_call.kwargs["assignmentid"] == 1
    assert save_call.kwargs["plugindata[onlinetext_editor][text]"] == "my answer"
    assert save_call.kwargs["plugindata[onlinetext_editor][format]"] == 2


def test_submit_assignment_for_unknown_id_raises(mock_client):
    mock_client.call.return_value = {"courses": [{"id": 6253, "assignments": []}]}
    with pytest.raises(ValueError):
        submit_assignment_for(mock_client, course_id=6253, assignment_id=999, text="x")


# configs shape taken verbatim from a real live mod_assign_get_assignments
# response (course 5968, "중간고사 전 과제" -- the first real assignment to
# ever exist on the test account, issue #84).
_REAL_FILE_SUBMISSION_ASSIGNMENT = {
    "id": 4975,
    "name": "중간고사 전 과제",
    "configs": [
        {"plugin": "file", "subtype": "assignsubmission", "name": "enabled", "value": "1"},
        {
            "plugin": "file",
            "subtype": "assignsubmission",
            "name": "maxfilesubmissions",
            "value": "2",
        },
        {
            "plugin": "file",
            "subtype": "assignsubmission",
            "name": "maxsubmissionsizebytes",
            "value": "1000",
        },
        {"plugin": "file", "subtype": "assignsubmission", "name": "filetypeslist", "value": ""},
    ],
}


def test_submit_assignment_for_file_dry_run_previews_without_uploading(mock_client, tmp_path):
    mock_client.call.return_value = {
        "courses": [{"id": 5968, "assignments": [_REAL_FILE_SUBMISSION_ASSIGNMENT]}]
    }
    f = tmp_path / "report.pdf"
    f.write_bytes(b"%PDF-1.4 fake pdf content")

    result = submit_assignment_for(
        mock_client, course_id=5968, assignment_id=4975, file_paths=[str(f)]
    )

    assert result.dry_run is True
    assert result.preview["file_paths"] == [str(f)]
    mock_client.upload_file.assert_not_called()
    mock_client.get_unused_draft_itemid.assert_not_called()


def test_submit_assignment_for_file_real_run_uploads_then_saves_submission(mock_client, tmp_path):
    def fake_call(fn, **kw):
        if fn == "mod_assign_get_assignments":
            return {"courses": [{"id": 5968, "assignments": [_REAL_FILE_SUBMISSION_ASSIGNMENT]}]}
        if fn == "mod_assign_save_submission":
            return []
        raise AssertionError(f"unexpected call: {fn}")

    mock_client.call.side_effect = fake_call
    mock_client.get_unused_draft_itemid.return_value = 999
    f = tmp_path / "report.pdf"
    content = b"%PDF-1.4 fake pdf content"
    f.write_bytes(content)

    submit_assignment_for(mock_client, course_id=5968, assignment_id=4975, file_paths=[str(f)])
    result = submit_assignment_for(
        mock_client, course_id=5968, assignment_id=4975, file_paths=[str(f)], dry_run=False
    )

    assert result.executed is True
    mock_client.get_unused_draft_itemid.assert_called_once()
    mock_client.upload_file.assert_called_once_with(999, "report.pdf", content)
    save_call = next(
        c for c in mock_client.call.call_args_list if c.args[0] == "mod_assign_save_submission"
    )
    assert save_call.kwargs["plugindata[files_filemanager]"] == 999
    assert "plugindata[onlinetext_editor][text]" not in save_call.kwargs


def test_submit_assignment_for_file_rejects_when_submission_type_disabled(mock_client, tmp_path):
    mock_client.call.return_value = {
        "courses": [{"id": 6253, "assignments": [{"id": 1, "name": "HW1"}]}]  # no configs at all
    }
    f = tmp_path / "x.pdf"
    f.write_bytes(b"x")

    with pytest.raises(PlatoMCPError, match="did not report whether"):
        submit_assignment_for(mock_client, course_id=6253, assignment_id=1, file_paths=[str(f)])


def test_submit_assignment_for_file_rejects_too_many_files(mock_client, tmp_path):
    mock_client.call.return_value = {
        "courses": [{"id": 5968, "assignments": [_REAL_FILE_SUBMISSION_ASSIGNMENT]}]
    }
    paths = []
    for i in range(3):  # max_files is 2 in the fixture
        f = tmp_path / f"f{i}.pdf"
        f.write_bytes(b"x")
        paths.append(str(f))

    with pytest.raises(PlatoMCPError, match="at most 2"):
        submit_assignment_for(mock_client, course_id=5968, assignment_id=4975, file_paths=paths)


def test_submit_assignment_for_file_rejects_oversized_file(mock_client, tmp_path):
    mock_client.call.return_value = {
        "courses": [{"id": 5968, "assignments": [_REAL_FILE_SUBMISSION_ASSIGNMENT]}]
    }
    f = tmp_path / "big.pdf"
    f.write_bytes(b"x" * 2000)  # max_size_bytes is 1000 in the fixture

    with pytest.raises(PlatoMCPError, match="exceeding"):
        submit_assignment_for(mock_client, course_id=5968, assignment_id=4975, file_paths=[str(f)])


def test_submit_assignment_for_file_rejects_disallowed_extension(mock_client, tmp_path):
    mock_client.call.return_value = {
        "courses": [{"id": 5968, "assignments": [_REAL_FILE_SUBMISSION_ASSIGNMENT]}]
    }
    f = tmp_path / "script.exe"
    f.write_bytes(b"x")

    with pytest.raises(PlatoMCPError, match="not allowed"):
        submit_assignment_for(mock_client, course_id=5968, assignment_id=4975, file_paths=[str(f)])


def test_submit_assignment_for_file_rejects_missing_file(mock_client):
    mock_client.call.return_value = {
        "courses": [{"id": 5968, "assignments": [_REAL_FILE_SUBMISSION_ASSIGNMENT]}]
    }

    with pytest.raises(PlatoMCPError, match="not found"):
        submit_assignment_for(
            mock_client, course_id=5968, assignment_id=4975, file_paths=["/no/such/file.pdf"]
        )


def test_submit_assignment_for_requires_text_or_files(mock_client):
    with pytest.raises(PlatoMCPError, match="empty submission"):
        submit_assignment_for(mock_client, course_id=5968, assignment_id=4975)


def test_assignment_summary_file_submission_computed_field_from_real_configs():
    from plato_mcp.models import AssignmentSummary

    assignment = AssignmentSummary(**_REAL_FILE_SUBMISSION_ASSIGNMENT)

    assert assignment.file_submission.known is True
    assert assignment.file_submission.enabled is True
    assert assignment.file_submission.max_files == 2
    assert assignment.file_submission.max_size_bytes == 1000
    assert assignment.file_submission.allowed_extensions == []
    # onlinetext has no config rows at all for this real assignment -- it's
    # genuinely disabled for this one, which "known" lets us tell apart from
    # "we don't know" (see onlinetext fail-open behavior in assignments.py).
    assert assignment.onlinetext_submission.known is False

    dumped = assignment.model_dump()
    assert dumped["file_submission"]["enabled"] is True


def test_get_grades_for_available(mock_client):
    def fake_call(fn, **kw):
        if fn == "core_webservice_get_site_info":
            return {"userid": 448520}
        item = {
            "id": 1,
            "itemname": "출석",
            "itemtype": "manual",
            "graderaw": 10.0,
            "grademin": 0.0,
            "grademax": 100.0,
            "feedback": "잘했습니다",
        }
        return {"usergrades": [{"gradeitems": [item]}]}

    mock_client.call.side_effect = fake_call
    result = get_grades_for(mock_client, course_id=6253)
    assert result.available is True
    assert result.gradeitems[0].graderaw == 10.0
    assert result.gradeitems[0].grademax == 100.0
    assert result.gradeitems[0].feedback == "잘했습니다"


def test_get_grades_for_no_permission(mock_client):
    def fake_call(fn, **kw):
        if fn == "core_webservice_get_site_info":
            return {"userid": 448520}
        raise MoodleAPIError("No permission", errorcode="nopermissiontoviewgrades")

    mock_client.call.side_effect = fake_call
    result = get_grades_for(mock_client, course_id=12633)
    assert result.available is False
    assert result.gradeitems == []


def test_get_grades_for_other_error_propagates(mock_client):
    def fake_call(fn, **kw):
        if fn == "core_webservice_get_site_info":
            return {"userid": 448520}
        raise MoodleAPIError("boom", errorcode="somethingelse")

    mock_client.call.side_effect = fake_call
    with pytest.raises(MoodleAPIError):
        get_grades_for(mock_client, course_id=6253)


def test_get_grades_access_info_for_real_response_shape(mock_client):
    # Real live response shape against course 5968 (issue #95).
    mock_client.call.return_value = {
        "canviewusergradereport": True,
        "canviewmygrades": True,
        "canviewallgrades": False,
        "warnings": [],
    }

    result = get_grades_access_info_for(mock_client, course_id=5968)

    assert result.canviewmygrades is True
    assert result.canviewallgrades is False
    mock_client.call.assert_called_once_with(
        "gradereport_user_get_access_information", courseid=5968
    )


def test_list_calendar_events_sorted_chronologically(mock_client):
    now = datetime.now(UTC)
    later = _epoch(now + timedelta(days=5))
    earlier = _epoch(now + timedelta(days=2))
    past = _epoch(now - timedelta(days=1))
    mock_client.call.return_value = {
        "events": [
            {"id": 1, "name": "Later", "timestart": later},
            {"id": 2, "name": "Earlier", "timestart": earlier},
            {"id": 3, "name": "Past", "timestart": past},
        ]
    }
    result = list_calendar_events_for(mock_client, days_ahead=14)
    assert [e.name for e in result] == ["Earlier", "Later"]  # past event filtered out


def test_list_calendar_events_excludes_events_beyond_window(mock_client):
    now = datetime.now(UTC)
    within = _epoch(now + timedelta(days=5))
    beyond = _epoch(now + timedelta(days=20))
    mock_client.call.return_value = {
        "events": [
            {"id": 1, "name": "Within", "timestart": within, "description": "<p>hi</p>"},
            {"id": 2, "name": "Beyond", "timestart": beyond},
        ]
    }
    result = list_calendar_events_for(mock_client, days_ahead=14)
    assert [e.name for e in result] == ["Within"]
    assert result[0].description == "<p>hi</p>"


def test_get_unread_messages_for(mock_client):
    def fake_call(fn, **kw):
        if fn == "core_webservice_get_site_info":
            return {"userid": 448520}
        assert kw["read"] == 0
        return {
            "messages": [
                {
                    "id": 1,
                    "useridfrom": -10,
                    "userfromfullname": "PLATO",
                    "subject": "새 로그인",
                    "eventtype": "newlogin",
                }
            ]
        }

    mock_client.call.side_effect = fake_call
    result = get_unread_messages_for(mock_client)
    assert result[0].userfromfullname == "PLATO"
    assert result[0].eventtype == "newlogin"
    assert len(result) == 1
    assert result[0].subject == "새 로그인"
