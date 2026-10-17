"""Unit tests for issue #90: create_calendar_event, delete_calendar_event,
get_calendar_access_info.

All round-tripped live against the real account (create -> confirmed via
list_calendar_events -> delete -> confirmed removal) -- see
tests/integration/README.md.
"""

import pytest

from plato_mcp.errors import WriteConfirmationError
from plato_mcp.tools.calendar import (
    create_calendar_event_for,
    delete_calendar_event_for,
    get_calendar_access_info_for,
)


@pytest.fixture
def mock_client(mocker):
    client = mocker.Mock()
    return client


def test_get_calendar_access_info_for_real_response_shape(mock_client):
    # Real live response shape (issue #90).
    mock_client.call.return_value = {
        "canmanageentries": False,
        "canmanageownentries": True,
        "canmanagegroupentries": False,
        "warnings": [],
    }

    result = get_calendar_access_info_for(mock_client)

    assert result.canmanageownentries is True
    assert result.canmanagegroupentries is False


def test_create_calendar_event_for_dry_run_does_not_call(mock_client):
    result = create_calendar_event_for(mock_client, name="Test", timestart=1790000000)
    assert result.dry_run is True
    mock_client.call.assert_not_called()


def test_create_calendar_event_for_real_run_requires_preview_then_calls(mock_client):
    mock_client.call.return_value = {"events": [{"id": 33584}]}

    create_calendar_event_for(mock_client, name="Test", timestart=1790000000)
    result = create_calendar_event_for(
        mock_client, name="Test", timestart=1790000000, dry_run=False
    )

    assert result.executed is True
    assert result.preview["event_id"] == 33584
    mock_client.call.assert_called_once_with(
        "core_calendar_create_calendar_events",
        **{
            "events[0][name]": "Test",
            "events[0][description]": "",
            "events[0][eventtype]": "user",
            "events[0][timestart]": 1790000000,
            "events[0][timeduration]": 0,
        },
    )


def test_create_calendar_event_for_without_preview_raises(mock_client):
    with pytest.raises(WriteConfirmationError):
        create_calendar_event_for(
            mock_client, name="Test", timestart=1790000000, dry_run=False
        )


def test_delete_calendar_event_for_dry_run_does_not_call(mock_client):
    result = delete_calendar_event_for(mock_client, event_id=33584)
    assert result.dry_run is True
    mock_client.call.assert_not_called()


def test_delete_calendar_event_for_real_run_requires_preview_then_calls(mock_client):
    mock_client.call.return_value = None  # real live response was None

    delete_calendar_event_for(mock_client, event_id=33584)
    result = delete_calendar_event_for(mock_client, event_id=33584, dry_run=False)

    assert result.executed is True
    mock_client.call.assert_called_once_with(
        "core_calendar_delete_calendar_events",
        **{"events[0][eventid]": 33584, "events[0][repeat]": 0},
    )
