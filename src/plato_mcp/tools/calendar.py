"""Tool: list_calendar_events (issue #16)."""

import time
from datetime import UTC, datetime
from typing import Annotated

from mcp.server.mcpserver import Context
from pydantic import Field

from plato_mcp.context import get_client
from plato_mcp.models import CalendarEvent
from plato_mcp.moodle_client import MoodleClient
from plato_mcp.tool_annotations import READ_ONLY_TOOL_ANNOTATIONS

DEFAULT_DAYS_AHEAD = 14


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
