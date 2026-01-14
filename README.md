# Canvas MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

MCP server for Canvas LMS. Helps students track assignments, grades, due dates, and course content through AI assistants like Claude Desktop.

## What Can It Do?

- "What assignments do I have due this week?"
- "Show me my grades"
- "What's on my Canvas TODO list?"
- "Show me the syllabus for [course]"
- "Download the lecture slides"

## Quick Start

### 1. Install

```bash
git clone https://github.com/vishalsachdev/canvas-mcp.git
cd canvas-mcp

python3 -m venv .venv
. .venv/bin/activate
pip install -e .
```

### 2. Configure

```bash
cp env.template .env
# Edit .env with your Canvas credentials:
#   CANVAS_API_TOKEN=your_token_here
#   CANVAS_API_URL=https://your-school.instructure.com/api/v1
```

**Get your Canvas API token:** Canvas → Account → Settings → New Access Token

> **Note:** Some schools restrict API token creation for students. Contact your IT department if you can't create a token.

### 3. Add to Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

```json
{
  "mcpServers": {
    "canvas-api": {
      "command": "/full/path/to/canvas-mcp/.venv/bin/canvas-mcp-server"
    }
  }
}
```

### 4. Test

```bash
canvas-mcp-server --test
```

Restart Claude Desktop and try: "What courses am I enrolled in?"

## Available Tools

| Category | Tools |
|----------|-------|
| **Personal** | `get_my_upcoming_assignments`, `get_my_course_grades`, `get_my_todo_items`, `get_my_submission_status`, `get_my_peer_reviews_todo` |
| **Courses** | `list_courses`, `get_course_details`, `get_course_content_overview` |
| **Assignments** | `list_assignments`, `get_assignment_details` |
| **Discussions** | `list_discussion_topics`, `list_announcements`, `post_discussion_entry`, `reply_to_discussion_entry` |
| **Content** | `list_pages`, `get_page_content`, `list_modules`, `list_module_items` |
| **Files** | `list_course_files`, `download_file` |

See [AGENTS.md](AGENTS.md) for full tool reference.

## Other MCP Clients

Works with any MCP client: [Cursor](https://cursor.sh), [Zed](https://zed.dev), [Windsurf](https://codeium.com/windsurf), [Continue](https://continue.dev).

See [MCP clients list](https://modelcontextprotocol.io/clients) for configuration.

## Privacy

- Your data only: Tools access only your Canvas data
- Local processing: Everything runs on your machine
- No tracking: Your usage remains private

## License

MIT License - see [LICENSE](LICENSE)
