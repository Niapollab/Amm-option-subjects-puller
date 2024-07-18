from io import BytesIO
from aiohttp import ClientSession
from moodle.auth import MoodleCachedSession
from moodle.constants import (
    MOODLE_BASE_ADDRESS,
    MOODLE_CHOICE_ACTIVITY_PATH,
    MOODLE_COURSE_VIEW_PATH,
    MOODLE_MAIN_PAGE_PATH,
    MOODLE_QUIZ_ACTIVITY_PATH,
    MOODLE_SESSION_COOKIE_NAME,
)
from moodle.html_parse_utils import HtmlTag, enumerate_tag_by_name
from moodle.progress import ProgressHandler, ProgressHandlerFactory
from moodle.models import (
    ChoiceMoodleActivity,
    MoodleActivity,
    MoodleAttemptStatus,
    MoodleCourse,
    MoodleQuizAttempt,
    MoodleSection,
    QuizMoodleActivity,
)
from typing import AsyncIterable, Self, Sequence
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
            course_id = MoodleSession._get_id_from_url(course_id)

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
            report_id = MoodleSession._get_id_from_url(report_id)

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

    async def get_quiz_attempts(
        self,
        quiz_id: str | int,
        query: MoodleAttemptStatus | None = None,
        progress_factory: ProgressHandlerFactory[int] | None = None,
        page_size: int = 30,
    ) -> AsyncIterable[Sequence[MoodleQuizAttempt]]:
        """Retrieve quiz attempts for a given quiz ID, optionally filtered by status.

        Args:
            quiz_id (str | int): The ID or URL of the quiz.
            query (MoodleAttemptStatus, optional): The status filter for the quiz attempts. Defaults to FINISHED.
            progress_factory (ProgressHandlerFactory[int], optional): Factory to create a progress handler to track the progress of fetching attempts. Defaults to None.
            page_size (int, optional): The number of attempts to fetch per page. Defaults to 30.

        Yields:
            AsyncIterable[Sequence[MoodleQuizAttempt]]: An asynchronous iterable of sequences of MoodleQuizAttempt.
        """

        query = query or MoodleAttemptStatus.FINISHED
        progress_factory = progress_factory or ProgressHandler.mock

        if isinstance(quiz_id, str):
            quiz_id = MoodleSession._get_id_from_url(quiz_id)
        quiz_url = f"{MOODLE_QUIZ_ACTIVITY_PATH}/report.php"

        page = 0
        uploaded_count = 0

        while True:
            data = {
                "id": quiz_id,
                "mode": "overview",
                "attempts": "enrolled_with",
                "stateinprogress": int(query == MoodleAttemptStatus.IN_PROGRESS),
                "stateoverdue": int(query == MoodleAttemptStatus.OVERDUE),
                "statefinished": int(query == MoodleAttemptStatus.FINISHED),
                "statebandoned": int(query == MoodleAttemptStatus.BANDONED),
                "onlygraded": int(query == MoodleAttemptStatus.ONLY_BEST_GRADED),
                "onlyregraded": int(query == MoodleAttemptStatus.ONLY_REGRADED),
                "pagesize": page_size,
                "slotmarks": 0,
                "page": page,
                "sesskey": self._session_key,
            }

            try:
                async with self._client.post(quiz_url, data=data) as response:
                    attempts_page_html = await response.text()
            except Exception:
                raise ConnectionError(
                    f'Unable to connect to the endpoint "{MOODLE_BASE_ADDRESS}{quiz_url}". Check the internet connection.'
                )

            if page == 0:
                attempts_count: int = MoodleSession.__get_attempts_count(
                    attempts_page_html
                )
                progress = progress_factory(attempts_count)

            current_page_size = min(page_size, attempts_count - uploaded_count)
            attempts = MoodleSession.__parse_attempts_page(
                attempts_page_html, current_page_size
            )

            uploaded_count += len(attempts)
            page += 1

            progress.update(uploaded_count)
            yield attempts

            if uploaded_count >= attempts_count:
                break

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
    def _get_id_from_url(url: str, param_name: str = "id") -> int:
        match = re.search(rf"{param_name}=(\d+)", url)
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

                if MOODLE_QUIZ_ACTIVITY_PATH in inner_tag.attributes["href"]:
                    return QuizMoodleActivity(id, name)

        return MoodleActivity(id, name)

    @staticmethod
    def __get_attempts_count(attempts_page_html: str) -> int:
        for tag in enumerate_tag_by_name(attempts_page_html, "div"):
            if (
                "class" in tag.attributes
                and "quizattemptcounts" in tag.attributes["class"]
            ):
                return int(re.sub(r"\D", "", tag.inner_text or ""))

        raise ValueError("Unable to find attempts count.")

    @staticmethod
    def __parse_attempts_page(
        attempts_page_html: str, page_size: int
    ) -> Sequence[MoodleQuizAttempt]:
        attempts = []

        for index, tag in enumerate(enumerate_tag_by_name(attempts_page_html, "tr")):
            if index > page_size:
                break

            if (
                "id" in tag.attributes
                and "mod-quiz-report-overview" in tag.attributes["id"]
            ):
                attempts.append(MoodleSession.__parse_attempt(tag))

        return attempts

    @staticmethod
    def __parse_attempt(attempt_tag: HtmlTag) -> MoodleQuizAttempt:
        tags = iter(attempt_tag.enumerate_tag_by_name("td"))

        # Skip checkbox column
        _ = next(tags)

        student_info_tag = next(tags)
        finished = (
            "class" in attempt_tag.attributes
            and "gradedattempt" in attempt_tag.attributes["class"]
        )

        login = next(tags).inner_text
        if not login:
            raise ValueError("Unable to parse login in attempt info.")

        email = next(tags).inner_text
        if not email:
            raise ValueError("Unable to parse email in attempt info.")

        fullname_tag, id_tag = student_info_tag.enumerate_tag_by_name("a")
        fullname = fullname_tag.inner_text
        if not fullname:
            raise ValueError("Unable to parse fullname in attempt info.")

        url = (
            id_tag.attributes["href"]
            if "href" in id_tag.attributes
            and MOODLE_QUIZ_ACTIVITY_PATH in id_tag.attributes["href"]
            else None
        )
        if not url:
            raise ValueError("Unable to parse id in attempt info.")

        id = MoodleSession._get_id_from_url(url, "attempt")

        return MoodleQuizAttempt(id, fullname, login, email, finished)
