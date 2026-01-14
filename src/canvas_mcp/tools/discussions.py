"""Discussion and announcement MCP tools for Canvas API (student-focused)."""

import re

from mcp.server.fastmcp import FastMCP

from ..core.cache import get_course_code, get_course_id
from ..core.client import fetch_all_paginated_results, make_canvas_request
from ..core.dates import format_date, truncate_text
from ..core.logging import log_error, log_warning
from ..core.validation import validate_params


def register_discussion_tools(mcp: FastMCP):
    """Register student-focused discussion and announcement MCP tools."""

    @mcp.tool()
    @validate_params
    async def list_discussion_topics(course_identifier: str | int,
                                   include_announcements: bool = False) -> str:
        """List discussion topics for a course.

        Args:
            course_identifier: Course code (e.g., CS_101_Fall2024) or Canvas ID
            include_announcements: Include announcements in list (default: False)
        """
        course_id = await get_course_id(course_identifier)

        params = {"per_page": 100}
        if include_announcements:
            params["include[]"] = ["announcement"]

        topics = await fetch_all_paginated_results(f"/courses/{course_id}/discussion_topics", params)

        if isinstance(topics, dict) and "error" in topics:
            return f"Error fetching discussion topics: {topics['error']}"

        if not topics:
            return f"No discussion topics found for course {course_identifier}."

        topics_info = []
        for topic in topics:
            topic_id = topic.get("id")
            title = topic.get("title", "Untitled topic")
            is_announcement = topic.get("is_announcement", False)
            posted_at = format_date(topic.get("posted_at"))

            topic_type = "Announcement" if is_announcement else "Discussion"
            topics_info.append(f"• {title}\n  ID: {topic_id} | Type: {topic_type} | Posted: {posted_at}")

        course_display = await get_course_code(course_id) or course_identifier
        return f"Discussion Topics for {course_display}:\n\n" + "\n\n".join(topics_info)

    @mcp.tool()
    @validate_params
    async def get_discussion_topic_details(course_identifier: str | int,
                                         topic_id: str | int) -> str:
        """Get details about a specific discussion topic.

        Args:
            course_identifier: Course code or Canvas ID
            topic_id: The discussion topic ID
        """
        course_id = await get_course_id(course_identifier)

        response = await make_canvas_request(
            "get", f"/courses/{course_id}/discussion_topics/{topic_id}"
        )

        if "error" in response:
            return f"Error fetching discussion topic: {response['error']}"

        title = response.get("title", "Untitled")
        message = response.get("message", "")
        is_announcement = response.get("is_announcement", False)
        author = response.get("author", {})
        author_name = author.get("display_name", "Unknown author")
        created_at = format_date(response.get("created_at"))
        posted_at = format_date(response.get("posted_at"))
        entries_count = response.get("discussion_entries_count", 0)
        unread_count = response.get("unread_count", 0)
        locked = response.get("locked", False)
        require_initial_post = response.get("require_initial_post", False)

        course_display = await get_course_code(course_id) or course_identifier
        topic_type = "Announcement" if is_announcement else "Discussion"

        result = f"{topic_type}: {title}\n"
        result += f"Course: {course_display}\n"
        result += f"ID: {topic_id}\n"
        result += f"Author: {author_name}\n"
        result += f"Posted: {posted_at}\n"
        result += f"Entries: {entries_count}"
        if unread_count > 0:
            result += f" ({unread_count} unread)"
        result += "\n"

        if locked:
            result += "Status: Locked\n"
        if require_initial_post:
            result += "Note: You must post before seeing other replies\n"

        if message:
            # Clean HTML from message
            clean_message = re.sub(r'<[^>]+>', '', message).strip()
            result += f"\nContent:\n{clean_message}"

        return result

    @mcp.tool()
    @validate_params
    async def list_discussion_entries(course_identifier: str | int,
                                    topic_id: str | int,
                                    include_full_content: bool = False) -> str:
        """List posts in a discussion topic.

        Args:
            course_identifier: Course code or Canvas ID
            topic_id: The discussion topic ID
            include_full_content: Show full post content (default: False, shows preview)
        """
        course_id = await get_course_id(course_identifier)

        entries = await fetch_all_paginated_results(
            f"/courses/{course_id}/discussion_topics/{topic_id}/entries",
            {"per_page": 100}
        )

        if isinstance(entries, dict) and "error" in entries:
            return f"Error fetching discussion entries: {entries['error']}"

        if not entries:
            return f"No posts found in this discussion."

        # Get topic title for context
        topic_response = await make_canvas_request(
            "get", f"/courses/{course_id}/discussion_topics/{topic_id}"
        )
        topic_title = topic_response.get("title", "Unknown Topic") if "error" not in topic_response else "Unknown Topic"

        course_display = await get_course_code(course_id) or course_identifier
        entries_info = []

        for entry in entries:
            entry_id = entry.get("id")
            user_name = entry.get("user_name", "Unknown user")
            created_at = format_date(entry.get("created_at"))
            message = entry.get("message", "")

            # Clean and format message
            if message:
                clean_msg = re.sub(r'<[^>]+>', '', message).strip()
                if not include_full_content and len(clean_msg) > 200:
                    clean_msg = clean_msg[:200] + "..."
            else:
                clean_msg = "[No content]"

            # Reply count
            recent_replies = entry.get("recent_replies", [])
            has_more = entry.get("has_more_replies", False)
            reply_text = f"{len(recent_replies)}{'+ more' if has_more else ''} replies" if recent_replies else "No replies"

            entries_info.append(
                f"• {user_name} ({created_at})\n"
                f"  ID: {entry_id} | {reply_text}\n"
                f"  {clean_msg}"
            )

        result = f"Posts in '{topic_title}' ({course_display}):\n\n" + "\n\n".join(entries_info)

        if not include_full_content:
            result += "\n\nTip: Use include_full_content=True for complete posts"

        return result

    @mcp.tool()
    @validate_params
    async def get_discussion_entry_details(course_identifier: str | int,
                                         topic_id: str | int,
                                         entry_id: str | int,
                                         include_replies: bool = True) -> str:
        """Get a specific discussion post with its replies.

        Args:
            course_identifier: Course code or Canvas ID
            topic_id: The discussion topic ID
            entry_id: The specific post ID
            include_replies: Include replies (default: True)
        """
        course_id = await get_course_id(course_identifier)

        # Try discussion view first (most complete data)
        entry_response = None
        replies = []

        try:
            view_response = await make_canvas_request(
                "get", f"/courses/{course_id}/discussion_topics/{topic_id}/view"
            )

            if "error" not in view_response and "view" in view_response:
                for entry in view_response.get("view", []):
                    if str(entry.get("id")) == str(entry_id):
                        entry_response = entry
                        if include_replies:
                            replies = entry.get("replies", [])
                        break
        except Exception as e:
            log_warning("Failed to fetch discussion view", exc=e)

        # Fallback to entry list
        if not entry_response:
            try:
                entry_list = await make_canvas_request(
                    "get", f"/courses/{course_id}/discussion_topics/{topic_id}/entry_list",
                    params={"ids[]": entry_id}
                )
                if "error" not in entry_list and isinstance(entry_list, list) and entry_list:
                    entry_response = entry_list[0]
            except Exception as e:
                log_warning("Failed to fetch entry list", exc=e)

        if not entry_response:
            return f"Could not find post {entry_id} in discussion {topic_id}."

        # Fetch replies if needed
        if include_replies and not replies:
            try:
                replies_response = await fetch_all_paginated_results(
                    f"/courses/{course_id}/discussion_topics/{topic_id}/entries/{entry_id}/replies",
                    {"per_page": 100}
                )
                if not isinstance(replies_response, dict) or "error" not in replies_response:
                    replies = replies_response
            except Exception as e:
                log_warning("Failed to fetch replies", exc=e)

        # Get topic title
        topic_response = await make_canvas_request(
            "get", f"/courses/{course_id}/discussion_topics/{topic_id}"
        )
        topic_title = topic_response.get("title", "Unknown Topic") if "error" not in topic_response else "Unknown Topic"

        # Format output
        course_display = await get_course_code(course_id) or course_identifier
        user_name = entry_response.get("user_name", "Unknown user")
        message = entry_response.get("message", "")
        created_at = format_date(entry_response.get("created_at"))

        result = f"Discussion Post in '{topic_title}' ({course_display}):\n\n"
        result += f"Author: {user_name}\n"
        result += f"Posted: {created_at}\n"
        result += f"Post ID: {entry_id}\n\n"
        result += f"Content:\n{message}\n"

        if include_replies and replies:
            result += f"\nReplies ({len(replies)}):\n" + "=" * 40 + "\n"
            for i, reply in enumerate(replies, 1):
                reply_user = reply.get("user_name", "Unknown")
                reply_msg = reply.get("message", "")
                reply_created = format_date(reply.get("created_at"))
                result += f"\n{i}. {reply_user} ({reply_created}):\n{reply_msg}\n"
        elif include_replies:
            result += "\nNo replies yet."

        return result

    @mcp.tool()
    @validate_params
    async def post_discussion_entry(course_identifier: str | int,
                                  topic_id: str | int,
                                  message: str) -> str:
        """Post a new entry to a discussion topic.

        Args:
            course_identifier: Course code or Canvas ID
            topic_id: The discussion topic ID
            message: Your post content
        """
        course_id = await get_course_id(course_identifier)

        response = await make_canvas_request(
            "post", f"/courses/{course_id}/discussion_topics/{topic_id}/entries",
            data={"message": message}
        )

        if "error" in response:
            return f"Error posting: {response['error']}"

        # Get topic title for confirmation
        topic_response = await make_canvas_request(
            "get", f"/courses/{course_id}/discussion_topics/{topic_id}"
        )
        topic_title = topic_response.get("title", "Unknown Topic") if "error" not in topic_response else "Unknown Topic"

        entry_id = response.get("id")
        created_at = format_date(response.get("created_at"))
        course_display = await get_course_code(course_id) or course_identifier

        return (
            f"Posted successfully!\n\n"
            f"Discussion: {topic_title}\n"
            f"Course: {course_display}\n"
            f"Post ID: {entry_id}\n"
            f"Posted: {created_at}\n\n"
            f"Your post:\n{truncate_text(message, 200)}"
        )

    @mcp.tool()
    @validate_params
    async def reply_to_discussion_entry(course_identifier: str | int,
                                      topic_id: str | int,
                                      entry_id: str | int,
                                      message: str) -> str:
        """Reply to a discussion post.

        Args:
            course_identifier: Course code or Canvas ID
            topic_id: The discussion topic ID
            entry_id: The post ID to reply to
            message: Your reply content
        """
        course_id = await get_course_id(course_identifier)

        response = await make_canvas_request(
            "post",
            f"/courses/{course_id}/discussion_topics/{topic_id}/entries/{entry_id}/replies",
            data={"message": message}
        )

        if "error" in response:
            return f"Error posting reply: {response['error']}"

        reply_id = response.get("id")
        course_display = await get_course_code(course_id) or course_identifier

        return (
            f"Reply posted successfully!\n\n"
            f"Course: {course_display}\n"
            f"Topic ID: {topic_id}\n"
            f"Original Post ID: {entry_id}\n"
            f"Your Reply ID: {reply_id}\n\n"
            f"Your reply:\n{truncate_text(message, 200)}"
        )

    @mcp.tool()
    async def list_announcements(course_identifier: str) -> str:
        """List announcements for a course.

        Args:
            course_identifier: Course code or Canvas ID
        """
        course_id = await get_course_id(course_identifier)

        params = {
            "only_announcements": True,
            "per_page": 100
        }

        announcements = await fetch_all_paginated_results(f"/courses/{course_id}/discussion_topics", params)

        if isinstance(announcements, dict) and "error" in announcements:
            return f"Error fetching announcements: {announcements['error']}"

        if not announcements:
            return f"No announcements found."

        announcements_info = []
        for ann in announcements:
            ann_id = ann.get("id")
            title = ann.get("title", "Untitled")
            posted_at = format_date(ann.get("posted_at"))
            message = ann.get("message", "")

            # Preview of message
            if message:
                preview = re.sub(r'<[^>]+>', '', message).strip()
                if len(preview) > 100:
                    preview = preview[:100] + "..."
            else:
                preview = "[No content]"

            announcements_info.append(
                f"• {title}\n"
                f"  ID: {ann_id} | Posted: {posted_at}\n"
                f"  {preview}"
            )

        course_display = await get_course_code(course_id) or course_identifier
        return f"Announcements for {course_display}:\n\n" + "\n\n".join(announcements_info)
