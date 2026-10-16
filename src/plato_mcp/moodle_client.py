"""Generic caller for PLATO's Moodle webservice REST API.

Wraps `webservice/rest/server.php`. Every official-API tool (Phase 1: courses,
contents, assignments, grades, calendar, messages) goes through this one
`MoodleClient.call()` rather than each having its own HTTP logic.
"""

import logging

import requests

from plato_mcp.auth import SessionManager
from plato_mcp.errors import MoodleAPIError
from plato_mcp.security import default_rate_limiter

logger = logging.getLogger("plato_mcp.moodle_client")

BASE_URL = "https://plato.pusan.ac.kr"
REST_ENDPOINT = f"{BASE_URL}/webservice/rest/server.php"
UPLOAD_ENDPOINT = f"{BASE_URL}/webservice/upload.php"


def flatten_params(params: dict) -> dict:
    """Expand list/dict-valued params into Moodle's bracket notation.

    e.g. flatten_params({"courseids": [1, 2]}) ->
         {"courseids[0]": 1, "courseids[1]": 2}
    """
    flat: dict = {}
    for key, value in params.items():
        if isinstance(value, (list, tuple)):
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    for subkey, subval in item.items():
                        flat[f"{key}[{i}][{subkey}]"] = subval
                else:
                    flat[f"{key}[{i}]"] = item
        else:
            flat[key] = value
    return flat


def _is_error_envelope(result: object) -> bool:
    return isinstance(result, dict) and "errorcode" in result


class MoodleClient:
    """Calls Moodle webservice functions for one PLATO session, with a
    single transparent retry when the cached wstoken has gone stale."""

    def __init__(
        self,
        session_manager: SessionManager,
        session_key: str,
        username: str,
        password: str,
        rest_endpoint: str = REST_ENDPOINT,
        upload_endpoint: str = UPLOAD_ENDPOINT,
        timeout: int = 15,
    ):
        self._session_manager = session_manager
        self._session_key = session_key
        self._username = username
        self._password = password
        self._rest_endpoint = rest_endpoint
        self._upload_endpoint = upload_endpoint
        self._timeout = timeout

    @property
    def session_key(self) -> str:
        """Exposed so callers outside call()/_raw_call() (e.g. files.py) can
        rate-limit their own requests against the same per-session budget."""
        return self._session_key

    def get_wstoken(self) -> str:
        """Ensure a logged-in session and return its wstoken.

        Used by files.py to build an authenticated pluginfile.php download
        URL (?token={wstoken}) -- that's not a webservice function call, so
        it doesn't go through call()/_raw_call(), but it needs the same
        cached-or-login session.
        """
        session = self._session_manager.get_or_login(
            self._session_key, self._username, self._password
        )
        return session.wstoken

    def call(self, wsfunction: str, **params) -> dict | list:
        session = self._session_manager.get_or_login(
            self._session_key, self._username, self._password
        )
        result = self._raw_call(session.wstoken, wsfunction, params)

        if _is_error_envelope(result) and result.get("errorcode") == "invalidtoken":
            logger.info("wstoken invalid for wsfunction=%s, refreshing once", wsfunction)
            session = self._session_manager.refresh(
                self._session_key, self._username, self._password
            )
            result = self._raw_call(session.wstoken, wsfunction, params)

        if _is_error_envelope(result):
            errorcode = result.get("errorcode")
            message = result.get("message") or result.get("error") or "Moodle API error"
            raise MoodleAPIError(message, errorcode=errorcode)

        return result

    def get_unused_draft_itemid(self) -> int:
        """Get a fresh draft-area itemid (`core_files_get_unused_draft_itemid`)
        to upload file(s) into before referencing them in a write call like
        `mod_assign_save_submission` (issue #84). Just a thin wrapper around
        `call()` -- kept as its own method because every file-upload caller
        needs this exact first step."""
        result = self.call("core_files_get_unused_draft_itemid")
        return result["itemid"]

    def upload_file(self, itemid: int, filename: str, content: bytes, filepath: str = "/") -> dict:
        """Upload one file's bytes into a draft area (issue #84).

        This is NOT a wsfunction call -- Moodle serves raw file upload from
        a dedicated endpoint, `/webservice/upload.php`, taking a multipart
        POST with the file bytes directly, separate from the JSON
        wsfunction protocol `call()`/`_raw_call()` use (confirmed live: no
        `core_files_upload` wsfunction exists at all, despite that name
        appearing in an earlier draft of this repo's own code comments).

        Returns the uploaded-file descriptor dict Moodle responds with
        (filename, filesize, itemid, etc.) -- confirmed live against this
        account's real draft area.
        """
        default_rate_limiter.check(self._session_key)
        session = self._session_manager.get_or_login(
            self._session_key, self._username, self._password
        )
        body = {"token": session.wstoken, "itemid": itemid, "filepath": filepath}
        files = {"file_1": (filename, content)}
        try:
            resp = requests.post(
                self._upload_endpoint, data=body, files=files, timeout=self._timeout
            )
            resp.raise_for_status()
        except requests.RequestException as e:
            raise MoodleAPIError(
                f"Moodle file upload failed (network or HTTP error): {type(e).__name__}",
                errorcode="upload_failed",
            ) from None

        result = resp.json()
        if _is_error_envelope(result):
            raise MoodleAPIError(
                result.get("message") or result.get("error") or "Moodle upload error",
                errorcode=result.get("errorcode"),
            )
        # upload.php returns a list of uploaded-file descriptors (one per
        # multipart field sent) rather than the single-dict error envelope
        # shape -- take the one file we sent.
        return result[0]

    def _raw_call(self, wstoken: str, wsfunction: str, params: dict) -> dict | list:
        # POST (data=), not GET (params=) -- wstoken is a live credential, and
        # a GET would put it in the request URL, which `requests`/urllib3
        # embed verbatim in HTTPError/ConnectionError messages on failure
        # (see the equivalent fix in auth.py._fetch_token for a live repro).
        default_rate_limiter.check(self._session_key)
        body = {"wstoken": wstoken, "wsfunction": wsfunction, "moodlewsrestformat": "json"}
        body.update(flatten_params(params))
        try:
            resp = requests.post(self._rest_endpoint, data=body, timeout=self._timeout)
            resp.raise_for_status()
        except requests.RequestException as e:
            logger.warning(
                "Moodle REST call failed for wsfunction=%s: %s", wsfunction, type(e).__name__
            )
            raise MoodleAPIError(
                f"Moodle REST call failed (network or HTTP error): {type(e).__name__}",
                errorcode="request_failed",
            ) from None
        return resp.json()
