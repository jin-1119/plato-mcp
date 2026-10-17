"""Unit tests for issue #96: get_user_profile, get_private_files_info,
get_user_preferences, add_private_file.

Fixture shapes taken verbatim from real live responses -- see
tests/integration/README.md.
"""

import pytest

from plato_mcp.errors import PlatoMCPError, WriteConfirmationError
from plato_mcp.tools.user_profile import (
    add_private_file_for,
    get_private_files_info_for,
    get_user_preferences_for,
    get_user_profile_for,
)


@pytest.fixture
def mock_client(mocker):
    client = mocker.Mock()
    return client


def test_get_user_profile_for_real_response_shape(mock_client):
    mock_client.call.return_value = [
        {
            "id": 448520,
            "username": "202443155",
            "fullname": "김진영",
            "email": "pnu72575535@pusan.ac.kr",
            "department": "경영학과",
            "institution": "경영대학",
            "profileimageurl": "https://plato.pusan.ac.kr/theme/image.php/coursemos/core/x/u/f1",
            "preferences": [{"name": "myCourseAllOpen", "value": "1"}],
        }
    ]

    result = get_user_profile_for(mock_client, course_id=5968, userid=448520)

    assert result.fullname == "김진영"
    assert result.department == "경영학과"
    mock_client.call.assert_called_once_with(
        "core_user_get_course_user_profiles",
        **{"userlist[0][userid]": 448520, "userlist[0][courseid]": 5968},
    )


def test_get_private_files_info_for_real_response_shape(mock_client):
    # Real live response shape for this account (issue #96) -- no private files.
    mock_client.call.return_value = {
        "filecount": 0,
        "foldercount": 0,
        "filesize": 0,
        "filesizewithoutreferences": 0,
        "warnings": [],
    }

    result = get_private_files_info_for(mock_client, userid=448520)

    assert result.filecount == 0
    mock_client.call.assert_called_once_with("core_user_get_private_files_info", userid=448520)


def test_get_user_preferences_for_real_response_shape(mock_client):
    # _lastloaded comes back as a raw int, not a string -- caught live
    # during this issue's verification (issue #96).
    mock_client.call.return_value = {
        "preferences": [
            {"name": "myCourseAllOpen", "value": "1"},
            {"name": "pw_nav", "value": "show"},
            {"name": "_lastloaded", "value": 1792219797},
        ],
        "warnings": [],
    }

    result = get_user_preferences_for(mock_client)

    assert len(result) == 3
    assert result[0].name == "myCourseAllOpen"
    assert result[2].value == 1792219797


def test_add_private_file_for_dry_run_does_not_upload(mock_client, tmp_path):
    f = tmp_path / "notes.txt"
    f.write_bytes(b"hello")

    result = add_private_file_for(mock_client, str(f))

    assert result.dry_run is True
    mock_client.upload_file.assert_not_called()
    mock_client.get_unused_draft_itemid.assert_not_called()


def test_add_private_file_for_real_run_uploads_then_registers(mock_client, tmp_path):
    mock_client.get_unused_draft_itemid.return_value = 777
    f = tmp_path / "notes.txt"
    content = b"hello private file"
    f.write_bytes(content)

    add_private_file_for(mock_client, str(f))
    result = add_private_file_for(mock_client, str(f), dry_run=False)

    assert result.executed is True
    mock_client.upload_file.assert_called_once_with(777, "notes.txt", content)
    mock_client.call.assert_called_once_with("core_user_add_user_private_files", draftid=777)


def test_add_private_file_for_without_preview_raises(mock_client, tmp_path):
    f = tmp_path / "notes.txt"
    f.write_bytes(b"x")
    with pytest.raises(WriteConfirmationError):
        add_private_file_for(mock_client, str(f), dry_run=False)


def test_add_private_file_for_missing_file_raises(mock_client):
    add_private_file_for(mock_client, "/no/such/file.txt")
    with pytest.raises(PlatoMCPError, match="not found"):
        add_private_file_for(mock_client, "/no/such/file.txt", dry_run=False)
