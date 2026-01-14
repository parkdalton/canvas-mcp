"""Quiz MCP tools for Canvas API (student-focused)."""

import json
import re
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..core.cache import get_course_code, get_course_id
from ..core.client import fetch_all_paginated_results, make_canvas_request
from ..core.dates import format_date
from ..core.validation import validate_params


def strip_html_tags(html_content: str) -> str:
    """Remove HTML tags and clean up text content."""
    if not html_content:
        return ""
    clean_text = re.sub(r'<[^>]+>', '', html_content)
    clean_text = clean_text.replace('&nbsp;', ' ')
    clean_text = clean_text.replace('&amp;', '&')
    clean_text = clean_text.replace('&lt;', '<')
    clean_text = clean_text.replace('&gt;', '>')
    clean_text = clean_text.replace('&quot;', '"')
    clean_text = re.sub(r'\s+', ' ', clean_text)
    return clean_text.strip()


def register_quiz_tools(mcp: FastMCP):
    """Register quiz-related MCP tools."""

    @mcp.tool()
    @validate_params
    async def list_quizzes(course_identifier: str | int) -> str:
        """List all quizzes in a course.

        Args:
            course_identifier: Course code or Canvas ID
        """
        course_id = await get_course_id(course_identifier)

        params = {"per_page": 100}
        quizzes = await fetch_all_paginated_results(f"/courses/{course_id}/quizzes", params)

        if isinstance(quizzes, dict) and "error" in quizzes:
            return f"Error fetching quizzes: {quizzes['error']}"

        if not quizzes:
            return "No quizzes found in this course."

        quiz_info = []
        for q in quizzes:
            quiz_id = q.get("id")
            title = q.get("title", "Untitled")
            due_at = format_date(q.get("due_at"))
            time_limit = q.get("time_limit")
            allowed_attempts = q.get("allowed_attempts", 1)
            question_count = q.get("question_count", 0)
            points = q.get("points_possible", 0)

            # Format time limit
            time_str = f"{time_limit} min" if time_limit else "No limit"

            # Format attempts
            if allowed_attempts == -1:
                attempts_str = "Unlimited"
            else:
                attempts_str = str(allowed_attempts)

            # Check if quiz can be started via API
            can_start_api = time_limit is None or allowed_attempts == -1
            api_note = " [API start OK]" if can_start_api else ""

            quiz_info.append(
                f"• {title}{api_note}\n"
                f"  ID: {quiz_id} | Due: {due_at}\n"
                f"  Questions: {question_count} | Points: {points}\n"
                f"  Time: {time_str} | Attempts: {attempts_str}"
            )

        course_display = await get_course_code(course_id) or course_identifier
        return f"Quizzes in {course_display}:\n\n" + "\n\n".join(quiz_info)

    @mcp.tool()
    @validate_params
    async def get_quiz_details(course_identifier: str | int, quiz_id: str | int) -> str:
        """Get detailed information about a specific quiz.

        Args:
            course_identifier: Course code or Canvas ID
            quiz_id: The quiz ID
        """
        course_id = await get_course_id(course_identifier)

        response = await make_canvas_request("get", f"/courses/{course_id}/quizzes/{quiz_id}")

        if "error" in response:
            return f"Error fetching quiz: {response['error']}"

        title = response.get("title", "Untitled")
        description = strip_html_tags(response.get("description", ""))
        due_at = format_date(response.get("due_at"))
        unlock_at = format_date(response.get("unlock_at"))
        lock_at = format_date(response.get("lock_at"))
        time_limit = response.get("time_limit")
        allowed_attempts = response.get("allowed_attempts", 1)
        question_count = response.get("question_count", 0)
        points = response.get("points_possible", 0)
        scoring_policy = response.get("scoring_policy", "keep_highest")
        shuffle_answers = response.get("shuffle_answers", False)
        one_question = response.get("one_question_at_a_time", False)
        cant_go_back = response.get("cant_go_back", False)
        access_code = response.get("access_code")
        ip_filter = response.get("ip_filter")

        # Format time limit
        time_str = f"{time_limit} minutes" if time_limit else "No time limit"

        # Format attempts
        if allowed_attempts == -1:
            attempts_str = "Unlimited"
        else:
            attempts_str = str(allowed_attempts)

        # Check API start eligibility
        can_start_api = time_limit is None or allowed_attempts == -1

        course_display = await get_course_code(course_id) or course_identifier

        result = f"Quiz: {title}\n"
        result += f"Course: {course_display}\n"
        result += f"ID: {quiz_id}\n"
        result += f"\nTiming:\n"
        result += f"  Due: {due_at}\n"
        result += f"  Available: {unlock_at} - {lock_at}\n"
        result += f"  Time Limit: {time_str}\n"
        result += f"\nAttempts:\n"
        result += f"  Allowed: {attempts_str}\n"
        result += f"  Scoring: {scoring_policy}\n"
        result += f"\nQuestions:\n"
        result += f"  Count: {question_count}\n"
        result += f"  Points: {points}\n"
        result += f"  Shuffle Answers: {shuffle_answers}\n"
        result += f"  One at a Time: {one_question}\n"
        result += f"  Can Go Back: {not cant_go_back}\n"

        if access_code:
            result += f"\nAccess Code Required: Yes\n"
        if ip_filter:
            result += f"IP Restriction: {ip_filter}\n"

        result += f"\nAPI Start Allowed: {'Yes' if can_start_api else 'No (timed + limited attempts)'}\n"

        if description:
            if len(description) > 500:
                description = description[:500] + "..."
            result += f"\nDescription:\n{description}"

        return result

    @mcp.tool()
    @validate_params
    async def get_my_quiz_submissions(course_identifier: str | int, quiz_id: str | int) -> str:
        """Get your quiz submission history (attempts and scores).

        Args:
            course_identifier: Course code or Canvas ID
            quiz_id: The quiz ID
        """
        course_id = await get_course_id(course_identifier)

        response = await make_canvas_request(
            "get",
            f"/courses/{course_id}/quizzes/{quiz_id}/submissions",
            params={"include[]": ["submission"]}
        )

        if "error" in response:
            return f"Error fetching submissions: {response['error']}"

        submissions = response.get("quiz_submissions", [])

        if not submissions:
            return "No quiz attempts found."

        submission_info = []
        for sub in submissions:
            attempt = sub.get("attempt", 1)
            score = sub.get("score")
            kept_score = sub.get("kept_score")
            started_at = format_date(sub.get("started_at"))
            finished_at = format_date(sub.get("finished_at"))
            time_spent = sub.get("time_spent")  # in seconds
            workflow_state = sub.get("workflow_state", "unknown")
            submission_id = sub.get("id")
            validation_token = sub.get("validation_token")

            # Format time spent
            if time_spent:
                minutes = time_spent // 60
                seconds = time_spent % 60
                time_str = f"{minutes}m {seconds}s"
            else:
                time_str = "N/A"

            info = f"Attempt {attempt}:\n"
            info += f"  Submission ID: {submission_id}\n"
            info += f"  Status: {workflow_state}\n"
            info += f"  Started: {started_at}\n"
            info += f"  Finished: {finished_at}\n"
            info += f"  Time Spent: {time_str}\n"

            if score is not None:
                info += f"  Score: {score}\n"
            if kept_score is not None:
                info += f"  Kept Score: {kept_score}\n"

            # Include validation token if quiz is in progress
            if workflow_state in ["untaken", "pending_review", "settings_only"]:
                if validation_token:
                    info += f"  Validation Token: {validation_token}\n"

            submission_info.append(info)

        course_display = await get_course_code(course_id) or course_identifier
        return f"Your Quiz Submissions ({course_display}):\n\n" + "\n".join(submission_info)

    @mcp.tool()
    @validate_params
    async def start_quiz(course_identifier: str | int, quiz_id: str | int) -> str:
        """Start a quiz attempt. RESTRICTED: Only works if quiz has no time limit OR unlimited attempts.

        Args:
            course_identifier: Course code or Canvas ID
            quiz_id: The quiz ID to start

        Returns:
            Quiz submission details including submission_id, attempt number, and validation_token
            needed for answering questions. Returns error if quiz has both time limit AND limited attempts.
        """
        course_id = await get_course_id(course_identifier)

        # First, fetch quiz details to check restrictions
        quiz = await make_canvas_request("get", f"/courses/{course_id}/quizzes/{quiz_id}")

        if "error" in quiz:
            return f"Error fetching quiz: {quiz['error']}"

        time_limit = quiz.get("time_limit")  # None = no limit
        allowed_attempts = quiz.get("allowed_attempts", 1)  # -1 = unlimited
        title = quiz.get("title", "Untitled")

        # Check if we can start via API
        # Allow if: no time limit OR unlimited attempts
        if time_limit is not None and allowed_attempts != -1:
            return (
                f"Cannot start quiz '{title}' via API.\n"
                f"Reason: Quiz has BOTH a time limit ({time_limit} min) AND limited attempts ({allowed_attempts}).\n"
                f"Please take this quiz directly in Canvas to ensure proper timing."
            )

        # Start the quiz
        response = await make_canvas_request(
            "post",
            f"/courses/{course_id}/quizzes/{quiz_id}/submissions"
        )

        if "error" in response:
            return f"Error starting quiz: {response['error']}"

        # Extract the quiz submission from response
        submissions = response.get("quiz_submissions", [])
        if not submissions:
            return "Quiz started but no submission data returned."

        sub = submissions[0]
        submission_id = sub.get("id")
        attempt = sub.get("attempt", 1)
        validation_token = sub.get("validation_token")
        started_at = format_date(sub.get("started_at"))
        end_at = format_date(sub.get("end_at"))

        result = f"Quiz Started: {title}\n\n"
        result += f"IMPORTANT - Save these values for answering questions:\n"
        result += f"  Submission ID: {submission_id}\n"
        result += f"  Attempt: {attempt}\n"
        result += f"  Validation Token: {validation_token}\n"
        result += f"\nTiming:\n"
        result += f"  Started: {started_at}\n"
        if end_at:
            result += f"  Must Complete By: {end_at}\n"
        result += f"\nNext: Use get_quiz_questions({submission_id}) to see the questions."

        return result

    @mcp.tool()
    @validate_params
    async def get_quiz_questions(quiz_submission_id: str | int) -> str:
        """Get all questions for an active quiz attempt.

        Args:
            quiz_submission_id: The quiz submission ID (from start_quiz)

        Returns:
            All questions with their text, type, and answer options.
        """
        response = await make_canvas_request(
            "get",
            f"/quiz_submissions/{quiz_submission_id}/questions"
        )

        if "error" in response:
            return f"Error fetching questions: {response['error']}"

        questions = response.get("quiz_submission_questions", [])

        if not questions:
            return "No questions found for this submission."

        question_info = []
        for q in questions:
            q_id = q.get("id")
            q_type = q.get("question_type", "unknown")
            q_text = strip_html_tags(q.get("question_text", ""))
            q_name = q.get("question_name", "")
            points = q.get("points_possible", 0)
            answers = q.get("answers", [])
            flagged = q.get("flagged", False)

            info = f"Question {q_id}: {q_name}\n"
            info += f"  Type: {q_type}\n"
            info += f"  Points: {points}\n"
            if flagged:
                info += f"  [FLAGGED]\n"
            info += f"  Text: {q_text}\n"

            # Show answer options based on question type
            if answers and q_type in [
                "multiple_choice_question",
                "true_false_question",
                "multiple_answers_question"
            ]:
                info += "  Options:\n"
                for a in answers:
                    a_id = a.get("id")
                    a_text = strip_html_tags(a.get("text", a.get("html", "")))
                    info += f"    [{a_id}] {a_text}\n"

            elif q_type == "matching_question":
                info += "  Matches:\n"
                info += "  Left side (answer_id):\n"
                for a in answers:
                    a_id = a.get("id")
                    a_text = strip_html_tags(a.get("text", a.get("left", "")))
                    info += f"    [{a_id}] {a_text}\n"
                matches = q.get("matches", [])
                if matches:
                    info += "  Right side (match_id):\n"
                    for m in matches:
                        m_id = m.get("match_id")
                        m_text = strip_html_tags(m.get("text", ""))
                        info += f"    [{m_id}] {m_text}\n"

            elif q_type == "fill_in_multiple_blanks_question":
                info += "  Blanks to fill: "
                blank_ids = set()
                for a in answers:
                    blank_id = a.get("blank_id")
                    if blank_id:
                        blank_ids.add(blank_id)
                info += ", ".join(blank_ids) + "\n"

            elif q_type == "multiple_dropdowns_question":
                info += "  Dropdowns:\n"
                blanks = {}
                for a in answers:
                    blank_id = a.get("blank_id", "default")
                    if blank_id not in blanks:
                        blanks[blank_id] = []
                    blanks[blank_id].append((a.get("id"), strip_html_tags(a.get("text", ""))))
                for blank_id, options in blanks.items():
                    info += f"    {blank_id}:\n"
                    for opt_id, opt_text in options:
                        info += f"      [{opt_id}] {opt_text}\n"

            question_info.append(info)

        header = f"Quiz Questions (Submission {quiz_submission_id}):\n"
        header += f"Total: {len(questions)} questions\n"
        header += "=" * 50 + "\n\n"

        return header + "\n".join(question_info)

    @mcp.tool()
    @validate_params
    async def answer_quiz_question(
        quiz_submission_id: str | int,
        attempt: int,
        validation_token: str,
        question_id: int,
        answer: Any
    ) -> str:
        """Submit an answer to a quiz question.

        Args:
            quiz_submission_id: The quiz submission ID (from start_quiz)
            attempt: Current attempt number (from start_quiz)
            validation_token: Validation token (from start_quiz)
            question_id: The question ID to answer
            answer: The answer - format depends on question type:
                - Multiple choice/True-False: answer_id as integer (e.g., 1234)
                - Essay/Short answer: text as string
                - Fill in blank: text as string
                - Multiple answers: list of answer_ids (e.g., [1234, 5678])
                - Matching: list of dicts (e.g., [{"answer_id": 1, "match_id": 2}])
                - Multiple blanks: dict (e.g., {"blank1": "answer1"})
                - Multiple dropdowns: dict (e.g., {"dropdown1": 1234})
                - Numerical: number (e.g., 42 or 3.14)

        Returns:
            Confirmation of answer submission or error message.
        """
        # Build the payload
        payload = {
            "attempt": attempt,
            "validation_token": validation_token,
            "quiz_questions": [{
                "id": question_id,
                "answer": answer
            }]
        }

        response = await make_canvas_request(
            "post",
            f"/quiz_submissions/{quiz_submission_id}/questions",
            json=payload
        )

        if "error" in response:
            return f"Error submitting answer: {response['error']}"

        # Check if answer was recorded
        questions = response.get("quiz_submission_questions", [])
        for q in questions:
            if q.get("id") == question_id:
                return (
                    f"Answer submitted for question {question_id}.\n"
                    f"Your answer has been recorded.\n"
                    f"Note: Quiz will auto-submit when time expires or you submit in Canvas."
                )

        return f"Answer submitted for question {question_id}."
