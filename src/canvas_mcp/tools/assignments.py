"""Assignment MCP tools for Canvas API (student-focused)."""

import re

from mcp.server.fastmcp import FastMCP

from ..core.cache import get_course_code, get_course_id
from ..core.client import fetch_all_paginated_results, make_canvas_request
from ..core.dates import format_date
from ..core.validation import validate_params


def register_assignment_tools(mcp: FastMCP):
    """Register student-focused assignment tools."""

    @mcp.tool()
    @validate_params
    async def list_assignments(course_identifier: str | int) -> str:
        """List assignments in a course.

        Args:
            course_identifier: Course code or Canvas ID
        """
        course_id = await get_course_id(course_identifier)

        params = {
            "per_page": 100,
            "include[]": ["submission"],
            "order_by": "due_at"
        }

        assignments = await fetch_all_paginated_results(f"/courses/{course_id}/assignments", params)

        if isinstance(assignments, dict) and "error" in assignments:
            return f"Error fetching assignments: {assignments['error']}"

        if not assignments:
            return f"No assignments found."

        assignments_info = []
        for a in assignments:
            name = a.get("name", "Unnamed")
            assignment_id = a.get("id")
            due_at = format_date(a.get("due_at"))
            points = a.get("points_possible", 0)

            # Check submission status
            submission = a.get("submission", {})
            if submission:
                submitted = submission.get("submitted_at") is not None
                score = submission.get("score")
                status = "Submitted" if submitted else "Not submitted"
                if score is not None:
                    status = f"Graded: {score}/{points}"
            else:
                status = "Not submitted"

            assignments_info.append(
                f"• {name}\n"
                f"  ID: {assignment_id} | Due: {due_at} | Points: {points}\n"
                f"  Status: {status}"
            )

        course_display = await get_course_code(course_id) or course_identifier
        return f"Assignments in {course_display}:\n\n" + "\n\n".join(assignments_info)

    @mcp.tool()
    @validate_params
    async def get_assignment_details(course_identifier: str | int, assignment_id: str | int) -> str:
        """Get details about a specific assignment.

        Args:
            course_identifier: Course code or Canvas ID
            assignment_id: The assignment ID
        """
        course_id = await get_course_id(course_identifier)

        response = await make_canvas_request(
            "get",
            f"/courses/{course_id}/assignments/{assignment_id}",
            params={"include[]": ["submission"]}
        )

        if "error" in response:
            return f"Error fetching assignment: {response['error']}"

        name = response.get("name", "Unnamed")
        description = response.get("description", "")
        due_at = format_date(response.get("due_at"))
        points = response.get("points_possible", 0)
        submission_types = ", ".join(response.get("submission_types", ["none"]))
        locked = response.get("locked_for_user", False)

        # Clean HTML from description
        if description:
            description = re.sub(r'<[^>]+>', '', description).strip()
            if len(description) > 500:
                description = description[:500] + "..."

        # Check your submission status
        submission = response.get("submission", {})
        if submission:
            submitted = submission.get("submitted_at") is not None
            score = submission.get("score")
            submitted_at = format_date(submission.get("submitted_at"))

            if score is not None:
                submission_status = f"Graded: {score}/{points}"
            elif submitted:
                submission_status = f"Submitted on {submitted_at}"
            else:
                submission_status = "Not submitted"
        else:
            submission_status = "Not submitted"

        course_display = await get_course_code(course_id) or course_identifier

        result = f"Assignment: {name}\n"
        result += f"Course: {course_display}\n"
        result += f"ID: {assignment_id}\n"
        result += f"Due: {due_at}\n"
        result += f"Points: {points}\n"
        result += f"Submission Types: {submission_types}\n"
        result += f"Your Status: {submission_status}\n"

        if locked:
            result += "Note: This assignment is currently locked.\n"

        if description:
            result += f"\nDescription:\n{description}"

        return result
