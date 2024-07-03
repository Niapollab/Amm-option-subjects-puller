from io import BytesIO
from aiohttp import ClientSession
from moodle.auth import MoodleCachedSession
from moodle.constants import (
    MOODLE_BASE_ADDRESS,
    MOODLE_CHOICE_ACTIVITY_PATH,
    MOODLE_COURSE_VIEW_PATH,
    MOODLE_MAIN_PAGE_PATH,
    MOODLE_SESSION_COOKIE_NAME,
)
from moodle.html_parse_utils import HtmlTag, enumerate_tag_by_name
from moodle.models import (
    ChoiceMoodleActivity,
    MoodleActivity,
    MoodleCourse,
    MoodleSection,
)
from typing import Self, Sequence
import pandas as pd
import re


class MoodleSession:
    """Class to manage a Moodle session, allowing interaction with Moodle's API."""

    _client: ClientSession
    """Instance of `ClientSession` used to handle HTTP requests and maintain a session."""

    _session_key: str
    """Key representing the current session, used to authenticate and manage session state."""

    def __init__(self, cached_session: MoodleCachedSession) -> None:
        """Initialize the Moodle session with a cached session.

        Args:
            cached_session (MoodleCachedSession): A cached session object for Moodle.
        """

        self._client = ClientSession(
            cookies={
                MOODLE_SESSION_COOKIE_NAME: cached_session.moodle_session_cookie,
            },
            base_url=MOODLE_BASE_ADDRESS,
        )
        self._session_key = cached_session.session_key

    async def is_valid(self) -> bool:
        """Check if the current session is still valid.

        Returns:
            bool: True if the session is valid, False otherwise.
        """

        async with self._client.get(url=MOODLE_MAIN_PAGE_PATH) as response:
            # Session is valid if is redirected to /my path
            return MOODLE_MAIN_PAGE_PATH in str(response.url)

    async def get_course(self, course_id: str | int) -> MoodleCourse:
        """Retrieve information about a specific Moodle course.

        Args:
            course_id (str | int): The course ID or a URL string containing the course ID.

        Returns:
            MoodleCourse: An object representing the Moodle course.
        """

        if isinstance(course_id, str):
            course_id = MoodleSession.__get_id_from_url(course_id)

        course_url = f"{MOODLE_COURSE_VIEW_PATH}/view.php?id={course_id}"
        try:
            async with self._client.get(course_url) as response:
                course_html = await response.text()
        except Exception:
            raise ConnectionError(
                f'Unable to connect to the endpoint "{MOODLE_BASE_ADDRESS}{course_url}". Check the internet connection.'
            )

        course_name = MoodleSession.__get_course_name(course_html)
        course_section = MoodleSession.__get_sections(course_html)

        return MoodleCourse(course_id, course_name, course_section)

    async def get_excel_report(self, report_id: str | int) -> pd.DataFrame:
        """Retrieve a Excel report from Moodle.

        Args:
            report_id (str | int): The ID or URL of the report to be retrieved.

        Returns:
            pd.DataFrame: A DataFrame containing the report data formatted for Excel.
        """

        if isinstance(report_id, str):
            report_id = MoodleSession.__get_id_from_url(report_id)

        report_url = f"{MOODLE_CHOICE_ACTIVITY_PATH}/report.php"
        params = {
            "id": report_id,
            "download": "xls",
            "sesskey": self._session_key,
        }

        try:
            async with self._client.get(report_url, params=params) as response:
                report_xsls_bytes = await response.content.read()
        except Exception:
            raise ConnectionError(
                f'Unable to connect to the endpoint "{MOODLE_BASE_ADDRESS}{report_url}". Check the internet connection.'
            )

        return pd.read_excel(BytesIO(report_xsls_bytes))

    async def close(self) -> None:
        """Close the current Moodle session."""

        await self._client.close()

    async def __aenter__(self) -> Self:
        """Enter the asynchronous context manager.

        Returns:
            Self: The current instance of MoodleSession.
        """

        return self

    async def __aexit__(self, *_) -> None:
        """Exit the asynchronous context manager.

        Args:
            *_: Optional arguments (ignored).

        Closes the session upon exiting the context manager.
        """

        return await self.close()

    @staticmethod
    def __get_id_from_url(url: str) -> int:
        match = re.search(r"id=(\d+)", url)
        if not match:
            raise ValueError("Unable to get course identifier.")

        return int(match[1])

    @staticmethod
    def __get_course_name(course_html: str) -> str:
        for tag in enumerate_tag_by_name(course_html, "a"):
            if (
                "href" in tag.attributes
                and "title" in tag.attributes
                and MOODLE_COURSE_VIEW_PATH in tag.attributes["href"]
            ):
                return tag.attributes["title"].strip()

        raise ValueError("Unable to find course title.")

    @staticmethod
    def __get_sections(course_html: str) -> Sequence[MoodleSection]:
        sections = []
        for tag in enumerate_tag_by_name(course_html, "li"):
            if (
                "id" in tag.attributes
                and "data-id" in tag.attributes
                and "section" in tag.attributes["id"]
            ):
                try:
                    section_id = int(tag.attributes["data-id"])
                    if not tag.inner_text:
                        raise ValueError("Unable to find name of section.")

                    h3_iter = iter(tag.enumerate_tag_by_name("h3"))
                    section_name = next(h3_iter).inner_text
                    if not section_name:
                        raise ValueError("Unable to find name of section.")

                    section_name = section_name.strip()

                    activities = MoodleSession.__get_activities(tag.inner_text)
                    section = MoodleSection(section_id, section_name, activities)

                    sections.append(section)
                except ValueError:
                    raise
                except Exception:
                    raise ValueError("Unable to parse section.")

        return sections

    @staticmethod
    def __get_activities(section_html: str) -> Sequence[MoodleActivity]:
        activities = []
        for tag in enumerate_tag_by_name(section_html, "li"):
            if (
                "class" in tag.attributes
                and "data-id" in tag.attributes
                and "activity" in tag.attributes["class"]
            ):
                activity_id = int(tag.attributes["data-id"])

                activity_name_iter = iter(
                    inner_tag.attributes["data-activityname"]
                    for inner_tag in tag.enumerate_tag_by_name("div")
                    if "data-activityname" in inner_tag.attributes
                )
                activity_name = next(activity_name_iter).strip()

                activity = MoodleSession.__build_activity(
                    activity_id, activity_name, tag
                )
                activities.append(activity)

        return activities

    @staticmethod
    def __build_activity(id: int, name: str, section_tag: HtmlTag) -> MoodleActivity:
        for inner_tag in section_tag.enumerate_tag_by_name("a"):
            if "href" in inner_tag.attributes:
                if MOODLE_CHOICE_ACTIVITY_PATH in inner_tag.attributes["href"]:
                    return ChoiceMoodleActivity(id, name)

        return MoodleActivity(id, name)
