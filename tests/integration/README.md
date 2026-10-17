# Integration smoke tests

These are opt-in, hit the real PLATO server with real credentials from
`.env`, and are **not** run in CI. Use `scripts/smoke_test_phase1.py`.

```bash
python scripts/smoke_test_phase1.py
```

## Phase 1 checklist (issue #18)

Run against a real PLATO account with at least one enrolled course.

- [x] `list_courses` — returns the account's actual enrolled courses (verified: 10 real courses)
- [x] `get_course_contents` — section/module structure matches the browser view (verified against 거시경제학, id=6253)
- [x] `list_assignments` — verified live against a real assignment as of issue #84 (2026-10-17):
      "중간고사 전 과제", course 5968 (관리회계). Earlier verification (0 live assignments at the time)
      only exercised the empty-list path; both paths are now live-verified.
- [x] `get_assignment_detail` — verified live against the same real assignment: `not-submitted` (status
      `new`) before issue #84's submission, `submitted` after. `late`/extension paths still unit-test-only
      (no late/extended real assignment has existed).
- [x] `get_grades` — returns real grade items for a course with visible grades (verified: 9 items for 6253);
      the `nopermissiontoviewgrades` path was also hit live (against course 12633, an exchange-program
      course with restricted grades) and returned `available=False` instead of crashing
- [x] `list_calendar_events` — returns 0 events when no events fall in the lookahead window (verified: the
      only two real events on this account are in the past, so an empty result is the *correct* answer,
      not a bug -- confirmed by checking their raw timestamps)
- [x] `get_unread_messages` — returns real unread notifications (verified: 3 real "new login" notifications)

## Phase 2 checklist (issues #19-#23)

- [x] `list_notices` — returns the real notice for 재무관리 (course 5973), matches the browser exactly
      (title/writer/date/view count); empty boards (e.g. 6253) return `[]`
- [x] `get_notice_detail` — matches the browser for the same real notice
- [x] `list_qna` — verified against 3 real courses, all return `[]` (every Q&A board on this account is
      genuinely empty, confirmed live)
- [ ] `get_qna_detail` — **never exercised against a real post.** No course on this account has ever had a
      Q&A question posted (checked live across all 10 enrolled courses). Implemented by reusing the same
      detail-page parser as `get_notice_detail` (same ubboard theme), which is a reasonable assumption but
      not a verified one for the Q&A board specifically. **Replies/threads are not parsed at all** -- no
      such page has ever been observed to know its markup. Re-run this once a real Q&A question (ideally
      with at least one reply) exists, and check `docs/ubboard_structure.md` section 5 for what's still
      unknown.

## Phase 3 checklist (issue #25)

- [x] `submit_assignment` (dry_run path) — sanity-checked against a real course: correctly resolves
      real assignment metadata via `list_assignments_for` and raises `ValueError` for a nonexistent
      assignment id
- [x] `submit_assignment` (dry_run=False, real submission) — **exercised live as of issue #84
      (2026-10-17)**, with the user's explicit go-ahead: a small test `.txt` file was submitted as a
      file attachment to the real "중간고사 전 과제" assignment (course 5968), and
      `get_assignment_detail` confirmed `submitted=True`/`status='submitted'` afterward. The
      onlinetext (plain-text) path specifically remains unit-test-only -- this real assignment's
      `assignsubmission_onlinetext` plugin is disabled (confirmed via its live `configs`), so there
      is still no real assignment to verify the text-submission wire format against.
      `maxattempts=1` on this assignment -- do not re-run this live test against it again without
      checking whether a resubmission is even possible (`cansubmit`) first.

## Phase 7 checklist (issue #84 -- file submission)

- [x] `core_files_get_unused_draft_itemid` — verified live, returns a real itemid for this account
- [x] `MoodleClient.upload_file` (multipart POST to `/webservice/upload.php`, not a wsfunction) —
      verified live: uploaded a real file into a draft area and got back a file descriptor
- [x] `AssignmentSummary.file_submission`/`.onlinetext_submission` computed fields — verified live
      against the real assignment's actual `configs` (file: enabled, max_files=20,
      max_size_bytes=1GB, no extension restriction; onlinetext: not configured at all for this
      assignment, i.e. `known=False`)
- [x] Full submit_assignment file-path flow, dry_run=True then dry_run=False, against the real
      assignment -- see Phase 3 checklist entry above for the result
- [ ] Remote/streamable-http file submission (inline content instead of a local path) — **not
      implemented, deliberately deferred.** stdio-only for now, same split `download_course_file`
      went through across issues #28 → #55.

## Phase 7 checklist (issue #88 -- completion/progress status)

- [x] `core_completion_get_course_completion_status` — verified live both ways: `nocriteriaset`
      error against course 6253/5968 (most courses here don't enable course-level completion
      tracking), and a real completed-with-criteria response against course 13518
- [x] `core_completion_get_activities_completion_status` — verified live against course 13518,
      including the nested `details[].rulevalue` shape (`completionview`, `completiontimeenabled`)
- [x] `CourseModule.vod_progress` (parsed from a `vod` module's `customdata`, NOT the video stream
      itself — see `models.VodProgress` docstring for why) — verified live against course 13518's
      real vod modules: `playtime_seconds`, `completion_progress_percent`,
      `lateness_progress_percent`, `attendance_required`, `time_open`/`time_close`/`time_lateness`
      all matched the raw API response

## Phase 7 checklist (issue #89 -- dashboard/timeline views)

- [x] `core_calendar_get_action_events_by_timesort` — verified live, returned 5 real upcoming
      `vod` watch-deadline events for course 10502
- [x] `core_course_get_enrolled_courses_by_timeline_classification` — verified live for
      `classification="inprogress"` (10 real courses) and `"future"` (0, correctly empty)
- [x] `gradereport_overview_get_course_grades` — verified live, returned all 5 real courses'
      overall grades in one call (all ungraded/`"-"` at the time, consistent with `get_grades`)
- [x] `core_calendar_get_action_events_by_course` — verified live (empty result for course 5968,
      which does have other real calendar-adjacent data) but deliberately given no tool of its
      own; see the "why" in `tools/dashboard.py`'s module docstring

## Phase 7 checklist (issue #85 -- quiz support)

- [x] `mod_quiz_get_quizzes_by_courses` — verified live against real courses: correctly returns
      `{"quizzes": [], "warnings": []}` (no course on this account has ever had a real quiz)
- [ ] `mod_quiz_get_user_attempts`/`get_user_best_grade` — schema-only (unit tests against
      documented Moodle 4.5 shape), never exercised against a real quizid -- same caveat
      `AssignmentSummary` had before a real assignment existed
- [ ] Attempt-taking (start/answer/submit/review) — **deliberately not implemented.** Needs a
      real quiz to verify the multi-step write flow against; see `tools/quiz.py`'s module
      docstring for the full reasoning.

## Phase 7 checklist (issue #86 -- forum support)

- [x] `mod_forum_get_forums_by_courses` — verified live against real courses: correctly returns
      `[]` (no course on this account has ever used a standard mod_forum -- all notice/board
      activity is the custom `ubboard` module instead)
- [ ] Discussion/post reads, add_discussion, add_discussion_post — schema-only, never exercised
      against a real forumid/discussionid
- [ ] lock/pin/subscription/favourite-state functions — not wired to tools; documented as
      moderator-only or unverifiable-without-a-real-forum in `tools/forum.py`'s module docstring

## Phase 7 checklist (issue #95 -- grades deep-dive)

- [x] `core_grades_get_gradeitems` — verified live against course 5968: `invalidparameter` error
      on a minimal call. Skipped (redundant with get_grades; not worth reverse-engineering the
      exact required params)
- [x] `core_grades_get_gradable_users` — verified live: `nopermissions` (lists all students for
      grading, a teacher capability). Skipped, confirmed admin/teacher-only
- [x] `gradereport_user_get_grades_table` — verified live: returns a fully-rendered HTML table
      (every cell is browser markup), not structured data. Skipped as wrong-shaped for an API
- [x] `gradereport_user_get_access_information` — verified live against course 5968:
      `{canviewusergradereport: true, canviewmygrades: true, canviewallgrades: false}`. Wired as
      `get_grades_access_info`
- [x] `mod_assign_get_grades` — verified live against the real assignment (id 4975): "No access
      rights in module context". Skipped, confirmed not accessible to a student account

## Phase 7 checklist (issue #100 -- mod_assign student-side remainder)

- [x] `mod_assign_get_user_flags` — verified live against the real assignment: "No access rights
      in module context" (same as #95's `mod_assign_get_grades`). Skipped, confirmed
      not-accessible-to-students
- [x] `mod_assign_view_assign`/`view_submission_status` — deliberately NOT wired to any tool;
      these are view-logging calls that would mutate server-side viewed state as a side effect
      of an AI "read" (see `tools/assignments.py`'s module docstring)
- [x] Audited `mod_assign_get_submission_status`'s real response for unexposed fields: found
      `lastattempt.submission.plugins[].fileareas[].files[]` (the actual submitted file list)
      was silently dropped. Fixed -- `SubmissionStatus.submitted_files` now exposes it,
      verified live against the real #84 test submission (`test_submission.txt` shows up
      correctly)
- [x] `mod_assign_remove_submission` — **live-tested and currently failing.** Tried
      `assignmentid`, `assignid`, `+userid`, `+plugin=''`, zero params, and GET instead of POST
      against the real assignment (id 4975) -- every combination returns a generic
      `invalidparameter` error with no field-specific detail. The real required parameter shape
      could not be determined. The tool is still wired (dry_run=True/preview works and is safe)
      but dry_run=False is NOT confirmed working -- see the loud docstring warning in
      `remove_submission_for`. Confirmed the real test submission was NOT affected by any of
      the failed attempts (an erroring call makes no server-side change).

## Phase 7 checklist (issue #102 -- course change detection)

- [x] `core_course_check_updates` — verified live against the real `assign` module (cmid 85415,
      course 5968): returns rich categorized changes (configuration/completion/gradeitems/
      submissions/grades). Verified against a custom `ubfile` module (cmid 31637, course 6253):
      `missingcallback` -- the module doesn't implement Moodle's change-tracking at all
- [x] `core_course_get_updates_since` — verified live against course 5968: identical real data
      for the assign module in one call (no per-module tocheck array needed), confirmed
      `missingcallback` for every custom module in the course (ubfile) -- wired as the tool
      (`check_updates` itself was NOT given a separate tool, redundant)
- [x] Findings cross-posted to #33 (deferred notification spike): the underlying primitive only
      works for standard activities (assign/quiz/forum-style), NOT this platform's dominant
      content types (ubfile/ubboard/vod) -- a real notification feature needs a different
      strategy (content-diffing) for those

## Phase 7 checklist (issue #103 -- course metadata/search)

- [x] `core_course_get_course_module`/`get_course_module_by_instance` — verified live (cmid
      31637): identical to filtering a real `get_course_contents` response. Wired as
      `get_course_module`
- [x] `core_course_search_courses` — verified live: searches the entire PLATO catalog (180
      results for one test term), not just enrolled courses. Wired as `search_courses`
- [x] `core_course_get_recent_courses` — verified live, returned real recently-accessed courses.
      Wired as `get_recent_courses` (NOTE: may overlap with #116's
      `block_recentlyaccesseditems_get_recent_items`, not yet landed -- revisit then)
- [x] `core_course_get_categories` — verified live (returns the full category tree). Skipped --
      admin/catalog taxonomy, no clear student-facing AI use case
- [x] `core_course_get_user_navigation_options`/`get_user_administration_options` — verified
      live against course 5968: UI show/hide booleans (every administration option was `false`
      for this student account). Skipped -- no data, just UI capability flags
- [x] `core_course_set_favourite_courses` — skipped, no real use case surfaced
- [x] `core_course_view_course` — deliberately not wired, same view-logging reasoning as #100
- [x] Full untruncated `core_course_get_contents` field audit (course 5968): `section.summary`
      and `module.description` exist in the schema but were empty/None for every section and
      module checked -- not worth exposing fields with no observed real data

## Phase 7 checklist (issues #87/#104/#105 -- messaging: site-wide disabled)

- [x] **Major finding, confirmed live**: PLATO has real-time messaging/conversations disabled
      site-wide (Moodle's `messaging` site config). Every conversation-related function errors
      with `{"errorcode": "disabled", "message": "이 사이트에서는 소식 전달이 안 됨"}` --
      `get_conversations`, `get_conversation_counts`, `get_self_conversation`,
      `get_member_info`, `data_for_messagearea_search_messages`, `send_instant_messages`,
      `get_user_contacts` all confirmed. This is a site admin setting, not per-account --
      nothing built on these functions can work here regardless of caller.
- [x] What still works: `get_messages` (notifications, already used) and
      `get_unread_notification_count` (returned a real value, 2, live) -- the separate
      *notifications* system, unaffected by the messaging-disabled setting. Wired as a new
      tool.
- [ ] No tools built for conversation read/send/contacts (#87/#104/#105) -- there is nothing to
      build. Re-verify if PLATO ever enables site messaging.

## Phase 7 checklist (issue #90 -- calendar write)

- [x] `core_calendar_get_allowed_event_types` — verified live: `{"allowedeventtypes": ["user"]}`
      -- a student account can only create personal events. Not wired as its own tool (fixed
      answer), documented in create_calendar_event's docstring
- [x] `core_calendar_get_calendar_access_information` — verified live:
      `canmanageownentries=True`, `canmanagegroupentries=False`. Wired as
      `get_calendar_access_info`
- [x] `core_calendar_get_calendar_export_token` — verified live, mints a real export credential.
      Deliberately NOT exposed as a tool (token-exposure concern, same as files.py's
      TOKEN_IN_URL_WARNING)
- [x] `core_calendar_create_calendar_events`/`delete_calendar_events` — **full round-trip
      verified live**: created a real personal event, confirmed it via list_calendar_events,
      deleted it, confirmed removal. Wired as `create_calendar_event`/`delete_calendar_event`
- [x] `get_calendar_day_view`/`get_calendar_monthly_view`/`get_calendar_upcoming_view`/
      `get_calendar_event_by_id` — skipped as redundant with the already-implemented
      `list_calendar_events` for this account's actual calendar usage (no group/category
      events observed)

## Phase 7 checklist (issue #113 -- tool_mobile and miscellaneous core internals)

No new tools from this issue -- documentation-only, as its own acceptance criteria expected.

- [x] `tool_mobile_get_config`/`get_public_config`/`get_plugins_supporting_mobile` — verified
      live: site/app configuration data (site name, login settings, installed plugin list),
      not user data. Skipped, no AI-assistant use case
- [x] **`tool_mobile_call_external_functions` (batching) -- evaluated with a real measurement**:
      batched 2 real calls (`mod_assign_get_assignments` + `mod_assign_get_submission_status`)
      into one HTTP request live and timed both paths: sequential ~0.95s, batched ~0.56s (~40%
      faster for 2 calls). The response wraps each result as a JSON-encoded *string* in
      `responses[].data` (needs an extra `json.loads`, not a plain nested object) -- a real
      wire-format detail any future implementation would need to handle. **Decision: worth
      adopting as a future `MoodleClient` optimization (e.g. batching
      get_assignment_detail_for's two sequential calls), but implementing it is a separate,
      deliberate refactor with its own regression risk -- out of scope for this
      audit-and-decide issue. Tracked as a documented opportunity, not built now.**
- [x] `tool_mobile_get_autologin_key`/`get_tokens_for_qr_login`/`validate_subscription_key` --
      **security decision: do not expose.** Live-tested (errors with `invalidparameter` on a
      minimal call -- needs additional params not pursued, since the decision is to skip
      regardless of whether they'd succeed). These mint session/login credentials; per the
      existing wstoken-scope finding (files.py's TOKEN_IN_URL_WARNING, confirmed in #56 that a
      token authenticates arbitrary API calls), exposing credential-minting functions to an AI
      caller is a straightforward security regression, not a feature
- [x] `core_filters_get_available_in_context`/`core_get_component_strings` — verified live:
      `invalidparameter` on a minimal call (both need context-specific params); even if called
      correctly, both return UI-string/filter-config plumbing, not useful standalone. Skipped
- [x] `core_table_get_dynamic_table_content`/`core_my_view_page`/`core_question_update_flag` --
      not called (all three require implementation-specific context -- a table handler class
      name, a My Moodle block instance, a question-attempt id -- that only make sense from
      inside Moodle's own UI, not as a standalone AI tool call). Skipped as not independently
      meaningful
- [x] `tool_analytics_potential_contexts` — verified live: `nopermissions` ("모델 관리" =
      model management). Confirmed admin-only
- [x] `tool_moodlenet_verify_webfinger`/`search_courses` — verified live: `invalidparameter`.
      MoodleNet federation/discovery feature, no real use case on this platform. Skipped

## Phase 7 checklist (issue #116 -- blocks, AI placement, notification devices)

- [x] `block_recentlyaccesseditems_get_recent_items` — verified live: 9 real recently-accessed
      modules with direct view URLs. Wired as `get_recent_items`
- [x] `block_starredcourses_get_starred_courses` — verified live: `[]` (no starred courses, a
      valid empty state). Wired as `get_starred_courses`
- [x] `message_popup_get_popup_notifications` — verified live, compared against
      `get_unread_messages`: same underlying notification (a real assignment-due reminder
      appeared in both), richer HTML fields but no new information. Documented as redundant,
      no second tool built
- [x] `core_block_get_dashboard_blocks`/`get_course_blocks`/`fetch_addable_blocks` — verified
      live: UI layout data (which blocks are docked where). Skipped, not useful standalone
- [x] `aiplacement_*`/`core_ai_*` — the irony noted in the issue is real: PLATO exposes
      Moodle 4.5's own built-in AI text/image generation. **Documented decision: plato-mcp does
      NOT proxy another LMS's AI features** -- an MCP tool that itself calls a different AI is
      a confusing indirection with no clear benefit over the calling AI doing the work directly.
      Not wired, regardless of the exact live parameter shape (both tested functions errored
      `invalidparameter` on a minimal call; not pursued further since the decision doesn't
      depend on them working)
- [x] `message_airnotifier_*` (4 functions) — verified live: `is_system_configured` returns `0`
      (push notifications not set up on this platform at all). Skipped

## Phase 7 checklist (issue #91 -- video conference)

- [x] `mod_bigbluebuttonbn_get_bigbluebuttonbns_by_courses` — verified live: correctly returns
      `{"bigbluebuttonbns": [], "warnings": []}` (no real BBB module on this account). Wired as
      `list_video_conferences`
- [ ] `get_join_url`/`can_join`/`meeting_info` (BBB), `mod_zoom_get_state` — schema-only/not
      built. `mod_zoom_get_state` attempted live with a fake id: `invalidparameter` (real
      shape not determined, not pursued -- no real module to verify a guess against anyway)

## Phase 7 checklist (issue #92 -- other content modules, redundancy audit)

No new tools from this issue -- confirmed redundant with `get_course_contents`, as its own
acceptance criteria expected to check for.

- [x] `mod_url_get_urls_by_courses` — **diffed against a real response** (course 12932, the
      one real `url` module on this account, "설문조사"/survey). The type-specific function
      returns `externalurl` (a Google Forms link); `get_course_contents`'s generic
      `contents[].fileurl` for the same module already returns the exact same URL. Confirmed
      redundant
- [x] `mod_resource_get_resources_by_courses`/`get_folders_by_courses`/`get_pages_by_courses`/
      `get_books_by_courses`/`get_labels_by_courses`/`get_imscps_by_courses` — all verified
      live against real courses: correctly empty (none of these module types exist in any
      real course on this account). Given the `url` diff above already proved the generic
      path carries the same data for a sibling content module, these are presumed equally
      redundant rather than re-diffed one-by-one with no real instance to diff against
- [ ] `mod_lti_get_ltis_by_courses`/`get_tool_launch_data` — verified live: `{"ltis": [],
      "warnings": []}` (no LTI module on this account). `get_tool_launch_data` (which returns
      a signed launch URL NOT present in the generic contents path) could not be verified --
      no real LTI instance exists. Flagged unverified, same caveat pattern as
      AssignmentSummary before a real assignment existed -- re-check if an LTI module ever
      appears, since this is the one function in scope actually expected to NOT be redundant

## Phase 7 checklist (issue #93 -- mod_lesson)

- [x] `mod_lesson_get_lessons_by_courses` — verified live: correctly returns `{"lessons": [],
      "warnings": []}` (no mod_lesson on this account). Wired as `list_lessons`
- [ ] The remaining 16 functions (lesson detail, pages, user attempts/grades/timers, and the
      attempt-flow writes) -- not built, no real lesson to verify any schema or write flow
      against. Same reasoning as mod_quiz (#85)

## Phase 7 checklist (issue #94 -- mod_workshop)

- [x] `mod_workshop_get_workshops_by_courses` — verified live: correctly returns
      `{"workshops": [], "warnings": []}` (no mod_workshop on this account). Wired as
      `list_workshops`
- [ ] The remaining 18 functions (submissions, assessments, grades, and the submission/
      assessment writes) -- not built, no real workshop to verify any schema or write flow
      against

## Phase 7 checklist (issue #106 -- mod_feedback)

- [x] `mod_feedback_get_feedbacks_by_courses` — verified live: correctly returns
      `{"feedbacks": [], "warnings": []}`. Wired as `list_feedbacks`
- [ ] Remaining 13 functions (items, analysis, responses, submission writes) -- not built, no
      real feedback activity to verify against

## Phase 3 checklist (issues #26-#27)

- [x] `_fetch_write_form_tokens` (GET only) — verified live against the real Q&A write form:
      sesskey and both per-load draft-area ids extracted correctly
- [x] `post_qna_question` (dry_run path) — verified live: resolves the real Q&A board id (37083)
      and builds a correct preview, no request sent
- [ ] `post_new_thread` / `post_qna_question` (dry_run=False, real POST) — **deliberately not
      exercised live.** Unlike every read-only tool so far, this creates a real, visible post on
      a real course Q&A board -- doing that needs the user's explicit go-ahead (which was asked
      and deferred for now), not routine automated verification. When this is picked up: post one
      low-stakes test question, confirm it appears via `list_qna`, then decide whether/how to
      remove it (no delete tool exists yet).
- [ ] `reply_to_qna` — **not implemented at all.** The reply/thread POST mechanism (does it reuse
      `write.php` with `bwid` set to the parent post id? a different endpoint?) has never been
      observed -- no real Q&A thread exists anywhere on this account to reply to. See
      `docs/ubboard_structure.md` section 6. Needs a real thread to exist before this can be built
      on anything other than a guess.

## PII review follow-up (issue #36)

- [ ] Whether PLATO enforces a Q&A post's "secret" (private/instructor-only) flag
      **server-side** -- i.e. whether `list_qna`/`get_qna_detail` from a *different*
      account would simply never receive that post's content -- has never been
      tested. Verify by posting a real `secret` Q&A question from one account and
      confirming a second account can't see it via these tools. See
      `docs/pii_review.md` for the full review.

## Known gap

A real assignment now exists (course 5968, "중간고사 전 과제", since ~2026-10). The
"assignment exists and has a submission" path has been live-verified for the file-submission flow
(issue #84) and basic not-submitted/submitted transitions, but `feedback.plugins[].editorfields[].text`
(an instructor's actual written feedback comment) still has never appeared in a real response -- this
assignment has not been graded yet. Re-check once it is.

`AssignmentSummary`/`SubmissionStatus`/`SubmissionFeedback`/`PreviousAttempt`/`AssignmentExtraData` were
expanded (cmid, cutoffdate, gradingduedate, intro/introattachments, activity/activityattachments,
maxattempts, attemptreopenmethod, teamsubmission, cansubmit, locked, extensionduedate, gradingstatus,
feedback.grade/plugins, previousattempts, assignmentdata) based on reading Moodle 4.5's
`mod/assign/externallib.php` source directly (MOODLE_405_STABLE, matching PLATO's actual 4.5.13 release).
`configs` (added in issue #84) is now confirmed against a real response; the rest of this list is still
schema-only, unconfirmed against live data.
