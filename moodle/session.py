from moodle.auth import MoodleCachedSession
from moodle.constants import MOODLE_BASE_ADDRESS
from moodle.models import MoodleCourse
from typing import Self
import pandas as pd


class MoodleSession:
    '''Class to manage a Moodle session, allowing interaction with Moodle's API.'''

    def __init__(self, cached_session: MoodleCachedSession) -> None:
        '''Initialize the Moodle session with a cached session.

        Args:
            cached_session (MoodleCachedSession): A cached session object for Moodle.
        '''

        ...

    async def is_valid(self) -> bool:
        '''Check if the current session is still valid.

        Returns:
            bool: True if the session is valid, False otherwise.
        '''

        ...

    async def get_course(self, course_id: str | int) -> MoodleCourse:
        '''Retrieve information about a specific Moodle course.

        Args:
            course_id (str | int): The course ID or a URL string containing the course ID.

        Returns:
            MoodleCourse: An object representing the Moodle course.
        '''

        # TODO: Convert course URL (if provided as a string) to an ID
        if isinstance(course_id, str):
            course_id = ...

        ...

    async def get_excel_report(self, report_id: str | int) -> pd.DataFrame:
        '''Retrieve a Excel report from Moodle.

        Args:
            report_id (str | int): The ID or URL of the report to be retrieved.

        Returns:
            pd.DataFrame: A DataFrame containing the report data formatted for Excel.
        '''

        # TODO: Convert report URL (if provided as a string) to an ID
        if isinstance(report_id, str):
            report_id = ...

        ...

    async def close(self) -> None:
        '''Close the current Moodle session.'''

        ...

    async def __aenter__(self) -> Self:
        '''Enter the asynchronous context manager.

        Returns:
            Self: The current instance of MoodleSession.
        '''

        return self

    async def __aexit__(self, *_) -> None:
        '''Exit the asynchronous context manager.

        Args:
            *_: Optional arguments (ignored).

        Closes the session upon exiting the context manager.
        '''

        return await self.close()
