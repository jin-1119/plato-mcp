from . import (
    assignments,
    blocks,
    calendar,
    completion,
    course_lookup,
    course_updates,
    courses,
    dashboard,
    downloads,
    forum,
    grades,
    messages,
    notices_qna,
    quiz,
    video_conference,
)


def register_all(mcp) -> None:
    courses.register(mcp)
    assignments.register(mcp)
    grades.register(mcp)
    calendar.register(mcp)
    messages.register(mcp)
    notices_qna.register(mcp)
    downloads.register(mcp)
    completion.register(mcp)
    dashboard.register(mcp)
    quiz.register(mcp)
    forum.register(mcp)
    course_updates.register(mcp)
    course_lookup.register(mcp)
    blocks.register(mcp)
    video_conference.register(mcp)
