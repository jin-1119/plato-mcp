from . import (
    assignments,
    calendar,
    completion,
    courses,
    dashboard,
    downloads,
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
