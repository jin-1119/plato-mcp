"""Pydantic response schemas for Phase 1 (official-API) tools.

Every model uses `extra="ignore"` -- Moodle's JSON payloads carry many more
fields than we care about, and picking out only the ones we need keeps the
tool output focused instead of dumping the raw API response at the LLM.
"""

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator, model_validator


def _epoch_to_datetime(value: int | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromtimestamp(value, tz=UTC)


class CourseSummary(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    fullname: str
    shortname: str
    visible: bool = True
    # Moodle has no separate "term/semester" field -- startdate/enddate (from
    # core_enrol_get_users_courses) are the only structured signal of which
    # semester a course belongs to. enddate=0 means "no end date set" (some
    # long-running programs are like this), which maps to None below.
    startdate: datetime | None = None
    enddate: datetime | None = None

    @field_validator("startdate", "enddate", mode="before")
    @classmethod
    def _convert_epoch(cls, v: int | None) -> datetime | None:
        return _epoch_to_datetime(v)


class FileEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")

    filename: str
    fileurl: str
    filesize: int | None = None
    type: str | None = None
    mimetype: str | None = None
    author: str | None = Field(
        default=None,
        description=(
            "Who uploaded this file -- course materials are almost always uploaded "
            "by staff, not classmates (see docs/pii_review.md, issue #36)."
        ),
    )
    timemodified: datetime | None = None
    needs_token: bool = Field(
        default=True,
        description="Append ?token={wstoken} to fileurl before downloading (see issue #20).",
    )

    @field_validator("timemodified", mode="before")
    @classmethod
    def _convert_epoch(cls, v: int | None) -> datetime | None:
        return _epoch_to_datetime(v)


class CourseModule(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    name: str
    modname: str
    url: str | None = None
    completed: bool | None = Field(
        default=None, description="Whether this account has marked/viewed this module complete."
    )
    contents: list[FileEntry] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _extract_completed(cls, data):
        # Moodle nests completion under completiondata.isoverallcomplete rather than
        # a flat field -- pull it up so callers don't need to know that shape.
        if isinstance(data, dict) and "completed" not in data:
            completiondata = data.get("completiondata")
            if isinstance(completiondata, dict):
                data = {**data, "completed": completiondata.get("isoverallcomplete")}
        return data


class CourseSection(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    name: str
    modules: list[CourseModule] = Field(default_factory=list)


class AssignmentConfig(BaseModel):
    """One raw row of `mod_assign_get_assignments`'s `configs` array -- a
    flat (plugin, subtype, name, value) tuple describing one submission or
    feedback plugin's settings for this assignment. `value` is always a
    string in the API response, even for booleans/numbers (confirmed live,
    issue #84 -- e.g. `{"plugin": "file", "subtype": "assignsubmission",
    "name": "maxsubmissionsizebytes", "value": "1073741824"}`)."""

    model_config = ConfigDict(extra="ignore")

    plugin: str
    subtype: str
    name: str
    value: str


class SubmissionPluginConfig(BaseModel):
    """Derived, structured view of one submission plugin's `configs` rows
    (e.g. the 'file' or 'onlinetext' assignsubmission plugin) -- answers
    "can I submit a file to this assignment, and under what limits" without
    the caller having to scan the raw `configs` array themselves.

    `known` distinguishes "Moodle told us this plugin is disabled" from
    "Moodle's response didn't include config rows for this plugin at all"
    (e.g. an older cached response, or a Moodle version/permission that
    omits `configs`) -- callers should fail closed on an explicit disable
    but not necessarily on missing information. `enabled` defaults to
    False either way since it's the safe default for display purposes."""

    model_config = ConfigDict(extra="ignore")

    known: bool = False
    enabled: bool = False
    max_files: int | None = None
    max_size_bytes: int | None = None
    allowed_extensions: list[str] = Field(default_factory=list)


class AssignmentSummary(BaseModel):
    """Schema verified against Moodle 4.5's mod_assign/externallib.php source
    (PLATO runs 4.5.13), and -- as of issue #84 -- against a real live
    response (course 5968's "중간고사 전 과제", the first real assignment to
    ever exist on the test account).
    """

    model_config = ConfigDict(extra="ignore")

    id: int
    cmid: int | None = None
    name: str
    courseid: int | None = None
    duedate: datetime | None = None
    allowsubmissionsfromdate: datetime | None = None
    cutoffdate: datetime | None = Field(
        default=None, description="Hard deadline; submissions after this need an extension."
    )
    gradingduedate: datetime | None = None
    intro: str | None = Field(default=None, description="Assignment instructions (HTML).")
    introformat: int | None = None
    introfiles: list[FileEntry] = Field(default_factory=list)
    introattachments: list[FileEntry] = Field(default_factory=list)
    activity: str | None = Field(
        default=None, description="Some assignment types carry a separate 'activity' description."
    )
    activityformat: int | None = None
    activityattachments: list[FileEntry] = Field(default_factory=list)
    maxattempts: int | None = None
    attemptreopenmethod: str | None = None
    teamsubmission: bool | None = None
    requireallteammemberssubmit: bool | None = None
    teamsubmissiongroupingid: int | None = None
    configs: list[AssignmentConfig] = Field(
        default_factory=list,
        description="Raw submission/feedback plugin settings. Prefer "
        "file_submission/onlinetext_submission over reading this directly.",
    )

    @field_validator(
        "duedate", "allowsubmissionsfromdate", "cutoffdate", "gradingduedate", mode="before"
    )
    @classmethod
    def _convert_epoch(cls, v: int | None) -> datetime | None:
        return _epoch_to_datetime(v)

    @field_validator("teamsubmission", "requireallteammemberssubmit", mode="before")
    @classmethod
    def _convert_int_bool(cls, v: int | None) -> bool | None:
        return None if v is None else bool(v)

    def _submission_plugin_config(self, plugin: str) -> SubmissionPluginConfig:
        rows = [c for c in self.configs if c.subtype == "assignsubmission" and c.plugin == plugin]
        values = {c.name: c.value for c in rows}
        raw_types = values.get("filetypeslist", "")
        extensions = [ext.strip() for ext in raw_types.split(",") if ext.strip()]
        max_files = values.get("maxfilesubmissions")
        max_size = values.get("maxsubmissionsizebytes")
        return SubmissionPluginConfig(
            known=bool(rows),
            enabled=values.get("enabled") == "1",
            max_files=int(max_files) if max_files else None,
            max_size_bytes=int(max_size) if max_size else None,
            allowed_extensions=extensions,
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def file_submission(self) -> SubmissionPluginConfig:
        """Whether/how this assignment accepts file attachments. Surfaced
        as a computed field (not just a raw `configs` scan) so an AI caller
        can tell ahead of time whether submit_assignment's file_paths
        argument will be accepted, and under what limits -- the gap that
        prompted issue #84 in the first place."""
        return self._submission_plugin_config("file")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def onlinetext_submission(self) -> SubmissionPluginConfig:
        """Whether this assignment accepts plain-text online submissions."""
        return self._submission_plugin_config("onlinetext")


class PluginEditorField(BaseModel):
    """One text field of a submission/feedback plugin -- e.g. the actual
    written comment text for the 'comments' feedback plugin."""

    model_config = ConfigDict(extra="ignore")

    name: str
    description: str | None = None
    text: str | None = None
    format: int | None = None


class PluginFileArea(BaseModel):
    model_config = ConfigDict(extra="ignore")

    area: str
    files: list[FileEntry] = Field(default_factory=list)


class AssignmentPlugin(BaseModel):
    """A submission or feedback plugin (e.g. 'file', 'onlinetext', 'comments')
    and the actual content it holds for one submission/grade."""

    model_config = ConfigDict(extra="ignore")

    type: str
    name: str
    fileareas: list[PluginFileArea] = Field(default_factory=list)
    editorfields: list[PluginEditorField] = Field(default_factory=list)


class SubmissionStatus(BaseModel):
    model_config = ConfigDict(extra="ignore")

    submitted: bool
    status: str | None = None
    late: bool = False
    timemodified: datetime | None = None
    cansubmit: bool | None = None
    locked: bool | None = None
    extensionduedate: datetime | None = Field(
        default=None, description="Individual extension granted to this student, if any."
    )
    gradingstatus: str | None = None

    @field_validator("timemodified", "extensionduedate", mode="before")
    @classmethod
    def _convert_epoch(cls, v: int | None) -> datetime | None:
        return _epoch_to_datetime(v)


class GradeInfo(BaseModel):
    model_config = ConfigDict(extra="ignore")

    grade: str | None = Field(default=None, description="Raw grade value (Moodle returns as text).")
    gradefordisplay: str | None = None
    timemodified: datetime | None = None
    grader: int | None = None

    @field_validator("timemodified", mode="before")
    @classmethod
    def _convert_epoch(cls, v: int | None) -> datetime | None:
        return _epoch_to_datetime(v)


class SubmissionFeedback(BaseModel):
    model_config = ConfigDict(extra="ignore")

    grade: GradeInfo | None = None
    gradefordisplay: str | None = None
    gradeddate: datetime | None = None
    plugins: list[AssignmentPlugin] = Field(
        default_factory=list, description="Includes the instructor's written feedback comments."
    )

    @field_validator("gradeddate", mode="before")
    @classmethod
    def _convert_epoch(cls, v: int | None) -> datetime | None:
        return _epoch_to_datetime(v)


class SubmissionInfo(BaseModel):
    """Lightweight submission snapshot used inside previousattempts (as
    opposed to SubmissionStatus, which is this account's *current* status)."""

    model_config = ConfigDict(extra="ignore")

    status: str | None = None
    timemodified: datetime | None = None

    @field_validator("timemodified", mode="before")
    @classmethod
    def _convert_epoch(cls, v: int | None) -> datetime | None:
        return _epoch_to_datetime(v)


class PreviousAttempt(BaseModel):
    model_config = ConfigDict(extra="ignore")

    attemptnumber: int
    submission: SubmissionInfo | None = None
    grade: GradeInfo | None = None
    feedbackplugins: list[AssignmentPlugin] = Field(default_factory=list)


class AssignmentExtraData(BaseModel):
    """Maps from Moodle's `assignmentdata` (attachments nested under
    `attachments.intro`/`attachments.activity`) to a flat shape."""

    model_config = ConfigDict(extra="ignore")

    activity: str | None = None
    attachments_intro: list[FileEntry] = Field(default_factory=list)
    attachments_activity: list[FileEntry] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _flatten_attachments(cls, data):
        if isinstance(data, dict):
            attachments = data.get("attachments") or {}
            data = {
                **data,
                "attachments_intro": attachments.get("intro", []),
                "attachments_activity": attachments.get("activity", []),
            }
        return data


class AssignmentDetail(BaseModel):
    model_config = ConfigDict(extra="ignore")

    assignment: AssignmentSummary
    submission: SubmissionStatus | None = None
    feedback: SubmissionFeedback | None = None
    previousattempts: list[PreviousAttempt] = Field(default_factory=list)
    extra: AssignmentExtraData | None = None


class GradeItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    itemname: str | None = None
    itemtype: str
    graderaw: float | None = None
    gradeformatted: str | None = None
    grademin: float | None = None
    grademax: float | None = None
    feedback: str | None = None


class GradesResult(BaseModel):
    courseid: int
    available: bool
    gradeitems: list[GradeItem] = Field(default_factory=list)
    message: str | None = None


class CalendarEvent(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    name: str
    description: str | None = Field(default=None, description="HTML-formatted event description.")
    eventtype: str | None = None
    courseid: int | None = None
    timestart: datetime | None = None

    @field_validator("timestart", mode="before")
    @classmethod
    def _convert_epoch(cls, v: int | None) -> datetime | None:
        return _epoch_to_datetime(v)


class MessageItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    useridfrom: int
    userfromfullname: str | None = Field(
        default=None,
        description=(
            "Sender's display name -- these are notifications addressed to this "
            "account (e.g. system alerts), not a public feed of other users' "
            "messages (see docs/pii_review.md, issue #36)."
        ),
    )
    subject: str | None = None
    fullmessage: str | None = None
    eventtype: str | None = None
    timecreated: datetime | None = None

    @field_validator("timecreated", mode="before")
    @classmethod
    def _convert_epoch(cls, v: int | None) -> datetime | None:
        return _epoch_to_datetime(v)
