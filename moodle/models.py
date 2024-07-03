from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class MoodleActivity:
    '''Class to represent a section in a Moodle section.'''

    id: int
    '''The unique identifier for the Moodle activity.'''

    name: str
    '''The name or title of the Moodle activity.'''


@dataclass(frozen=True)
class ChoiceMoodleActivity(MoodleActivity):
    '''Class to represent a choice Moodle activity.'''

    pass


@dataclass(frozen=True)
class MoodleSection:
    '''Class to represent a section in a Moodle course.'''

    id: int
    '''The unique identifier for the Moodle section.'''

    name: str
    '''The name or title of the Moodle section.'''

    activities: Sequence[MoodleActivity]
    '''A sequence of MoodleActivity objects representing the activities within the section.'''


@dataclass(frozen=True)
class MoodleCourse:
    '''Class to represent a Moodle course.'''

    id: int
    '''The unique identifier for the Moodle course.'''

    name: str
    '''The name or title of the Moodle course.'''

    sections: Sequence[MoodleSection]
    '''A sequence of MoodleSection objects representing the sections within the course.'''
