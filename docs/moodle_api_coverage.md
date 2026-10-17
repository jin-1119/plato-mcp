# Moodle Open API coverage

Every function returned by `core_webservice_get_site_info` for this account's token (439 functions, confirmed live and unchanged across the Phase 7 epic, 2026-10-17), with its status, the issue that resolved it, and why.

This is the durable artifact issue #99 (closing out epic #83) exists to produce -- "did we cover everything" is answerable by reading this file instead of re-deriving it. See each referenced issue (and `tests/integration/README.md`'s matching "Phase 7 checklist" section) for the full live-verification detail behind each row.

| Function | Status | Issue | Note |
|---|---|---|---|
| `aiplacement_courseassist_summarise_text` | Verified live/attempted, not wired (product decision) | #116 | plato-mcp does not proxy another LMS's AI generation features |
| `aiplacement_editor_generate_image` | Verified live/attempted, not wired (product decision) | #116 | plato-mcp does not proxy another LMS's AI generation features |
| `aiplacement_editor_generate_text` | Verified live/attempted, not wired (product decision) | #116 | plato-mcp does not proxy another LMS's AI generation features |
| `block_recentlyaccesseditems_get_recent_items` | Implemented | - | wired into a plato-mcp tool |
| `block_starredcourses_get_starred_courses` | Implemented | - | wired into a plato-mcp tool |
| `core_ai_get_policy_status` | Verified live/attempted, not wired (product decision) | #116 | plato-mcp does not proxy another LMS's AI generation features |
| `core_ai_set_policy_status` | Verified live/attempted, not wired (product decision) | #116 | plato-mcp does not proxy another LMS's AI generation features |
| `core_badges_get_badge` | Disabled site-wide | #112 | badgesdisabled |
| `core_badges_get_user_badge_by_hash` | Disabled site-wide | #112 | badgesdisabled |
| `core_badges_get_user_badges` | Disabled site-wide | #112 | badgesdisabled |
| `core_block_fetch_addable_blocks` | Verified live, not wired | #116 | UI layout data, not useful standalone |
| `core_block_get_course_blocks` | Verified live, not wired | #116 | UI layout data, not useful standalone |
| `core_block_get_dashboard_blocks` | Verified live, not wired | #116 | UI layout data, not useful standalone |
| `core_blog_add_entry` | Disabled site-wide | #112 | blogdisable |
| `core_blog_delete_entry` | Disabled site-wide | #112 | blogdisable |
| `core_blog_get_access_information` | Disabled site-wide | #112 | blogdisable |
| `core_blog_get_entries` | Disabled site-wide | #112 | blogdisable |
| `core_blog_prepare_entry_for_edition` | Disabled site-wide | #112 | blogdisable |
| `core_blog_update_entry` | Disabled site-wide | #112 | blogdisable |
| `core_blog_view_entries` | Disabled site-wide | #112 | blogdisable |
| `core_calendar_create_calendar_events` | Implemented | - | wired into a plato-mcp tool |
| `core_calendar_delete_calendar_events` | Implemented | - | wired into a plato-mcp tool |
| `core_calendar_get_action_events_by_course` | Verified live, not wired | #89/#90 | subset of get_upcoming_action_events |
| `core_calendar_get_action_events_by_courses` | Verified live, not wired | #89/#90 | subset of get_upcoming_action_events |
| `core_calendar_get_action_events_by_timesort` | Implemented | - | wired into a plato-mcp tool |
| `core_calendar_get_allowed_event_types` | Verified live, not wired | #90 | redundant with list_calendar_events or fixed/trivial answer |
| `core_calendar_get_calendar_access_information` | Implemented | - | wired into a plato-mcp tool |
| `core_calendar_get_calendar_day_view` | Verified live, not wired | #90 | redundant with list_calendar_events or fixed/trivial answer |
| `core_calendar_get_calendar_event_by_id` | Verified live, not wired | #90 | redundant with list_calendar_events or fixed/trivial answer |
| `core_calendar_get_calendar_events` | Implemented | - | wired into a plato-mcp tool |
| `core_calendar_get_calendar_export_token` | Not wired (token-exposure concern) | #90 | mints a real export credential, same concern as files.py's TOKEN_IN_URL_WARNING |
| `core_calendar_get_calendar_monthly_view` | Verified live, not wired | #90 | redundant with list_calendar_events or fixed/trivial answer |
| `core_calendar_get_calendar_upcoming_view` | Verified live, not wired | #90 | redundant with list_calendar_events or fixed/trivial answer |
| `core_calendar_submit_create_update_form` | Verified live, not wired | #90 | redundant with list_calendar_events or fixed/trivial answer |
| `core_calendar_update_event_start_day` | Verified live, not wired | #90 | redundant with list_calendar_events or fixed/trivial answer |
| `core_comment_add_comments` | Not wired | #117 | write side of a family with no real item to attach to |
| `core_comment_delete_comments` | Not wired | #117 | write side of a family with no real item to attach to |
| `core_comment_get_comments` | Verified live, not wired | #117 | invalidparameter; no real commentable item exists |
| `core_competency_competency_viewed` | Verified live, unavailable | #114 | competency frameworks not configured on this platform (core_course_get_user_navigation_options confirms competencies.available=false) |
| `core_competency_delete_evidence` | Verified live, unavailable | #114 | competency frameworks not configured on this platform (core_course_get_user_navigation_options confirms competencies.available=false) |
| `core_competency_get_scale_values` | Verified live, unavailable | #114 | competency frameworks not configured on this platform (core_course_get_user_navigation_options confirms competencies.available=false) |
| `core_competency_grade_competency_in_course` | Verified live, unavailable | #114 | competency frameworks not configured on this platform (core_course_get_user_navigation_options confirms competencies.available=false) |
| `core_competency_list_course_competencies` | Verified live, unavailable | #114 | competency frameworks not configured on this platform (core_course_get_user_navigation_options confirms competencies.available=false) |
| `core_competency_user_competency_plan_viewed` | Verified live, unavailable | #114 | competency frameworks not configured on this platform (core_course_get_user_navigation_options confirms competencies.available=false) |
| `core_competency_user_competency_viewed` | Verified live, unavailable | #114 | competency frameworks not configured on this platform (core_course_get_user_navigation_options confirms competencies.available=false) |
| `core_competency_user_competency_viewed_in_course` | Verified live, unavailable | #114 | competency frameworks not configured on this platform (core_course_get_user_navigation_options confirms competencies.available=false) |
| `core_competency_user_competency_viewed_in_plan` | Verified live, unavailable | #114 | competency frameworks not configured on this platform (core_course_get_user_navigation_options confirms competencies.available=false) |
| `core_completion_get_activities_completion_status` | Implemented | - | wired into a plato-mcp tool |
| `core_completion_get_course_completion_status` | Implemented | - | wired into a plato-mcp tool |
| `core_completion_mark_course_self_completed` | Not wired | #88 | manual completion override, no clear AI-assistant use case beyond the read tools already built |
| `core_completion_update_activity_completion_status_manually` | Not wired | #88 | manual completion override, no clear AI-assistant use case beyond the read tools already built |
| `core_course_check_updates` | Redundant | #102 | same data as core_course_get_updates_since for one module |
| `core_course_get_categories` | Verified live, not wired | #103 | admin/catalog taxonomy, UI booleans, or no real use case |
| `core_course_get_contents` | Implemented | - | wired into a plato-mcp tool |
| `core_course_get_course_module` | Implemented | - | wired into a plato-mcp tool |
| `core_course_get_course_module_by_instance` | Verified live, not wired | #103 | admin/catalog taxonomy, UI booleans, or no real use case |
| `core_course_get_courses` | Verified live, not wired | #103 | admin/catalog taxonomy, UI booleans, or no real use case |
| `core_course_get_courses_by_field` | Verified live, not wired | #103 | admin/catalog taxonomy, UI booleans, or no real use case |
| `core_course_get_enrolled_courses_by_timeline_classification` | Implemented | - | wired into a plato-mcp tool |
| `core_course_get_enrolled_courses_with_action_events_by_timeline_classification` | Not wired | #89 | overlaps get_upcoming_action_events + get_courses_by_timeline |
| `core_course_get_recent_courses` | Implemented | - | wired into a plato-mcp tool |
| `core_course_get_updates_since` | Implemented | - | wired into a plato-mcp tool |
| `core_course_get_user_administration_options` | Verified live, not wired | #103 | admin/catalog taxonomy, UI booleans, or no real use case |
| `core_course_get_user_navigation_options` | Verified live, not wired | #103 | admin/catalog taxonomy, UI booleans, or no real use case |
| `core_course_search_courses` | Implemented | - | wired into a plato-mcp tool |
| `core_course_set_favourite_courses` | Verified live, not wired | #103 | admin/catalog taxonomy, UI booleans, or no real use case |
| `core_course_view_course` | Not wired (view-logging) | #103 | same reasoning as other view_* functions |
| `core_enrol_get_course_enrolment_methods` | Verified live (empty) | #97 | no visible enrolment-method detail for a student role |
| `core_enrol_get_enrolled_users` | Implemented | - | wired into a plato-mcp tool |
| `core_enrol_get_users_courses` | Implemented | - | wired into a plato-mcp tool |
| `core_enrol_search_users` | Not wired (privacy scope) | #97 | errored on minimal call; same concern as get_users_by_field |
| `core_files_delete_draft_files` | Not wired | #84 | internal draft-area file management beyond what get_unused_draft_itemid+upload_file already need |
| `core_files_get_files` | Not wired | #84 | internal draft-area file management beyond what get_unused_draft_itemid+upload_file already need |
| `core_files_get_unused_draft_itemid` | Implemented | - | wired into a plato-mcp tool |
| `core_filters_get_all_states` | Verified live, not wired | #113 | UI filter config, same bucket as get_available_in_context |
| `core_filters_get_available_in_context` | Verified live, not wired | #113 | invalidparameter; UI filter config even if called correctly |
| `core_get_component_strings` | Verified live, not wired | #113 | invalidparameter; UI string plumbing |
| `core_grades_get_enrolled_users_for_search_widget` | Not wired (teacher grading-UI widgets) | #95 | same family as gradereport_grader_get_users_in_report |
| `core_grades_get_enrolled_users_for_selector` | Not wired (teacher grading-UI widgets) | #95 | same family as gradereport_grader_get_users_in_report |
| `core_grades_get_gradable_users` | Permission-denied (teacher-only) | #95 | nopermissions |
| `core_grades_get_gradeitems` | Redundant | #95 | covered by get_grades |
| `core_grades_get_groups_for_search_widget` | Not wired (teacher grading-UI widgets) | #95 | same family as gradereport_grader_get_users_in_report |
| `core_grades_get_groups_for_selector` | Not wired (teacher grading-UI widgets) | #95 | same family as gradereport_grader_get_users_in_report |
| `core_grades_grader_gradingpanel_point_fetch` | Not wired (teacher grading-UI widgets) | #95 | same family as gradereport_grader_get_users_in_report |
| `core_grades_grader_gradingpanel_point_store` | Not wired (teacher grading-UI widgets) | #95 | same family as gradereport_grader_get_users_in_report |
| `core_grades_grader_gradingpanel_scale_fetch` | Not wired (teacher grading-UI widgets) | #95 | same family as gradereport_grader_get_users_in_report |
| `core_grades_grader_gradingpanel_scale_store` | Not wired (teacher grading-UI widgets) | #95 | same family as gradereport_grader_get_users_in_report |
| `core_group_get_activity_allowed_groups` | Not called | #97 | no group-restricted activity exists on this account |
| `core_group_get_activity_groupmode` | Not wired (teacher-side group metadata) | #97 | same bucket as core_group_get_course_groups |
| `core_group_get_course_groupings` | Not wired (teacher-side group metadata) | #97 | same bucket as core_group_get_course_groups |
| `core_group_get_course_groups` | Permission-denied (teacher-only) | #97 | nopermissions (팀 관리) |
| `core_group_get_course_user_groups` | Implemented | - | wired into a plato-mcp tool |
| `core_group_get_groups_for_selector` | Not wired (teacher-side group metadata) | #97 | same bucket as core_group_get_course_groups |
| `core_h5p_get_trusted_h5p_file` | Verified live, not wired | #115 | correctly handles invalid URL; no real H5P content to test further |
| `core_message_block_user` | Disabled site-wide | #87/#104/#105 | messaging disabled (errorcode=disabled) |
| `core_message_confirm_contact_request` | Disabled site-wide | #87/#104/#105 | messaging disabled (errorcode=disabled) |
| `core_message_create_contact_request` | Disabled site-wide | #87/#104/#105 | messaging disabled (errorcode=disabled) |
| `core_message_data_for_messagearea_search_messages` | Disabled site-wide | #87/#104/#105 | messaging disabled (errorcode=disabled) |
| `core_message_decline_contact_request` | Disabled site-wide | #87/#104/#105 | messaging disabled (errorcode=disabled) |
| `core_message_delete_contacts` | Disabled site-wide | #87/#104/#105 | messaging disabled (errorcode=disabled) |
| `core_message_delete_conversations_by_id` | Disabled site-wide | #87/#104/#105 | messaging disabled (errorcode=disabled) |
| `core_message_delete_message` | Disabled site-wide | #87/#104/#105 | messaging disabled (errorcode=disabled) |
| `core_message_delete_message_for_all_users` | Disabled site-wide | #87/#104/#105 | messaging disabled (errorcode=disabled) |
| `core_message_get_blocked_users` | Disabled site-wide | #87/#104/#105 | messaging disabled (errorcode=disabled) |
| `core_message_get_contact_requests` | Disabled site-wide | #87/#104/#105 | messaging disabled (errorcode=disabled) |
| `core_message_get_conversation` | Disabled site-wide | #87/#104/#105 | messaging disabled (errorcode=disabled) |
| `core_message_get_conversation_between_users` | Disabled site-wide | #87/#104/#105 | messaging disabled (errorcode=disabled) |
| `core_message_get_conversation_counts` | Disabled site-wide | #87/#104/#105 | messaging disabled (errorcode=disabled) |
| `core_message_get_conversation_members` | Disabled site-wide | #87/#104/#105 | messaging disabled (errorcode=disabled) |
| `core_message_get_conversation_messages` | Disabled site-wide | #87/#104/#105 | messaging disabled (errorcode=disabled) |
| `core_message_get_conversations` | Disabled site-wide | #87/#104/#105 | messaging disabled (errorcode=disabled) |
| `core_message_get_member_info` | Disabled site-wide | #87/#104/#105 | messaging disabled (errorcode=disabled) |
| `core_message_get_messages` | Implemented | - | wired into a plato-mcp tool |
| `core_message_get_received_contact_requests_count` | Disabled site-wide | #87/#104/#105 | messaging disabled (errorcode=disabled) |
| `core_message_get_self_conversation` | Disabled site-wide | #87/#104/#105 | messaging disabled (errorcode=disabled) |
| `core_message_get_unread_conversation_counts` | Disabled site-wide | #87/#104/#105 | messaging disabled (errorcode=disabled) |
| `core_message_get_unread_conversations_count` | Disabled site-wide | #87/#104/#105 | messaging disabled (errorcode=disabled) |
| `core_message_get_unread_notification_count` | Implemented | - | wired into a plato-mcp tool |
| `core_message_get_user_contacts` | Disabled site-wide | #87/#104/#105 | messaging disabled (errorcode=disabled) |
| `core_message_get_user_message_preferences` | Disabled site-wide | #87/#104/#105 | messaging disabled (errorcode=disabled) |
| `core_message_get_user_notification_preferences` | Disabled site-wide | #87/#104/#105 | messaging disabled (errorcode=disabled) |
| `core_message_mark_all_conversation_messages_as_read` | Disabled site-wide | #87/#104/#105 | messaging disabled (errorcode=disabled) |
| `core_message_mark_all_notifications_as_read` | Disabled site-wide | #87/#104/#105 | messaging disabled (errorcode=disabled) |
| `core_message_mark_message_read` | Disabled site-wide | #87/#104/#105 | messaging disabled (errorcode=disabled) |
| `core_message_mark_notification_read` | Disabled site-wide | #87/#104/#105 | messaging disabled (errorcode=disabled) |
| `core_message_message_processor_config_form` | Disabled site-wide | #87/#104/#105 | messaging disabled (errorcode=disabled) |
| `core_message_message_search_users` | Disabled site-wide | #87/#104/#105 | messaging disabled (errorcode=disabled) |
| `core_message_mute_conversations` | Disabled site-wide | #87/#104/#105 | messaging disabled (errorcode=disabled) |
| `core_message_search_contacts` | Disabled site-wide | #87/#104/#105 | messaging disabled (errorcode=disabled) |
| `core_message_send_instant_messages` | Disabled site-wide | #87/#104/#105 | messaging disabled (errorcode=disabled) |
| `core_message_send_messages_to_conversation` | Disabled site-wide | #87/#104/#105 | messaging disabled (errorcode=disabled) |
| `core_message_set_favourite_conversations` | Disabled site-wide | #87/#104/#105 | messaging disabled (errorcode=disabled) |
| `core_message_unblock_user` | Disabled site-wide | #87/#104/#105 | messaging disabled (errorcode=disabled) |
| `core_message_unmute_conversations` | Disabled site-wide | #87/#104/#105 | messaging disabled (errorcode=disabled) |
| `core_message_unset_favourite_conversations` | Disabled site-wide | #87/#104/#105 | messaging disabled (errorcode=disabled) |
| `core_my_view_page` | Not wired (view-logging) | #100/#103/#96 | mutates server-side viewed/completion state as a side effect of an AI read |
| `core_notes_create_notes` | Disabled site-wide | #112 | notesdisabled |
| `core_notes_delete_notes` | Disabled site-wide | #112 | notesdisabled |
| `core_notes_get_course_notes` | Disabled site-wide | #112 | notesdisabled |
| `core_notes_view_notes` | Disabled site-wide | #112 | notesdisabled |
| `core_question_update_flag` | Not called | #113 | question-attempt-specific, no standalone meaning |
| `core_rating_add_rating` | Not wired | #117 | write side of a family with no real item to attach to |
| `core_rating_get_item_ratings` | Verified live, not wired | #117 | invalidparameter; no real rateable item exists |
| `core_reportbuilder_can_view_system_report` | Verified live (empty) | #98 | no custom reports configured/shared |
| `core_reportbuilder_list_reports` | Verified live (empty) | #98 | no custom reports configured/shared |
| `core_reportbuilder_retrieve_report` | Verified live (empty) | #98 | no custom reports configured/shared |
| `core_reportbuilder_retrieve_system_report` | Verified live (empty) | #98 | no custom reports configured/shared |
| `core_reportbuilder_view_report` | Verified live (empty) | #98 | no custom reports configured/shared |
| `core_search_get_results` | Disabled site-wide | #98 | globalsearchdisabled |
| `core_search_get_search_areas_list` | Disabled site-wide | #98 | same globalsearchdisabled finding as core_search_get_results |
| `core_search_get_top_results` | Disabled site-wide | #98 | same globalsearchdisabled finding as core_search_get_results |
| `core_search_view_results` | Disabled site-wide | #98 | same globalsearchdisabled finding as core_search_get_results |
| `core_table_get_dynamic_table_content` | Not called | #113 | needs implementation-specific context, not a standalone AI concept |
| `core_tag_get_tag_areas` | Disabled site-wide | #117 | tagsaredisabled |
| `core_tag_get_tag_cloud` | Disabled site-wide | #117 | tagsaredisabled |
| `core_tag_get_tag_collections` | Disabled site-wide | #117 | tagsaredisabled |
| `core_tag_get_tagindex` | Disabled site-wide | #117 | tagsaredisabled |
| `core_tag_get_tagindex_per_area` | Disabled site-wide | #117 | tagsaredisabled |
| `core_user_add_user_device` | Not wired | #96 | native mobile push-notification device registration, no meaning for an MCP server |
| `core_user_add_user_private_files` | Implemented | - | wired into a plato-mcp tool |
| `core_user_agree_site_policy` | Not wired (policy decision) | #96 | an AI should not accept legal/site policies on a user's behalf |
| `core_user_get_course_user_profiles` | Implemented | - | wired into a plato-mcp tool |
| `core_user_get_private_files_info` | Implemented | - | wired into a plato-mcp tool |
| `core_user_get_user_preferences` | Implemented | - | wired into a plato-mcp tool |
| `core_user_get_users_by_field` | Not wired (privacy scope) | #96 | global user lookup, deliberately not exposed |
| `core_user_prepare_private_files_for_edition` | Not wired (same flow as add_user_private_files) | #96 | no second write path needed |
| `core_user_remove_user_device` | Not wired | #96 | native mobile push-notification device registration, no meaning for an MCP server |
| `core_user_set_user_preferences` | Not wired | #96 | no use case for an AI to mutate Moodle's own UI state |
| `core_user_update_picture` | Not wired | #96 | no real use case for an AI to change a profile picture unprompted |
| `core_user_update_private_files` | Not wired (same flow as add_user_private_files) | #96 | no second write path needed |
| `core_user_update_user_device_public_key` | Not wired | #96 | native mobile push-notification device registration, no meaning for an MCP server |
| `core_user_update_user_preferences` | Not wired | #96 | no use case for an AI to mutate Moodle's own UI state |
| `core_user_view_user_list` | Not wired (view-logging/scope) | #96 | view-logging |
| `core_user_view_user_profile` | Not wired (view-logging/scope) | #96 | view-logging |
| `core_webservice_get_site_info` | Implemented | - | wired into a plato-mcp tool |
| `core_xapi_delete_state` | Verified live, not wired | #115 | internal activity-tracking plumbing (invalidparameter on a minimal call) |
| `core_xapi_delete_states` | Verified live, not wired | #115 | internal activity-tracking plumbing (invalidparameter on a minimal call) |
| `core_xapi_get_state` | Verified live, not wired | #115 | internal activity-tracking plumbing (invalidparameter on a minimal call) |
| `core_xapi_get_states` | Verified live, not wired | #115 | internal activity-tracking plumbing (invalidparameter on a minimal call) |
| `core_xapi_post_state` | Verified live, not wired | #115 | internal activity-tracking plumbing (invalidparameter on a minimal call) |
| `core_xapi_statement_post` | Verified live, not wired | #115 | internal activity-tracking plumbing (invalidparameter on a minimal call) |
| `enrol_guest_get_instance_info` | Not called | #97 | low standalone value, no real guest-enrol instance |
| `enrol_guest_validate_password` | Not wired | #97 | guest-enrolment family, not pursued |
| `enrol_self_enrol_user` | Not wired (explicit user decision) | #97 | changes real account enrolment, no clear AI-assistant use case |
| `enrol_self_get_instance_info` | Not wired | #97 | self-enrolment family, not pursued per the enrol_self_enrol_user decision |
| `gradereport_grader_get_users_in_report` | Not wired (teacher-only UI widgets) | #95 | grading-UI support functions, not student data |
| `gradereport_overview_get_course_grades` | Implemented | - | wired into a plato-mcp tool |
| `gradereport_overview_view_grade_report` | Not wired (view-logging) | #95 | same view_* reasoning as other view-logging functions |
| `gradereport_singleview_get_grade_items_for_search_widget` | Not wired (teacher-only UI widgets) | #95 | grading-UI support functions, not student data |
| `gradereport_user_get_access_information` | Implemented | - | wired into a plato-mcp tool |
| `gradereport_user_get_grade_items` | Implemented | - | wired into a plato-mcp tool |
| `gradereport_user_get_grades_table` | Redundant/wrong-shaped | #95 | returns rendered HTML, not structured data |
| `gradereport_user_view_grade_report` | Not wired (view-logging) | #95 | same view_* reasoning as other view-logging functions |
| `message_airnotifier_are_notification_preferences_configured` | Verified live, not wired | #116 | push notifications not configured on this platform (is_system_configured=0) |
| `message_airnotifier_enable_device` | Verified live, not wired | #116 | push notifications not configured on this platform (is_system_configured=0) |
| `message_airnotifier_get_user_devices` | Verified live, not wired | #116 | push notifications not configured on this platform (is_system_configured=0) |
| `message_airnotifier_is_system_configured` | Verified live, not wired | #116 | push notifications not configured on this platform (is_system_configured=0) |
| `message_popup_get_popup_notifications` | Redundant | #116 | same data as get_unread_messages |
| `message_popup_get_unread_popup_notification_count` | Redundant | #116 | same data as get_unread_notification_count |
| `mod_assign_get_assignments` | Implemented | - | wired into a plato-mcp tool |
| `mod_assign_get_grades` | Permission-denied (teacher-only) | #95/#100 | No access rights in module context |
| `mod_assign_get_participant` | Permission-denied (teacher-only) | #101 | required_capability_exception/nopermission(s) |
| `mod_assign_get_submission_status` | Implemented | - | wired into a plato-mcp tool |
| `mod_assign_get_submissions` | Permission-denied (teacher-only) | #101 | required_capability_exception/nopermission(s) |
| `mod_assign_get_user_flags` | Permission-denied (teacher-only) | #95/#100 | No access rights in module context |
| `mod_assign_get_user_mappings` | Permission-denied (teacher-only) | #101 | required_capability_exception/nopermission(s) |
| `mod_assign_list_participants` | Permission-denied (teacher-only) | #101 | required_capability_exception/nopermission(s) |
| `mod_assign_lock_submissions` | Permission-denied (teacher-only) | #101 | required_capability_exception/nopermission(s) |
| `mod_assign_remove_submission` | Implemented | - | wired into a plato-mcp tool |
| `mod_assign_reveal_identities` | Permission-denied (teacher-only) | #101 | required_capability_exception/nopermission(s) |
| `mod_assign_revert_submissions_to_draft` | Permission-denied (teacher-only) | #101 | required_capability_exception/nopermission(s) |
| `mod_assign_save_grade` | Permission-denied (teacher-only) | #101 | required_capability_exception/nopermission(s) |
| `mod_assign_save_grades` | Permission-denied (teacher-only) | #101 | required_capability_exception/nopermission(s) |
| `mod_assign_save_submission` | Implemented | - | wired into a plato-mcp tool |
| `mod_assign_save_user_extensions` | Permission-denied (teacher-only) | #101 | required_capability_exception/nopermission(s) |
| `mod_assign_set_user_flags` | Permission-denied (teacher-only) | #101 | required_capability_exception/nopermission(s) |
| `mod_assign_start_submission` | Not wired | #84/#100 | draft-mode submission workflow (submissiondrafts=1); the real assignment uses direct submission (submissiondrafts=0), which submit_assignment already handles |
| `mod_assign_submit_for_grading` | Not wired | #84/#100 | draft-mode submission workflow (submissiondrafts=1); the real assignment uses direct submission (submissiondrafts=0), which submit_assignment already handles |
| `mod_assign_submit_grading_form` | Permission-denied (teacher-only) | #101 | required_capability_exception/nopermission(s) |
| `mod_assign_unlock_submissions` | Permission-denied (teacher-only) | #101 | required_capability_exception/nopermission(s) |
| `mod_assign_view_assign` | Not wired (view-logging) | #100/#103/#96 | mutates server-side viewed/completion state as a side effect of an AI read |
| `mod_assign_view_grading_table` | Permission-denied (teacher-only) | #101 | required_capability_exception/nopermission(s) |
| `mod_assign_view_submission_status` | Not wired (view-logging) | #100/#103/#96 | mutates server-side viewed/completion state as a side effect of an AI read |
| `mod_bigbluebuttonbn_can_join` | Not built (no real BBB) | #91 | no real meeting instance to verify against |
| `mod_bigbluebuttonbn_completion_validate` | Not built (no real BBB) | #91 | no real meeting instance to verify against |
| `mod_bigbluebuttonbn_end_meeting` | Not built (no real BBB) | #91 | no real meeting instance to verify against |
| `mod_bigbluebuttonbn_get_bigbluebuttonbns_by_courses` | Implemented | - | wired into a plato-mcp tool |
| `mod_bigbluebuttonbn_get_join_url` | Not built (no real BBB) | #91 | no real meeting instance to verify against |
| `mod_bigbluebuttonbn_get_recordings` | Not built (no real BBB) | #91 | no real meeting instance to verify against |
| `mod_bigbluebuttonbn_get_recordings_to_import` | Not built (no real BBB) | #91 | no real meeting instance to verify against |
| `mod_bigbluebuttonbn_meeting_info` | Not built (no real BBB) | #91 | no real meeting instance to verify against |
| `mod_bigbluebuttonbn_update_recording` | Not built (no real BBB) | #91 | no real meeting instance to verify against |
| `mod_bigbluebuttonbn_view_bigbluebuttonbn` | Not built (no real BBB) | #91 | no real meeting instance to verify against |
| `mod_book_get_books_by_courses` | Redundant | #92 | same data already in get_course_contents (diffed against real mod_url response) |
| `mod_book_view_book` | Not wired (view-logging) | #100/#103/#96 | mutates server-side viewed/completion state as a side effect of an AI read |
| `mod_chat_get_chat_latest_messages` | Not built (no real chat) | #111 | no real chat room to verify against |
| `mod_chat_get_chat_users` | Not built (no real chat) | #111 | no real chat room to verify against |
| `mod_chat_get_chats_by_courses` | Implemented | - | wired into a plato-mcp tool |
| `mod_chat_get_session_messages` | Not built (no real chat) | #111 | no real chat room to verify against |
| `mod_chat_get_sessions` | Not built (no real chat) | #111 | no real chat room to verify against |
| `mod_chat_login_user` | Not built (no real chat) | #111 | no real chat room to verify against |
| `mod_chat_send_chat_message` | Not built (no real chat) | #111 | no real chat room to verify against |
| `mod_chat_view_chat` | Not wired (view-logging) | #100/#103/#96 | mutates server-side viewed/completion state as a side effect of an AI read |
| `mod_chat_view_sessions` | Not wired (view-logging) | #100/#103/#96 | mutates server-side viewed/completion state as a side effect of an AI read |
| `mod_choice_delete_choice_responses` | Not built (no real choice) | #107 | no real choice activity to verify against |
| `mod_choice_get_choice_options` | Not built (no real choice) | #107 | no real choice activity to verify against |
| `mod_choice_get_choice_results` | Not built (no real choice) | #107 | no real choice activity to verify against |
| `mod_choice_get_choices_by_courses` | Implemented | - | wired into a plato-mcp tool |
| `mod_choice_submit_choice_response` | Not built (no real choice) | #107 | no real choice activity to verify against |
| `mod_choice_view_choice` | Not wired (view-logging) | #100/#103/#96 | mutates server-side viewed/completion state as a side effect of an AI read |
| `mod_data_add_entry` | Not built (no real database activity) | #110 | no real database activity to verify against (list tool only built) |
| `mod_data_approve_entry` | Not built (no real database activity) | #110 | no real database activity to verify against (list tool only built) |
| `mod_data_delete_entry` | Not built (no real database activity) | #110 | no real database activity to verify against (list tool only built) |
| `mod_data_get_data_access_information` | Not built (no real database activity) | #110 | no real database activity to verify against (list tool only built) |
| `mod_data_get_databases_by_courses` | Implemented | - | wired into a plato-mcp tool |
| `mod_data_get_entries` | Not built (no real database activity) | #110 | no real database activity to verify against (list tool only built) |
| `mod_data_get_entry` | Not built (no real database activity) | #110 | no real database activity to verify against (list tool only built) |
| `mod_data_get_fields` | Not built (no real database activity) | #110 | no real database activity to verify against (list tool only built) |
| `mod_data_search_entries` | Not built (no real database activity) | #110 | no real database activity to verify against (list tool only built) |
| `mod_data_update_entry` | Not built (no real database activity) | #110 | no real database activity to verify against (list tool only built) |
| `mod_data_view_database` | Not wired (view-logging) | #100/#103/#96 | mutates server-side viewed/completion state as a side effect of an AI read |
| `mod_feedback_get_analysis` | Not built (no real feedback) | #106 | no real feedback activity to verify against |
| `mod_feedback_get_current_completed_tmp` | Not built (no real feedback) | #106 | no real feedback activity to verify against |
| `mod_feedback_get_feedback_access_information` | Not built (no real feedback) | #106 | no real feedback activity to verify against |
| `mod_feedback_get_feedbacks_by_courses` | Implemented | - | wired into a plato-mcp tool |
| `mod_feedback_get_finished_responses` | Not built (no real feedback) | #106 | no real feedback activity to verify against |
| `mod_feedback_get_items` | Not built (no real feedback) | #106 | no real feedback activity to verify against |
| `mod_feedback_get_last_completed` | Not built (no real feedback) | #106 | no real feedback activity to verify against |
| `mod_feedback_get_non_respondents` | Not built (no real feedback) | #106 | no real feedback activity to verify against |
| `mod_feedback_get_page_items` | Not built (no real feedback) | #106 | no real feedback activity to verify against |
| `mod_feedback_get_responses_analysis` | Not built (no real feedback) | #106 | no real feedback activity to verify against |
| `mod_feedback_get_unfinished_responses` | Not built (no real feedback) | #106 | no real feedback activity to verify against |
| `mod_feedback_launch_feedback` | Not built (no real feedback) | #106 | no real feedback activity to verify against |
| `mod_feedback_process_page` | Not built (no real feedback) | #106 | no real feedback activity to verify against |
| `mod_feedback_view_feedback` | Not wired (view-logging) | #100/#103/#96 | mutates server-side viewed/completion state as a side effect of an AI read |
| `mod_folder_get_folders_by_courses` | Redundant | #92 | same data already in get_course_contents (diffed against real mod_url response) |
| `mod_folder_view_folder` | Not wired (view-logging) | #100/#103/#96 | mutates server-side viewed/completion state as a side effect of an AI read |
| `mod_forum_add_discussion` | Implemented | - | wired into a plato-mcp tool |
| `mod_forum_add_discussion_post` | Implemented | - | wired into a plato-mcp tool |
| `mod_forum_can_add_discussion` | Not wired | #86 | moderator-only or unverifiable without a real forum |
| `mod_forum_delete_post` | Not wired | #86 | moderator-only or unverifiable without a real forum |
| `mod_forum_get_discussion_post` | Not wired | #86 | moderator-only or unverifiable without a real forum |
| `mod_forum_get_discussion_posts` | Implemented | - | wired into a plato-mcp tool |
| `mod_forum_get_forum_access_information` | Not wired | #86 | moderator-only or unverifiable without a real forum |
| `mod_forum_get_forum_discussions` | Implemented | - | wired into a plato-mcp tool |
| `mod_forum_get_forums_by_courses` | Implemented | - | wired into a plato-mcp tool |
| `mod_forum_prepare_draft_area_for_post` | Not wired | #86 | moderator-only or unverifiable without a real forum |
| `mod_forum_set_lock_state` | Not wired | #86 | moderator-only or unverifiable without a real forum |
| `mod_forum_set_pin_state` | Not wired | #86 | moderator-only or unverifiable without a real forum |
| `mod_forum_set_subscription_state` | Not wired | #86 | moderator-only or unverifiable without a real forum |
| `mod_forum_toggle_favourite_state` | Not wired | #86 | moderator-only or unverifiable without a real forum |
| `mod_forum_update_discussion_post` | Not wired | #86 | moderator-only or unverifiable without a real forum |
| `mod_forum_view_forum` | Not wired (view-logging) | #100/#103/#96 | mutates server-side viewed/completion state as a side effect of an AI read |
| `mod_forum_view_forum_discussion` | Not wired (view-logging) | #100/#103/#96 | mutates server-side viewed/completion state as a side effect of an AI read |
| `mod_glossary_add_entry` | Not built (no real glossary) | #109 | no real glossary to verify against (list tool only built) |
| `mod_glossary_delete_entry` | Not built (no real glossary) | #109 | no real glossary to verify against (list tool only built) |
| `mod_glossary_get_authors` | Not built (no real glossary) | #109 | no real glossary to verify against (list tool only built) |
| `mod_glossary_get_categories` | Not built (no real glossary) | #109 | no real glossary to verify against (list tool only built) |
| `mod_glossary_get_entries_by_author` | Not built (no real glossary) | #109 | no real glossary to verify against (list tool only built) |
| `mod_glossary_get_entries_by_author_id` | Not built (no real glossary) | #109 | no real glossary to verify against (list tool only built) |
| `mod_glossary_get_entries_by_category` | Not built (no real glossary) | #109 | no real glossary to verify against (list tool only built) |
| `mod_glossary_get_entries_by_date` | Not built (no real glossary) | #109 | no real glossary to verify against (list tool only built) |
| `mod_glossary_get_entries_by_letter` | Not built (no real glossary) | #109 | no real glossary to verify against (list tool only built) |
| `mod_glossary_get_entries_by_search` | Not built (no real glossary) | #109 | no real glossary to verify against (list tool only built) |
| `mod_glossary_get_entries_by_term` | Not built (no real glossary) | #109 | no real glossary to verify against (list tool only built) |
| `mod_glossary_get_entries_to_approve` | Not built (no real glossary) | #109 | no real glossary to verify against (list tool only built) |
| `mod_glossary_get_entry_by_id` | Not built (no real glossary) | #109 | no real glossary to verify against (list tool only built) |
| `mod_glossary_get_glossaries_by_courses` | Implemented | - | wired into a plato-mcp tool |
| `mod_glossary_prepare_entry_for_edition` | Not built (no real glossary) | #109 | no real glossary to verify against (list tool only built) |
| `mod_glossary_update_entry` | Not built (no real glossary) | #109 | no real glossary to verify against (list tool only built) |
| `mod_glossary_view_entry` | Not wired (view-logging) | #100/#103/#96 | mutates server-side viewed/completion state as a side effect of an AI read |
| `mod_glossary_view_glossary` | Not wired (view-logging) | #100/#103/#96 | mutates server-side viewed/completion state as a side effect of an AI read |
| `mod_h5pactivity_get_attempts` | Not built (no real H5P) | #108 | no real H5P activity to verify against |
| `mod_h5pactivity_get_h5pactivities_by_courses` | Implemented | - | wired into a plato-mcp tool |
| `mod_h5pactivity_get_h5pactivity_access_information` | Not built (no real H5P) | #108 | no real H5P activity to verify against |
| `mod_h5pactivity_get_results` | Not built (no real H5P) | #108 | no real H5P activity to verify against |
| `mod_h5pactivity_get_user_attempts` | Not built (no real H5P) | #108 | no real H5P activity to verify against |
| `mod_h5pactivity_log_report_viewed` | Not built (no real H5P) | #108 | no real H5P activity to verify against |
| `mod_h5pactivity_view_h5pactivity` | Not wired (view-logging) | #100/#103/#96 | mutates server-side viewed/completion state as a side effect of an AI read |
| `mod_imscp_get_imscps_by_courses` | Redundant | #92 | same data already in get_course_contents (diffed against real mod_url response) |
| `mod_imscp_view_imscp` | Not wired (view-logging) | #100/#103/#96 | mutates server-side viewed/completion state as a side effect of an AI read |
| `mod_label_get_labels_by_courses` | Redundant | #92 | same data already in get_course_contents (diffed against real mod_url response) |
| `mod_lesson_finish_attempt` | Not built (no real lesson) | #93 | no real lesson to verify schema/write flow against |
| `mod_lesson_get_attempts_overview` | Not built (no real lesson) | #93 | no real lesson to verify schema/write flow against |
| `mod_lesson_get_content_pages_viewed` | Not built (no real lesson) | #93 | no real lesson to verify against |
| `mod_lesson_get_lesson` | Not built (no real lesson) | #93 | no real lesson to verify schema/write flow against |
| `mod_lesson_get_lesson_access_information` | Not built (no real lesson) | #93 | no real lesson to verify schema/write flow against |
| `mod_lesson_get_lessons_by_courses` | Implemented | - | wired into a plato-mcp tool |
| `mod_lesson_get_page_data` | Not built (no real lesson) | #93 | no real lesson to verify against |
| `mod_lesson_get_pages` | Not built (no real lesson) | #93 | no real lesson to verify schema/write flow against |
| `mod_lesson_get_pages_possible_jumps` | Not built (no real lesson) | #93 | no real lesson to verify schema/write flow against |
| `mod_lesson_get_questions_attempts` | Not built (no real lesson) | #93 | no real lesson to verify schema/write flow against |
| `mod_lesson_get_user_attempt` | Not built (no real lesson) | #93 | no real lesson to verify schema/write flow against |
| `mod_lesson_get_user_attempt_grade` | Not built (no real lesson) | #93 | no real lesson to verify schema/write flow against |
| `mod_lesson_get_user_grade` | Not built (no real lesson) | #93 | no real lesson to verify schema/write flow against |
| `mod_lesson_get_user_timers` | Not built (no real lesson) | #93 | no real lesson to verify schema/write flow against |
| `mod_lesson_launch_attempt` | Not built (no real lesson) | #93 | no real lesson to verify schema/write flow against |
| `mod_lesson_process_page` | Not built (no real lesson) | #93 | no real lesson to verify schema/write flow against |
| `mod_lesson_view_lesson` | Not wired (view-logging) | #100/#103/#96 | mutates server-side viewed/completion state as a side effect of an AI read |
| `mod_lti_get_ltis_by_courses` | Verified live (empty) | #92 | no real LTI module on this account |
| `mod_lti_get_tool_launch_data` | Unverified (no real instance) | #92 | the one function expected to NOT be redundant; no real LTI module exists |
| `mod_lti_view_lti` | Not wired (view-logging) | #100/#103/#96 | mutates server-side viewed/completion state as a side effect of an AI read |
| `mod_page_get_pages_by_courses` | Redundant | #92 | same data already in get_course_contents (diffed against real mod_url response) |
| `mod_page_view_page` | Not wired (view-logging) | #100/#103/#96 | mutates server-side viewed/completion state as a side effect of an AI read |
| `mod_quiz_get_attempt_access_information` | Not built (no real quiz) | #85 | no real quiz to verify against |
| `mod_quiz_get_attempt_data` | Implemented (unverified response shape) | #85 | wired, but response shape fully UNVERIFIED -- needs a real attempt id |
| `mod_quiz_get_attempt_review` | Implemented (unverified response shape) | #85 | wired, but response shape fully UNVERIFIED -- needs a real attempt id |
| `mod_quiz_get_attempt_summary` | Implemented (unverified response shape) | #85 | wired, but response shape fully UNVERIFIED -- needs a real attempt id |
| `mod_quiz_get_combined_review_options` | Implemented (unverified response shape) | #85 | parameter name confirmed live (progressed to DB lookup, not invalidparameter) |
| `mod_quiz_get_quiz_access_information` | Implemented (unverified response shape) | #85 | parameter name confirmed live (progressed to DB lookup, not invalidparameter) |
| `mod_quiz_get_quiz_feedback_for_grade` | Implemented (unverified response shape) | #85 | parameter name confirmed live (progressed to DB lookup, not invalidparameter) |
| `mod_quiz_get_quiz_required_qtypes` | Implemented (unverified response shape) | #85 | parameter name confirmed live (progressed to DB lookup, not invalidparameter) |
| `mod_quiz_get_quizzes_by_courses` | Implemented | - | wired into a plato-mcp tool |
| `mod_quiz_get_user_attempts` | Implemented | - | wired into a plato-mcp tool |
| `mod_quiz_get_user_best_grade` | Implemented | - | wired into a plato-mcp tool |
| `mod_quiz_process_attempt` | Implemented (unverified response shape) | #85 | wired, but response shape fully UNVERIFIED -- needs a real attempt id |
| `mod_quiz_save_attempt` | Implemented (unverified response shape) | #85 | wired, but response shape fully UNVERIFIED -- needs a real attempt id |
| `mod_quiz_start_attempt` | Implemented (unverified response shape) | #85 | parameter name confirmed live (progressed to DB lookup, not invalidparameter) |
| `mod_quiz_view_attempt` | Not wired (view-logging) | #100/#103/#96 | mutates server-side viewed/completion state as a side effect of an AI read |
| `mod_quiz_view_attempt_review` | Not wired (view-logging) | #100/#103/#96 | mutates server-side viewed/completion state as a side effect of an AI read |
| `mod_quiz_view_attempt_summary` | Not wired (view-logging) | #100/#103/#96 | mutates server-side viewed/completion state as a side effect of an AI read |
| `mod_quiz_view_quiz` | Not wired (view-logging) | #100/#103/#96 | mutates server-side viewed/completion state as a side effect of an AI read |
| `mod_resource_get_resources_by_courses` | Redundant | #92 | same data already in get_course_contents (diffed against real mod_url response) |
| `mod_resource_view_resource` | Not wired (view-logging) | #100/#103/#96 | mutates server-side viewed/completion state as a side effect of an AI read |
| `mod_scorm_get_scorm_access_information` | Not built (no real SCORM) | #108 | no real SCORM package to verify against |
| `mod_scorm_get_scorm_attempt_count` | Not built (no real SCORM) | #108 | no real SCORM package to verify against |
| `mod_scorm_get_scorm_sco_tracks` | Not built (no real SCORM) | #108 | no real SCORM package to verify against |
| `mod_scorm_get_scorm_scoes` | Not built (no real SCORM) | #108 | no real SCORM package to verify against |
| `mod_scorm_get_scorm_user_data` | Not built (no real SCORM) | #108 | no real SCORM package to verify against |
| `mod_scorm_get_scorms_by_courses` | Implemented | - | wired into a plato-mcp tool |
| `mod_scorm_insert_scorm_tracks` | Not built (no real SCORM) | #108 | no real SCORM package to verify against |
| `mod_scorm_launch_sco` | Not built (no real SCORM) | #108 | no real SCORM package to verify against |
| `mod_scorm_view_scorm` | Not wired (view-logging) | #100/#103/#96 | mutates server-side viewed/completion state as a side effect of an AI read |
| `mod_survey_get_questions` | Not built (no real survey) | #107 | no real survey activity to verify against |
| `mod_survey_get_surveys_by_courses` | Implemented | - | wired into a plato-mcp tool |
| `mod_survey_submit_answers` | Not built (no real survey) | #107 | no real survey activity to verify against |
| `mod_survey_view_survey` | Not wired (view-logging) | #100/#103/#96 | mutates server-side viewed/completion state as a side effect of an AI read |
| `mod_url_get_urls_by_courses` | Redundant | #92 | same data already in get_course_contents (diffed against real mod_url response) |
| `mod_url_view_url` | Not wired (view-logging) | #100/#103/#96 | mutates server-side viewed/completion state as a side effect of an AI read |
| `mod_wiki_edit_page` | Not built (no real wiki) | #111 | no real wiki to verify against (list tool only built) |
| `mod_wiki_get_page_contents` | Not built (no real wiki) | #111 | no real wiki to verify against (list tool only built) |
| `mod_wiki_get_page_for_editing` | Not built (no real wiki) | #111 | no real wiki to verify against (list tool only built) |
| `mod_wiki_get_subwiki_files` | Not built (no real wiki) | #111 | no real wiki to verify against (list tool only built) |
| `mod_wiki_get_subwiki_pages` | Not built (no real wiki) | #111 | no real wiki to verify against (list tool only built) |
| `mod_wiki_get_subwikis` | Not built (no real wiki) | #111 | no real wiki to verify against (list tool only built) |
| `mod_wiki_get_wikis_by_courses` | Implemented | - | wired into a plato-mcp tool |
| `mod_wiki_new_page` | Not built (no real wiki) | #111 | no real wiki to verify against (list tool only built) |
| `mod_wiki_view_page` | Not wired (view-logging) | #100/#103/#96 | mutates server-side viewed/completion state as a side effect of an AI read |
| `mod_wiki_view_wiki` | Not wired (view-logging) | #100/#103/#96 | mutates server-side viewed/completion state as a side effect of an AI read |
| `mod_workshop_add_submission` | Not built (no real workshop) | #94 | no real workshop to verify against |
| `mod_workshop_delete_submission` | Not built (no real workshop) | #94 | no real workshop to verify against |
| `mod_workshop_evaluate_assessment` | Not built (no real workshop) | #94 | no real workshop to verify against |
| `mod_workshop_evaluate_submission` | Not built (no real workshop) | #94 | no real workshop to verify against |
| `mod_workshop_get_assessment` | Not built (no real workshop) | #94 | no real workshop to verify against |
| `mod_workshop_get_assessment_form_definition` | Not built (no real workshop) | #94 | no real workshop to verify against |
| `mod_workshop_get_grades` | Not built (no real workshop) | #94 | no real workshop to verify against |
| `mod_workshop_get_grades_report` | Not built (no real workshop) | #94 | no real workshop to verify against |
| `mod_workshop_get_reviewer_assessments` | Not built (no real workshop) | #94 | no real workshop to verify against |
| `mod_workshop_get_submission` | Not built (no real workshop) | #94 | no real workshop to verify against |
| `mod_workshop_get_submission_assessments` | Not built (no real workshop) | #94 | no real workshop to verify against |
| `mod_workshop_get_submissions` | Not built (no real workshop) | #94 | no real workshop to verify against |
| `mod_workshop_get_user_plan` | Not built (no real workshop) | #94 | no real workshop to verify against |
| `mod_workshop_get_workshop_access_information` | Not built (no real workshop) | #94 | no real workshop to verify against |
| `mod_workshop_get_workshops_by_courses` | Implemented | - | wired into a plato-mcp tool |
| `mod_workshop_update_assessment` | Not built (no real workshop) | #94 | no real workshop to verify against |
| `mod_workshop_update_submission` | Not built (no real workshop) | #94 | no real workshop to verify against |
| `mod_workshop_view_submission` | Not wired (view-logging) | #100/#103/#96 | mutates server-side viewed/completion state as a side effect of an AI read |
| `mod_workshop_view_workshop` | Not wired (view-logging) | #100/#103/#96 | mutates server-side viewed/completion state as a side effect of an AI read |
| `mod_zoom_get_state` | Not built (no real Zoom) | #91 | invalidparameter on a minimal call, no real instance to verify shape against |
| `mod_zoom_grade_item_update` | Not built (no real Zoom) | #91 | no real Zoom instance to verify against |
| `report_insights_action_executed` | Not wired | #98 | teacher/analytics-dashboard concept |
| `report_insights_set_fixed_prediction` | Not wired | #98 | teacher/analytics-dashboard concept |
| `report_insights_set_notuseful_prediction` | Not wired | #98 | teacher/analytics-dashboard concept |
| `tool_analytics_potential_contexts` | Permission-denied (admin-only) | #113 | nopermissions (모델 관리) |
| `tool_dataprivacy_cancel_data_request` | Not wired (explicit decision) | #115 | an AI should not file/cancel a GDPR data request on a user's behalf |
| `tool_dataprivacy_contact_dpo` | Not wired | #115 | same policy-decision family as create/cancel_data_request |
| `tool_dataprivacy_create_data_request` | Not wired (explicit decision) | #115 | an AI should not file/cancel a GDPR data request on a user's behalf |
| `tool_dataprivacy_get_access_information` | Verified live, not wired | #115 | invalidparameter on a minimal call |
| `tool_dataprivacy_get_data_requests` | Permission-denied (DPO-only) | #115 | privacyofficeronly |
| `tool_lp_data_for_course_competencies_page` | Verified live, unavailable | #114 | competency frameworks not configured on this platform (core_course_get_user_navigation_options confirms competencies.available=false) |
| `tool_lp_data_for_plan_page` | Verified live, unavailable | #114 | competency frameworks not configured on this platform (core_course_get_user_navigation_options confirms competencies.available=false) |
| `tool_lp_data_for_plans_page` | Verified live, unavailable | #114 | competency frameworks not configured on this platform (core_course_get_user_navigation_options confirms competencies.available=false) |
| `tool_lp_data_for_user_competency_summary` | Verified live, unavailable | #114 | competency frameworks not configured on this platform (core_course_get_user_navigation_options confirms competencies.available=false) |
| `tool_lp_data_for_user_competency_summary_in_course` | Verified live, unavailable | #114 | competency frameworks not configured on this platform (core_course_get_user_navigation_options confirms competencies.available=false) |
| `tool_lp_data_for_user_competency_summary_in_plan` | Verified live, unavailable | #114 | competency frameworks not configured on this platform (core_course_get_user_navigation_options confirms competencies.available=false) |
| `tool_lp_data_for_user_evidence_list_page` | Verified live, unavailable | #114 | competency frameworks not configured on this platform (core_course_get_user_navigation_options confirms competencies.available=false) |
| `tool_lp_data_for_user_evidence_page` | Verified live, unavailable | #114 | competency frameworks not configured on this platform (core_course_get_user_navigation_options confirms competencies.available=false) |
| `tool_mobile_call_external_functions` | Evaluated, not adopted yet | #113 | ~40% faster for 2 batched calls (measured live); worth a future MoodleClient optimization, not built in this epic |
| `tool_mobile_get_autologin_key` | Not wired (security decision) | #113 | mints session/login credentials |
| `tool_mobile_get_config` | Verified live, not wired | #113 | app/site config data, not user data |
| `tool_mobile_get_content` | Verified live, not wired | #113 | app/site config data, not user data |
| `tool_mobile_get_plugins_supporting_mobile` | Verified live, not wired | #113 | app/site config data, not user data |
| `tool_mobile_get_public_config` | Verified live, not wired | #113 | app/site config data, not user data |
| `tool_mobile_get_tokens_for_qr_login` | Verified live, not wired | #113 | app/site config data, not user data |
| `tool_mobile_validate_subscription_key` | Verified live, not wired | #113 | app/site config data, not user data |
| `tool_moodlenet_search_courses` | Verified live, not wired | #113 | MoodleNet federation/discovery, no real use case |
| `tool_moodlenet_verify_webfinger` | Verified live, not wired | #113 | MoodleNet federation/discovery, no real use case |
| `tool_policy_get_user_acceptances` | Verified live (empty) | #115 | no policies configured requiring tracked acceptance |
| `tool_policy_set_acceptances_status` | Not wired (policy decision) | #115 | an AI should not accept site policies on a user's behalf |
