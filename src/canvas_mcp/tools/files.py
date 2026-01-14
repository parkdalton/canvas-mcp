"""File-related MCP tools for Canvas API."""

import os
from typing import Optional

from mcp.server.fastmcp import FastMCP

from ..core.cache import get_course_code, get_course_id
from ..core.client import fetch_all_paginated_results, make_canvas_request
from ..core.dates import format_date
from ..core.validation import validate_params


def register_file_tools(mcp: FastMCP) -> None:
    """Register all file-related MCP tools."""

    @mcp.tool()
    @validate_params
    async def list_course_files(
        course_identifier: str | int,
        search_term: Optional[str] = None,
        content_types: Optional[str] = None,
        sort: str = "name",
        order: str = "asc"
    ) -> str:
        """List files in a course.

        Args:
            course_identifier: The Canvas course code or ID
            search_term: Optional search term to filter files by name
            content_types: Optional comma-separated content types (e.g., "application/pdf,image/png")
            sort: Sort by: name, size, created_at, updated_at, content_type (default: name)
            order: Sort order: asc or desc (default: asc)
        """
        course_id = await get_course_id(course_identifier)

        params = {
            "per_page": 100,
            "sort": sort,
            "order": order
        }

        if search_term:
            params["search_term"] = search_term

        if content_types:
            params["content_types[]"] = content_types.split(",")

        files = await fetch_all_paginated_results(f"/courses/{course_id}/files", params)

        if isinstance(files, dict) and "error" in files:
            return f"Error fetching files: {files['error']}"

        if not files:
            return "No files found in this course."

        course_display = await get_course_code(course_id) or course_identifier

        files_info = []
        for f in files:
            file_id = f.get("id")
            name = f.get("display_name", f.get("filename", "Unknown"))
            size_bytes = f.get("size", 0)
            size_display = _format_file_size(size_bytes)
            content_type = f.get("content-type", "unknown")
            updated = format_date(f.get("updated_at"))
            folder_id = f.get("folder_id", "root")

            files_info.append(
                f"• {name}\n"
                f"  ID: {file_id} | Size: {size_display} | Type: {content_type}\n"
                f"  Updated: {updated} | Folder ID: {folder_id}"
            )

        return f"Files in {course_display} ({len(files)} files):\n\n" + "\n\n".join(files_info)

    @mcp.tool()
    @validate_params
    async def list_course_folders(
        course_identifier: str | int
    ) -> str:
        """List folders in a course to understand file organization.

        Args:
            course_identifier: The Canvas course code or ID
        """
        course_id = await get_course_id(course_identifier)

        folders = await fetch_all_paginated_results(f"/courses/{course_id}/folders", {"per_page": 100})

        if isinstance(folders, dict) and "error" in folders:
            return f"Error fetching folders: {folders['error']}"

        if not folders:
            return "No folders found in this course."

        course_display = await get_course_code(course_id) or course_identifier

        # Build folder tree structure
        folder_map = {f.get("id"): f for f in folders}

        folders_info = []
        for folder in sorted(folders, key=lambda x: x.get("full_name", "")):
            folder_id = folder.get("id")
            name = folder.get("name", "Unknown")
            full_name = folder.get("full_name", name)
            files_count = folder.get("files_count", 0)
            folders_count = folder.get("folders_count", 0)

            folders_info.append(
                f"• {full_name}\n"
                f"  ID: {folder_id} | Files: {files_count} | Subfolders: {folders_count}"
            )

        return f"Folders in {course_display} ({len(folders)} folders):\n\n" + "\n\n".join(folders_info)

    @mcp.tool()
    @validate_params
    async def get_file_download_url(
        file_id: int | str
    ) -> str:
        """Get the download URL for a specific file.

        Args:
            file_id: The Canvas file ID
        """
        response = await make_canvas_request("get", f"/files/{file_id}")

        if "error" in response:
            return f"Error fetching file: {response['error']}"

        name = response.get("display_name", response.get("filename", "Unknown"))
        size_display = _format_file_size(response.get("size", 0))
        content_type = response.get("content-type", "unknown")
        url = response.get("url", "")

        if not url:
            return f"No download URL available for file: {name}"

        return (
            f"File: {name}\n"
            f"Size: {size_display}\n"
            f"Type: {content_type}\n"
            f"Download URL: {url}\n\n"
            f"Note: This URL is time-limited and authenticated. Use it promptly."
        )

    @mcp.tool()
    @validate_params
    async def download_file(
        file_id: int | str,
        destination_folder: str = "~/Downloads"
    ) -> str:
        """Download a file from Canvas to your local machine.

        ⚠️ RATE LIMIT WARNING: Do not use this tool in rapid succession.
        Download files one at a time with pauses between downloads.
        For bulk downloads, consider using the Canvas web interface instead.

        Args:
            file_id: The Canvas file ID
            destination_folder: Local folder to save the file (default: ~/Downloads)
        """
        import httpx

        # Get file details first
        response = await make_canvas_request("get", f"/files/{file_id}")

        if "error" in response:
            return f"Error fetching file details: {response['error']}"

        name = response.get("display_name", response.get("filename", f"file_{file_id}"))
        url = response.get("url", "")
        size_bytes = response.get("size", 0)

        if not url:
            return f"No download URL available for file: {name}"

        # Expand user path and create destination
        dest_folder = os.path.expanduser(destination_folder)
        if not os.path.exists(dest_folder):
            os.makedirs(dest_folder)

        dest_path = os.path.join(dest_folder, name)

        # Handle duplicate filenames
        if os.path.exists(dest_path):
            base, ext = os.path.splitext(name)
            counter = 1
            while os.path.exists(dest_path):
                dest_path = os.path.join(dest_folder, f"{base}_{counter}{ext}")
                counter += 1

        try:
            # Download the file
            async with httpx.AsyncClient(follow_redirects=True, timeout=120.0) as client:
                response = await client.get(url)
                response.raise_for_status()

                with open(dest_path, "wb") as f:
                    f.write(response.content)

            actual_size = os.path.getsize(dest_path)
            return (
                f"✓ Downloaded successfully!\n"
                f"File: {name}\n"
                f"Size: {_format_file_size(actual_size)}\n"
                f"Saved to: {dest_path}"
            )

        except httpx.HTTPStatusError as e:
            return f"Download failed with HTTP error: {e.response.status_code}"
        except Exception as e:
            return f"Download failed: {str(e)}"

    @mcp.tool()
    @validate_params
    async def list_folder_files(
        folder_id: int | str,
        sort: str = "name",
        order: str = "asc"
    ) -> str:
        """List files in a specific folder.

        Args:
            folder_id: The Canvas folder ID
            sort: Sort by: name, size, created_at, updated_at, content_type (default: name)
            order: Sort order: asc or desc (default: asc)
        """
        params = {
            "per_page": 100,
            "sort": sort,
            "order": order
        }

        files = await fetch_all_paginated_results(f"/folders/{folder_id}/files", params)

        if isinstance(files, dict) and "error" in files:
            return f"Error fetching folder files: {files['error']}"

        if not files:
            return "No files found in this folder."

        # Get folder info
        folder_response = await make_canvas_request("get", f"/folders/{folder_id}")
        folder_name = folder_response.get("full_name", f"Folder {folder_id}")

        files_info = []
        for f in files:
            file_id = f.get("id")
            name = f.get("display_name", f.get("filename", "Unknown"))
            size_display = _format_file_size(f.get("size", 0))
            content_type = f.get("content-type", "unknown")
            updated = format_date(f.get("updated_at"))

            files_info.append(
                f"• {name}\n"
                f"  ID: {file_id} | Size: {size_display} | Type: {content_type}\n"
                f"  Updated: {updated}"
            )

        return f"Files in {folder_name} ({len(files)} files):\n\n" + "\n\n".join(files_info)


def _format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    if size_bytes == 0:
        return "0 B"

    units = ["B", "KB", "MB", "GB"]
    unit_index = 0
    size = float(size_bytes)

    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1

    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    return f"{size:.1f} {units[unit_index]}"
