"""Shared annotations for read-only tools.

See write_tools.py's WRITE_TOOL_ANNOTATIONS for the write-tool counterpart.
"""

from mcp.types import ToolAnnotations

READ_ONLY_TOOL_ANNOTATIONS = ToolAnnotations(
    read_only_hint=True,
    open_world_hint=True,
)
