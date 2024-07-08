from dataclasses import dataclass
from enum import Flag, auto
from typing import Sequence


@dataclass(frozen=True)
class MoodleActivity:
    """Class to represent a section in a Moodle section."""

    id: int
    """The unique identifier for the Moodle activity."""

    name: str
    """The name or title of the Moodle activity."""


@dataclass(frozen=True)
class ChoiceMoodleActivity(MoodleActivity):
    """Class to represent a choice Moodle activity."""

    pass


@dataclass(frozen=True)
class QuizMoodleActivity(MoodleActivity):
    """Class to represent a quiz Moodle activity."""

    pass


@dataclass(frozen=True)
class MoodleSection:
    """Class to represent a section in a Moodle course."""

    id: int
    """The unique identifier for the Moodle section."""

    name: str
    """The name or title of the Moodle section."""

    activities: Sequence[MoodleActivity]
    """A sequence of MoodleActivity objects representing the activities within the section."""


@dataclass(frozen=True)
class MoodleCourse:
    """Class to represent a Moodle course."""

    id: int
    """The unique identifier for the Moodle course."""

    name: str
    """The name or title of the Moodle course."""

    sections: Sequence[MoodleSection]
    """A sequence of MoodleSection objects representing the sections within the course."""


class MoodleAttemptStatus(Flag):
    """Enumeration for Moodle attempt statuses."""

    IN_PROGRESS = auto()
    """Status indicating the attempt is currently in progress."""

    OVERDUE = auto()
    """Status indicating the attempt is overdue."""

    FINISHED = auto()
    """Status indicating the attempt is finished."""

    BANDONED = auto()
    """Status indicating the attempt has been abandoned."""

    ONLY_BEST_GRADED = auto()
    """Status indicating only the best graded attempt."""

    ONLY_REGRADED = auto()
    """Status indicating only the regraded attempt."""


@dataclass(frozen=True)
class MoodleQuizAttempt:
    """Data class representing a Moodle quiz attempt."""

    id: int
    """The unique identifier of the quiz attempt."""

    fullname: str
    """The full name of the user who attempted the quiz."""

    login: str
    """The login name of the user who attempted the quiz."""

    email: str
    """The email address of the user who attempted the quiz."""

    finished: bool
    """Boolean indicating whether the quiz attempt is finished."""
