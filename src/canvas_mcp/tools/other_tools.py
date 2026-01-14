"""Other MCP tools for Canvas API (pages, modules, groups) - student-focused."""

import re

from mcp.server.fastmcp import FastMCP

from ..core.cache import get_course_code, get_course_id
from ..core.client import fetch_all_paginated_results, make_canvas_request
from ..core.dates import format_date
from ..core.validation import validate_params


def register_other_tools(mcp: FastMCP):
    """Register student-focused page, module, and group tools."""

    @mcp.tool()
    @validate_params
    async def list_pages(course_identifier: str | int,
                        search_term: str | None = None) -> str:
        """List pages in a course.

        Args:
            course_identifier: Course code or Canvas ID
            search_term: Optional search term to filter pages
        """
        course_id = await get_course_id(course_identifier)

        params = {"per_page": 100, "sort": "title", "order": "asc"}
        if search_term:
            params["search_term"] = search_term

        pages = await fetch_all_paginated_results(f"/courses/{course_id}/pages", params)

        if isinstance(pages, dict) and "error" in pages:
            return f"Error fetching pages: {pages['error']}"

        if not pages:
            return f"No pages found."

        pages_info = []
        for page in pages:
            url = page.get("url", "")
            title = page.get("title", "Untitled")
            updated_at = format_date(page.get("updated_at"))
            is_front = " (Front Page)" if page.get("front_page", False) else ""

            pages_info.append(f"• {title}{is_front}\n  URL: {url} | Updated: {updated_at}")

        course_display = await get_course_code(course_id) or course_identifier
        return f"Pages in {course_display}:\n\n" + "\n\n".join(pages_info)

    @mcp.tool()
    @validate_params
    async def get_page_content(course_identifier: str | int, page_url: str) -> str:
        """Get the content of a specific page.

        Args:
            course_identifier: Course code or Canvas ID
            page_url: The page URL (from list_pages)
        """
        course_id = await get_course_id(course_identifier)

        response = await make_canvas_request("get", f"/courses/{course_id}/pages/{page_url}")

        if "error" in response:
            return f"Error fetching page: {response['error']}"

        title = response.get("title", "Untitled")
        body = response.get("body", "")
        updated_at = format_date(response.get("updated_at"))

        if not body:
            return f"Page '{title}' has no content."

        # Clean HTML for readability
        clean_body = re.sub(r'<[^>]+>', '', body).strip()

        course_display = await get_course_code(course_id) or course_identifier
        return f"Page: {title}\nCourse: {course_display}\nUpdated: {updated_at}\n\n{clean_body}"

    @mcp.tool()
    @validate_params
    async def get_front_page(course_identifier: str | int) -> str:
        """Get the course front/home page content.

        Args:
            course_identifier: Course code or Canvas ID
        """
        course_id = await get_course_id(course_identifier)

        response = await make_canvas_request("get", f"/courses/{course_id}/front_page")

        if "error" in response:
            return f"Error fetching front page: {response['error']}"

        title = response.get("title", "Untitled")
        body = response.get("body", "")
        updated_at = format_date(response.get("updated_at"))

        if not body:
            return f"Front page '{title}' has no content."

        # Clean HTML
        clean_body = re.sub(r'<[^>]+>', '', body).strip()

        course_display = await get_course_code(course_id) or course_identifier
        return f"Front Page: {title}\nCourse: {course_display}\nUpdated: {updated_at}\n\n{clean_body}"

    @mcp.tool()
    @validate_params
    async def list_modules(course_identifier: str | int) -> str:
        """List modules in a course.

        Args:
            course_identifier: Course code or Canvas ID
        """
        course_id = await get_course_id(course_identifier)

        modules = await fetch_all_paginated_results(
            f"/courses/{course_id}/modules", {"per_page": 100}
        )

        if isinstance(modules, dict) and "error" in modules:
            return f"Error fetching modules: {modules['error']}"

        if not modules:
            return f"No modules found."

        modules_info = []
        for mod in modules:
            mod_id = mod.get("id")
            name = mod.get("name", "Unnamed")
            items_count = mod.get("items_count", 0)
            state = mod.get("state", "unknown")

            modules_info.append(f"• {name}\n  ID: {mod_id} | Items: {items_count} | State: {state}")

        course_display = await get_course_code(course_id) or course_identifier
        return f"Modules in {course_display}:\n\n" + "\n\n".join(modules_info)

    @mcp.tool()
    @validate_params
    async def list_module_items(course_identifier: str | int, module_id: str | int) -> str:
        """List items in a specific module.

        Args:
            course_identifier: Course code or Canvas ID
            module_id: The module ID (from list_modules)
        """
        course_id = await get_course_id(course_identifier)

        items = await fetch_all_paginated_results(
            f"/courses/{course_id}/modules/{module_id}/items",
            {"per_page": 100, "include[]": ["content_details"]}
        )

        if isinstance(items, dict) and "error" in items:
            return f"Error fetching module items: {items['error']}"

        if not items:
            return f"No items in this module."

        # Get module name
        mod_response = await make_canvas_request("get", f"/courses/{course_id}/modules/{module_id}")
        module_name = mod_response.get("name", "Unknown Module") if "error" not in mod_response else "Unknown Module"

        items_info = []
        for item in items:
            title = item.get("title", "Untitled")
            item_type = item.get("type", "Unknown")
            url = item.get("html_url", "")

            items_info.append(f"• {title}\n  Type: {item_type}")
            if url:
                items_info[-1] += f" | URL: {url}"

        course_display = await get_course_code(course_id) or course_identifier
        return f"Items in '{module_name}' ({course_display}):\n\n" + "\n\n".join(items_info)

    @mcp.tool()
    @validate_params
    async def list_groups(course_identifier: str | int) -> str:
        """List groups in a course.

        Args:
            course_identifier: Course code or Canvas ID
        """
        course_id = await get_course_id(course_identifier)

        groups = await fetch_all_paginated_results(
            f"/courses/{course_id}/groups", {"per_page": 100}
        )

        if isinstance(groups, dict) and "error" in groups:
            return f"Error fetching groups: {groups['error']}"

        if not groups:
            return f"No groups found."

        groups_info = []
        for group in groups:
            group_id = group.get("id")
            name = group.get("name", "Unnamed")
            member_count = group.get("members_count", 0)

            groups_info.append(f"• {name}\n  ID: {group_id} | Members: {member_count}")

        course_display = await get_course_code(course_id) or course_identifier
        return f"Groups in {course_display}:\n\n" + "\n\n".join(groups_info)
