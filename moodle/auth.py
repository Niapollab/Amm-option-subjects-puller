from dataclasses import dataclass
from moodle.constants import MOODLE_BASE_ADDRESS, MOODLE_SESSION_COOKIE_NAME
from moodle.exceptions import (
    CorruptedSessionError,
    OpeningSessionFileError,
    IncorrectCredentialsError,
    SavingSessionFileError,
)
from aiohttp import ClientSession
from aiofiles import open
import re
import json


@dataclass(frozen=True)
class MoodleCredentials:
    """Class to store Moodle login credentials."""

    login: str
    """The username for logging into Moodle."""

    password: str
    """The password for logging into Moodle."""


@dataclass(frozen=True)
class MoodleCachedSession:
    """Class to store a cached Moodle session."""

    login: str
    """The login username used for the Moodle session."""

    session_key: str
    """The key associated with the Moodle session, used for authentication."""

    moodle_session_cookie: str
    """The cookie string used to maintain the Moodle session."""


async def authorize(credentials: MoodleCredentials) -> MoodleCachedSession:
    """Authorize the user and create a new Moodle session.

    Args:
        credentials (MoodleCredentials): The login credentials for Moodle.

    Returns:
        MoodleCachedSession: An authenticated Moodle session.
    """

    auth_preparation_endpoint = f"{MOODLE_BASE_ADDRESS}/login/index.php"

    async with ClientSession() as session:
        async with session.get(auth_preparation_endpoint) as auth_preparation_response:
            login_token = _get_auth_preparation_token(
                await auth_preparation_response.text()
            )

        data = {
            "logintoken": login_token,
            "username": credentials.login,
            "password": credentials.password,
        }

        try:
            async with await session.post(
                f"{MOODLE_BASE_ADDRESS}/login/index.php", data=data
            ) as auth_response:
                text = await auth_response.text()
        except Exception:
            raise ConnectionError(
                f'Unable to connect to the endpoint "{auth_preparation_endpoint}". Check the internet connection.'
            )

        _ensure_valid_credentials(text)

        cached_session = MoodleCachedSession(
            credentials.login,
            _get_api_token_key(text),
            auth_response.history[0].cookies[MOODLE_SESSION_COOKIE_NAME].value,
        )

        return cached_session


async def restore_session(filename: str) -> MoodleCachedSession:
    """Restore a Moodle session from a cached session file.

    Args:
        filename (str): The path to the file containing the cached session.

    Returns:
        MoodleCachedSession: An authenticated Moodle session.
    """

    try:
        async with open(filename, "r") as file:
            auth_json = json.loads(await file.read())
    except Exception:
        raise OpeningSessionFileError("Unable to open session file.")

    try:
        login = auth_json["login"]
        session_key = auth_json["session_key"]
        moodle_session_cookie = auth_json["moodle_session_cookie"]
    except Exception:
        raise CorruptedSessionError("Session is corrupted.")

    cached_session = MoodleCachedSession(login, session_key, moodle_session_cookie)
    return cached_session


async def serialize_session(filename: str, session: MoodleCachedSession) -> None:
    """Read session from a cached session file.

    Args:
        filename (str): The path to the file containing the cached session.
        session (MoodleCachedSession): A cached Moodle session.
    """

    auth_info = {
        "login": session.login,
        "session_key": session.session_key,
        "moodle_session_cookie": session.moodle_session_cookie,
    }
    try:
        async with open(filename, "w") as file:
            json_object = json.dumps(auth_info, indent=4)
            await file.write(json_object)
    except Exception:
        raise SavingSessionFileError("Unable to save session file.")


def _get_api_token_key(html: str) -> str:
    match = re.search(r'<(?:.*?)name="sesskey"(?:.*?)value="(.*?)">', html)

    if not match:
        raise ValueError("Unable to get session token.")

    return match[1]


def _ensure_valid_credentials(html: str) -> None:
    match = re.search(r'<a href="#" id="loginerrormessage"', html)
    if match:
        raise IncorrectCredentialsError(
            "Invald credentials. Check login and password correctness."
        )


def _get_auth_preparation_token(html: str) -> str:
    match = re.search(r'<(?:.*?)name="logintoken"(?:.*?)value="(.*?)">', html)
    if not match:
        raise ValueError("Unable to get login token.")

    return match[1]
