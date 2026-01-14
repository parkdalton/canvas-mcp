# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Canvas MCP is a student-focused MCP server for Canvas LMS. It provides tools to track assignments, grades, due dates, discussions, and course content.

## Commands

```bash
# Install
python3 -m venv .venv && . .venv/bin/activate
pip install -e .

# Run server
canvas-mcp-server

# Test connection
canvas-mcp-server --test

# Run tests
pytest tests/

# Code quality
ruff check src/
black src/
```

## Architecture

### Structure
```
src/canvas_mcp/
├── server.py              # MCP server entry point
├── core/                  # Shared utilities
│   ├── client.py         # make_canvas_request(), pagination
│   ├── config.py         # Environment config
│   ├── validation.py     # @validate_params decorator
│   ├── cache.py          # Course code ↔ ID mapping
│   └── dates.py          # Date formatting
├── tools/                 # MCP tool implementations
│   ├── student_tools.py  # Personal: grades, todos, due dates
│   ├── courses.py        # Course info, syllabus
│   ├── assignments.py    # Assignment details
│   ├── discussions.py    # Discussions, announcements
│   ├── other_tools.py    # Pages, modules, groups
│   ├── files.py          # File browsing/download
│   ├── code_execution.py # TypeScript execution
│   └── discovery.py      # Tool search
└── resources/            # MCP resources/prompts
```

### Key Patterns

**Tool registration:**
```python
def register_my_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    @validate_params
    async def my_tool(course_identifier: str | int) -> str:
        course_id = await get_course_id(course_identifier)
        response = await make_canvas_request("get", f"/courses/{course_id}/...")
        return json.dumps(response)
```

**Course identifiers:** Always use `get_course_id()` to resolve course codes → Canvas IDs.

**API calls:** All requests go through `make_canvas_request()` which handles pagination, rate limiting, and errors.

## Environment

Required in `.env`:
- `CANVAS_API_TOKEN` - Canvas API token
- `CANVAS_API_URL` - e.g., `https://your-school.instructure.com/api/v1`
