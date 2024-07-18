from logic.models import Report, Student
from moodle.auth import MoodleCachedSession
from moodle.constants import MOODLE_BASE_ADDRESS, MOODLE_QUIZ_ACTIVITY_PATH
from moodle.html_parse_utils import enumerate_tag_by_name
from moodle.models import MoodleAttemptStatus
from moodle.progress import ProgressHandlerFactory
from moodle.session import MoodleSession as BaseMoodleSession
from typing import Sequence
import asyncio
import re


class MoodleSession(BaseMoodleSession):
    """Class to handle Moodle session operations and interactions."""

    def __init__(self, cached_session: MoodleCachedSession) -> None:
        """Initialize the Moodle session with a cached session.

        Args:
            cached_session (MoodleCachedSession): A cached session object for Moodle.
        """

        super().__init__(cached_session)

    async def get_quiz_report(
        self,
        quiz_id: str | int,
        progress_factory: ProgressHandlerFactory[int] | None = None,
        page_size: int = 30,
    ) -> Report:
        """Retrieve the quiz report with a list of students and their department priorities.

        Args:
            quiz_id (str | int): The ID of the quiz, either as a string or an integer.
            progress_factory (ProgressHandlerFactory[int] | None, optional): A factory for creating progress handlers. Defaults to None.
            page_size (int, optional): The number of attempts to fetch per page. Defaults to 30.

        Returns:
            Report: A report containing a sequence of student objects with their priorities.
        """

        students = []

        async for chunk in self.get_quiz_attempts(
            quiz_id, MoodleAttemptStatus.FINISHED, progress_factory, page_size
        ):
            department_priority_tasks = [
                (
                    attempt.fullname,
                    asyncio.create_task(self.get_department_priority(attempt.id)),
                )
                for attempt in chunk
            ]
            for fullname, department_priority_task in department_priority_tasks:
                priority = await department_priority_task
                students.append(Student(fullname, priority))

        return Report(students)

    async def get_department_priority(self, attempt_id: str | int) -> Sequence[str]:
        """Initialize the Moodle session with a cached session.

        Args:
            cached_session (MoodleCachedSession): A cached session object for Moodle.
        """

        if isinstance(attempt_id, str):
            attempt_id = MoodleSession._get_id_from_url(attempt_id, "attempt")

        params = {
            "attempt": attempt_id,
        }
        attempt_url = f"{MOODLE_QUIZ_ACTIVITY_PATH}/review.php"

        try:
            async with self._client.get(attempt_url, params=params) as response:
                attempt_html = await response.text()
        except Exception:
            raise ConnectionError(
                f'Unable to connect to the endpoint "{MOODLE_BASE_ADDRESS}{attempt_url}". Check the internet connection.'
            )

        return MoodleSession.__parse_department_priority(attempt_html)

    @staticmethod
    def __parse_department_priority(attempt_html: str) -> Sequence[str]:
        I_TAG_PATTERN = re.compile(r"<i.*?>.*?<\/i>")

        priority = []
        for tag in enumerate_tag_by_name(attempt_html, "li"):
            if "id" in tag.attributes and "ordering_item" in tag.attributes["id"]:
                priority.append(I_TAG_PATTERN.sub("", tag.inner_text or "").strip())

        return priority
