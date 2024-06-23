from dataclasses import dataclass
from moodle.constants import MOODLE_BASE_ADDRESS
from moodle.session import MoodleSession


@dataclass(frozen=True)
class MoodleCredentials:
    '''Class to store Moodle login credentials.'''

    login: str
    '''The username for logging into Moodle.'''

    password: str
    '''The password for logging into Moodle.'''


@dataclass(frozen=True)
class MoodleCachedSession:
    '''Class to store a cached Moodle session.'''

    ...


class MoodleSessionFactory:
    '''Factory class to create and manage Moodle sessions.'''

    async def auth(self, credentials: MoodleCredentials) -> MoodleSession:
        '''Authenticate the user and create a new Moodle session.

        Args:
            credentials (MoodleCredentials): The login credentials for Moodle.

        Returns:
            MoodleSession: An authenticated Moodle session.
        '''

        # TODO: Build cached session there
        ...

        cached_session = ...
        return MoodleSession(cached_session)

    async def restore(self, filename: str) -> MoodleSession:
        '''Restore a Moodle session from a cached session file.

        Args:
            filename (str): The path to the file containing the cached session.

        Returns:
            MoodleSession: A restored Moodle session.
        '''

        # TODO: Read cached session from file there
        ...

        cached_session = ...
        return MoodleSession(cached_session)
