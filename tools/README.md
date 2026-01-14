# Canvas MCP Tools Reference

Complete reference for all Canvas MCP tools. For AI agents, see [AGENTS.md](../AGENTS.md).

## Personal Tracking Tools

Your personal Canvas data - grades, assignments, TODOs.

### `get_my_upcoming_assignments`
Get assignments due in the next N days.

**Parameters:**
- `days` (optional): Number of days to look ahead (default: 7)

**Example:** "What's due this week?"

---

### `get_my_submission_status`
Check what you've submitted vs what's missing.

**Parameters:**
- `course_identifier` (optional): Specific course to check

**Example:** "What have I submitted in CS 101?"

---

### `get_my_course_grades`
View your current grades across all courses.

**Example:** "Show me my grades"

---

### `get_my_todo_items`
Get items from your Canvas TODO list.

**Example:** "What's on my Canvas TODO?"

---

### `get_my_peer_reviews_todo`
See peer reviews you need to complete.

**Parameters:**
- `course_identifier` (optional): Specific course to check

**Example:** "What peer reviews do I need to do?"

---

## Course Tools

### `list_courses`
List all courses you're enrolled in.

**Example:** "What courses am I in?"

---

### `get_course_details`
Get course information including syllabus.

**Parameters:**
- `course_identifier`: Course code or Canvas ID

**Example:** "Show me the syllabus for CS 101"

---

### `get_course_content_overview`
Get an overview of course content.

**Parameters:**
- `course_identifier`: Course code or Canvas ID

---

## Assignment Tools

### `list_assignments`
List all assignments in a course with your submission status.

**Parameters:**
- `course_identifier`: Course code or Canvas ID

**Example:** "What assignments are in CS 101?"

---

### `get_assignment_details`
Get full details about an assignment including description.

**Parameters:**
- `course_identifier`: Course code or Canvas ID
- `assignment_id`: The assignment ID

**Example:** "Tell me about assignment 12345"

---

## Discussion Tools

### `list_discussion_topics`
List discussions in a course.

**Parameters:**
- `course_identifier`: Course code or Canvas ID
- `include_announcements` (optional): Include announcements (default: false)

---

### `get_discussion_topic_details`
Get details about a discussion topic.

**Parameters:**
- `course_identifier`: Course code or Canvas ID
- `topic_id`: Discussion topic ID

---

### `list_discussion_entries`
List posts in a discussion.

**Parameters:**
- `course_identifier`: Course code or Canvas ID
- `topic_id`: Discussion topic ID
- `include_full_content` (optional): Show full posts (default: false)

---

### `post_discussion_entry`
Post to a discussion.

**Parameters:**
- `course_identifier`: Course code or Canvas ID
- `topic_id`: Discussion topic ID
- `message`: Your post content

---

### `reply_to_discussion_entry`
Reply to a discussion post.

**Parameters:**
- `course_identifier`: Course code or Canvas ID
- `topic_id`: Discussion topic ID
- `entry_id`: Post ID to reply to
- `message`: Your reply

---

### `list_announcements`
List course announcements.

**Parameters:**
- `course_identifier`: Course code or Canvas ID

**Example:** "Show announcements for CS 101"

---

## Content Tools

### `list_pages`
List pages in a course.

**Parameters:**
- `course_identifier`: Course code or Canvas ID
- `search_term` (optional): Filter by title

---

### `get_page_content`
Read the content of a page.

**Parameters:**
- `course_identifier`: Course code or Canvas ID
- `page_url`: Page URL from `list_pages`

---

### `get_front_page`
Get the course home/front page.

**Parameters:**
- `course_identifier`: Course code or Canvas ID

---

### `list_modules`
List modules in a course.

**Parameters:**
- `course_identifier`: Course code or Canvas ID

---

### `list_module_items`
List items in a module.

**Parameters:**
- `course_identifier`: Course code or Canvas ID
- `module_id`: Module ID from `list_modules`

---

### `list_groups`
List groups in a course.

**Parameters:**
- `course_identifier`: Course code or Canvas ID

---

## File Tools

### `list_course_files`
List files in a course.

**Parameters:**
- `course_identifier`: Course code or Canvas ID
- `search_term` (optional): Filter by filename
- `content_types` (optional): Filter by type (e.g., "application/pdf")

---

### `list_course_folders`
List folder structure in a course.

**Parameters:**
- `course_identifier`: Course code or Canvas ID

---

### `list_folder_files`
List files in a specific folder.

**Parameters:**
- `folder_id`: Folder ID from `list_course_folders`

---

### `get_file_download_url`
Get a download URL for a file.

**Parameters:**
- `file_id`: File ID from `list_course_files`

**Note:** URLs are time-limited.

---

### `download_file`
Download a file to your local machine.

**Parameters:**
- `file_id`: File ID from `list_course_files`
- `destination_folder` (optional): Where to save (default: ~/Downloads)

**Warning:** Don't call this rapidly. Download one file at a time.

---

## Quiz Tools

### `list_quizzes`
List all quizzes in a course.

**Parameters:**
- `course_identifier`: Course code or Canvas ID

**Example:** "What quizzes are in CS 101?"

---

### `get_quiz_details`
Get detailed information about a quiz including time limit, attempts, and restrictions.

**Parameters:**
- `course_identifier`: Course code or Canvas ID
- `quiz_id`: The quiz ID

**Example:** "Show me details for quiz 12345"

---

### `get_my_quiz_submissions`
View your quiz attempt history and scores.

**Parameters:**
- `course_identifier`: Course code or Canvas ID
- `quiz_id`: The quiz ID

**Example:** "Show my attempts for the midterm quiz"

---

### `start_quiz`
Start a quiz attempt. **RESTRICTED** - only works if quiz has no time limit OR unlimited attempts.

**Parameters:**
- `course_identifier`: Course code or Canvas ID
- `quiz_id`: The quiz ID

**Returns:** submission_id, attempt number, and validation_token needed for answering questions.

**Restriction:** If quiz has BOTH a time limit AND limited attempts, you must take it in Canvas directly.

---

### `get_quiz_questions`
Get all questions for an active quiz attempt.

**Parameters:**
- `quiz_submission_id`: The submission ID from `start_quiz`

**Returns:** Questions with text, type, and answer options (including answer IDs for multiple choice).

---

### `answer_quiz_question`
Submit an answer to a quiz question.

**Parameters:**
- `quiz_submission_id`: The submission ID from `start_quiz`
- `attempt`: Current attempt number from `start_quiz`
- `validation_token`: Token from `start_quiz`
- `question_id`: The question ID to answer
- `answer`: The answer (format depends on question type)

**Answer Formats:**
| Question Type | Format | Example |
|--------------|--------|---------|
| Multiple choice | `int` (answer_id) | `1234` |
| True/False | `int` (answer_id) | `5678` |
| Essay | `str` | `"My essay answer"` |
| Fill in blank | `str` | `"answer text"` |
| Multiple answers | `list[int]` | `[1234, 5678]` |
| Matching | `list[dict]` | `[{"answer_id": 1, "match_id": 2}]` |
| Multiple blanks | `dict` | `{"blank1": "answer1"}` |
| Numerical | `float` | `3.14` |

**Note:** There is no `complete_quiz` tool. Quizzes auto-submit when time expires or you submit in Canvas.

---

## Course Identifiers

All tools that take `course_identifier` accept:
- **Course code:** `CS_101_Fall2024` (from `list_courses`)
- **Canvas ID:** `12345`

Use `list_courses()` to find your course codes/IDs.
