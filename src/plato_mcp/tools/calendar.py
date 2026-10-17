"""Tool: list_calendar_events (issue #16), create/delete_calendar_event,
get_calendar_access_info (issue #90).

Issue #90 audited the rest of the core_calendar_* family against the real
account:
- `core_calendar_get_allowed_event_types` -- confirmed live:
  `{"allowedeventtypes": ["user"]}`. A student account can only create
  personal ("user") events, never course/group/category events -- not
  wired as its own tool since it's a fixed answer, documented here and
  in create_calendar_event's docstring instead.
- `core_calendar_get_calendar_access_information` -- confirmed live:
  `canmanageownentries=True`, `canmanagegroupentries=False`. Wired as
  get_calendar_access_info.
- `core_calendar_get_calendar_export_token` -- confirmed live to mint a
  real export credential (an iCal feed token). Deliberately NOT exposed
  as a tool -- same token-exposure concern already documented in
  files.py's TOKEN_IN_URL_WARNING (a bearer credential, not inert data).
- `get_calendar_day_view`/`get_calendar_monthly_view`/`get_calendar_upcoming_view`/
  `get_calendar_event_by_id` -- read-only views that are redundant with
  the already-implemented list_calendar_events for this account's actual
  use (personal + course events, no group/category use observed);
  skipped rather than building near-duplicate tools.
- create/delete round-tripped live: created a real personal event,
  confirmed it via list_calendar_events, deleted it, confirmed removal.
"""

import time
from datetime import UTC, datetime
from typing import Annotated

from mcp.server.mcpserver import Context
from pydantic import Field

from plato_mcp.context import get_client
from plato_mcp.models import CalendarAccessInfo, CalendarEvent
from plato_mcp.moodle_client import MoodleClient
from plato_mcp.tool_annotations import READ_ONLY_TOOL_ANNOTATIONS
from plato_mcp.write_tools import (
    WRITE_TOOL_ANNOTATIONS,
    WriteResult,
    default_preview_tracker,
    executed_result,
    preview_result,
)

DEFAULT_DAYS_AHEAD = 14
ACTION_CREATE_CALENDAR_EVENT = "create_calendar_event"
ACTION_DELETE_CALENDAR_EVENT = "delete_calendar_event"


def list_calendar_events_for(
    client: MoodleClient, days_ahead: int = DEFAULT_DAYS_AHEAD
) -> list[CalendarEvent]:
    # Server-side options[timestart]/options[timeend] filtering was tried first, but a live
    # test against a real PLATO account returned 0 events with it vs. 2 without -- the
    # webservice appears to need additional required sub-fields (courseids/groupids/userids,
    # userevents/siteevents flags) we don't otherwise need, so we filter client-side instead.
    now = int(time.time())
    window_end = now + days_ahead * 86400
    result = client.call("core_calendar_get_calendar_events")
    events = [CalendarEvent(**e) for e in result.get("events", [])]
    events = [e for e in events if e.timestart and now <= e.timestart.timestamp() <= window_end]
    events.sort(key=lambda e: e.timestart or datetime.min.replace(tzinfo=UTC))
    return events


def get_calendar_access_info_for(client: MoodleClient) -> CalendarAccessInfo:
    result = client.call("core_calendar_get_calendar_access_information")
    return CalendarAccessInfo(**result)


def create_calendar_event_for(
    client: MoodleClient,
    name: str,
    timestart: int,
    description: str = "",
    duration_seconds: int = 0,
    dry_run: bool = True,
) -> WriteResult:
    """Create a personal calendar event (issue #90). Only "user"-type
    (personal) events are supported -- confirmed live that's the only
    type a student account is allowed to create. IRREVERSIBLE once
    dry_run=False (same preview/confirm pattern as other write tools).
    """
    action_params = {
        "name": name,
        "timestart": timestart,
        "description": description,
        "duration_seconds": duration_seconds,
    }
    preview = {**action_params}

    if dry_run:
        default_preview_tracker.record_preview(
            client.session_key, ACTION_CREATE_CALENDAR_EVENT, action_params
        )
        return preview_result(preview, f"Calendar event '{name}'")

    default_preview_tracker.require_previewed(
        client.session_key, ACTION_CREATE_CALENDAR_EVENT, action_params
    )
    result = client.call(
        "core_calendar_create_calendar_events",
        **{
            "events[0][name]": name,
            "events[0][description]": description,
            "events[0][eventtype]": "user",
            "events[0][timestart]": timestart,
            "events[0][timeduration]": duration_seconds,
        },
    )
    created = result.get("events", [{}])[0]
    preview["event_id"] = created.get("id")
    return executed_result(preview, f"Calendar event '{name}'")


def delete_calendar_event_for(
    client: MoodleClient, event_id: int, dry_run: bool = True
) -> WriteResult:
    """Delete a personal calendar event this account owns (issue #90).
    IRREVERSIBLE once dry_run=False. Confirmed live this only works for
    events the account itself created (canmanageownentries) -- deleting
    a course/group event is expected to fail, not silently succeed.
    """
    action_params = {"event_id": event_id}
    preview = {**action_params}

    if dry_run:
        default_preview_tracker.record_preview(
            client.session_key, ACTION_DELETE_CALENDAR_EVENT, action_params
        )
        return preview_result(preview, f"Calendar event #{event_id}")

    default_preview_tracker.require_previewed(
        client.session_key, ACTION_DELETE_CALENDAR_EVENT, action_params
    )
    client.call(
        "core_calendar_delete_calendar_events",
        **{"events[0][eventid]": event_id, "events[0][repeat]": 0},
    )
    return executed_result(preview, f"Calendar event #{event_id}")


def register(mcp) -> None:
    @mcp.tool(annotations=READ_ONLY_TOOL_ANNOTATIONS)
    async def list_calendar_events(
        ctx: Context,
        days_ahead: Annotated[
            int, Field(description="How many days ahead of now to include events for.")
        ] = DEFAULT_DAYS_AHEAD,
    ) -> list[CalendarEvent]:
        """List upcoming calendar events within the next `days_ahead` days."""
        return list_calendar_events_for(get_client(ctx), days_ahead)

    @mcp.tool(annotations=READ_ONLY_TOOL_ANNOTATIONS)
    async def get_calendar_access_info(ctx: Context) -> CalendarAccessInfo:
        """Check this account's calendar-management permissions -- a
        student account can typically manage its own personal entries
        only, not course/group entries."""
        return get_calendar_access_info_for(get_client(ctx))

    @mcp.tool(annotations=WRITE_TOOL_ANNOTATIONS)
    async def create_calendar_event(
        name: Annotated[str, Field(description="Event title.")],
        timestart: Annotated[int, Field(description="Unix timestamp for the event's start.")],
        ctx: Context,
        description: Annotated[str, Field(description="Optional event description.")] = "",
        duration_seconds: Annotated[
            int, Field(description="Event duration in seconds, 0 for a point-in-time event.")
        ] = 0,
        dry_run: Annotated[
            bool,
            Field(
                description="If True (default), only preview the event without creating it. "
                "Call again with dry_run=False (same parameters) to actually create it."
            ),
        ] = True,
    ) -> WriteResult:
        """Create a personal calendar entry. IRREVERSIBLE once dry_run=False.
        Only personal ("user") events are supported -- course/group events
        are not something a student account can create.

        Call with dry_run=True (default) first, show the preview to the user,
        and only call again with dry_run=False after they explicitly confirm.
        """
        return create_calendar_event_for(
            get_client(ctx), name, timestart, description, duration_seconds, dry_run
        )

    @mcp.tool(annotations=WRITE_TOOL_ANNOTATIONS)
    async def delete_calendar_event(
        event_id: Annotated[int, Field(description="Calendar event id to delete.")],
        ctx: Context,
        dry_run: Annotated[
            bool,
            Field(
                description="If True (default), only preview the deletion without doing it. "
                "Call again with dry_run=False (same parameters) to actually delete it."
            ),
        ] = True,
    ) -> WriteResult:
        """Delete a personal calendar entry this account owns. IRREVERSIBLE
        once dry_run=False.

        Call with dry_run=True (default) first, show the preview to the user,
        and only call again with dry_run=False after they explicitly confirm.
        """
        return delete_calendar_event_for(get_client(ctx), event_id, dry_run)
