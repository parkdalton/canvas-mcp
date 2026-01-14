"""Tool modules for Canvas MCP server (student-focused)."""

from .courses import register_course_tools
from .assignments import register_assignment_tools
from .discussions import register_discussion_tools
from .other_tools import register_other_tools
from .student_tools import register_student_tools
from .discovery import register_discovery_tools
from .code_execution import register_code_execution_tools
from .files import register_file_tools
from .quizzes import register_quiz_tools

__all__ = [
    'register_course_tools',
    'register_assignment_tools',
    'register_discussion_tools',
    'register_other_tools',
    'register_student_tools',
    'register_discovery_tools',
    'register_code_execution_tools',
    'register_file_tools',
    'register_quiz_tools'
]
