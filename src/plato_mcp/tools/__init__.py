from . import (
    assignments,
    calendar,
    completion,
    course_updates,
    courses,
    dashboard,
    downloads,
    forum,
    grades,
    messages,
    notices_qna,
    quiz,
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
