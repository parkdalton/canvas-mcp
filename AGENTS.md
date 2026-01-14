# Canvas MCP - Student Tools Guide

MCP server for Canvas LMS. Helps students track assignments, grades, due dates, and course content.

## Quick Reference

### What can I ask?
- "What assignments do I have due this week?"
- "Show me my grades"
- "What's on my Canvas TODO list?"
- "List my courses"
- "Show the syllabus for [course]"
- "What peer reviews do I need to complete?"
- "Show announcements for [course]"
- "Download file 12345"
- "What quizzes are in [course]?"
- "Show my quiz attempts for [quiz]"
- "Help me take the practice quiz"

## All Tools

### Personal Tracking (Your Data)
| Tool | What it does |
|------|--------------|
| `get_my_upcoming_assignments` | Assignments due in next N days |
| `get_my_submission_status` | What you've submitted vs missing |
| `get_my_course_grades` | Your grades across all courses |
| `get_my_todo_items` | Your Canvas TODO list |
| `get_my_peer_reviews_todo` | Peer reviews you need to complete |

### Courses
| Tool | What it does |
|------|--------------|
| `list_courses` | Your enrolled courses |
| `get_course_details` | Course info and syllabus |
| `get_course_content_overview` | Overview of course content |

### Assignments
| Tool | What it does |
|------|--------------|
| `list_assignments` | Assignments in a course |
| `get_assignment_details` | Assignment description, due date, your submission status |

### Discussions
| Tool | What it does |
|------|--------------|
| `list_discussion_topics` | Discussion forums in a course |
| `get_discussion_topic_details` | Details about a discussion |
| `list_discussion_entries` | Posts in a discussion |
| `get_discussion_entry_details` | Specific post with replies |
| `post_discussion_entry` | Post to a discussion |
| `reply_to_discussion_entry` | Reply to a post |
| `list_announcements` | Course announcements |

### Course Content
| Tool | What it does |
|------|--------------|
| `list_pages` | Course pages |
| `get_page_content` | Read a page |
| `get_front_page` | Course home page |
| `list_modules` | Course modules |
| `list_module_items` | Items in a module |
| `list_groups` | Course groups |

### Files
| Tool | What it does |
|------|--------------|
| `list_course_files` | Files in a course |
| `list_course_folders` | Folder structure |
| `list_folder_files` | Files in a folder |
| `get_file_download_url` | Get download link |
| `download_file` | Download to local machine |

**Note:** Don't spam `download_file`. Download one file at a time.

### Quizzes
| Tool | What it does |
|------|--------------|
| `list_quizzes` | All quizzes in a course |
| `get_quiz_details` | Quiz info, time limit, attempts allowed |
| `get_my_quiz_submissions` | Your quiz attempts and scores |
| `start_quiz` | Start a quiz attempt (RESTRICTED - see below) |
| `get_quiz_questions` | Get questions for active quiz |
| `answer_quiz_question` | Submit answer to a question |

**IMPORTANT Quiz Restrictions:**
- `start_quiz` only works if the quiz has **no time limit** OR **unlimited attempts**
- If quiz has BOTH a time limit AND limited attempts, you must take it in Canvas directly
- There is NO `complete_quiz` tool - quizzes auto-submit when time expires or you submit in Canvas

**Answer Formats by Question Type:**
| Type | Format | Example |
|------|--------|---------|
| Multiple choice | `int` (answer_id) | `1234` |
| True/False | `int` (answer_id) | `5678` |
| Essay | `str` | `"My answer text"` |
| Fill in blank | `str` | `"answer"` |
| Multiple answers | `list[int]` | `[1234, 5678]` |
| Matching | `list[dict]` | `[{"answer_id": 1, "match_id": 2}]` |
| Multiple blanks | `dict` | `{"blank1": "ans1"}` |
| Numerical | `float` | `3.14` |

## Important Notes

### Finding a Syllabus
Syllabi can be in multiple places. Check in this order:
1. **Course details** - `get_course_details(course)` may have syllabus in the response
2. **Course files** - `list_course_files(course, search_term="syllabus")` - **most common location**
3. **Course pages** - `list_pages(course, search_term="syllabus")`
4. **Modules** - Check first module with `list_modules(course)` then `list_module_items(course, module_id)`

If user asks to "download the syllabus", search files first, then download with `download_file(file_id)`.

## Common Workflows

### Weekly Planning
```
1. get_my_upcoming_assignments(days=7)  → What's due
2. get_my_submission_status()           → What you've done
3. get_my_peer_reviews_todo()           → Peer reviews needed
```

### Check a Course
```
1. list_courses()                       → Find course code
2. list_assignments(course)             → See assignments
3. list_announcements(course)           → Recent announcements
```

### Read Course Material
```
1. list_modules(course)                 → See structure
2. list_module_items(course, module_id) → See items
3. get_page_content(course, page_url)   → Read page
```

### Download Files
```
1. list_course_files(course)            → Find file ID
2. download_file(file_id)               → Download it
```

### Take a Quiz (API)
```
1. list_quizzes(course)                 → Find quiz ID, check if API-startable
2. get_quiz_details(course, quiz_id)    → Verify restrictions
3. start_quiz(course, quiz_id)          → Get submission_id + validation_token
4. get_quiz_questions(submission_id)    → See questions and answer options
5. answer_quiz_question(submission_id, attempt, token, q_id, answer)
   → Repeat for each question
6. Submit quiz in Canvas when done (no API complete)
```

## Course Identifiers

All course tools accept:
- Course code: `CS_101_Fall2024`
- Canvas ID: `12345`

Use `list_courses()` to find your course codes.

## Errors

| Error | Meaning |
|-------|---------|
| 401 | Token expired - need new Canvas token |
| 403 | You don't have access to this |
| 404 | Course/assignment doesn't exist |
| 429 | Too many requests - slow down |
