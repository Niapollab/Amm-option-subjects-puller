from dataclasses import dataclass
from datetime import date
from typing import Mapping
import re


_IDENTIFICATOR_PATTERN = re.compile(r'_*([^_]+)')
'''Regex pattern to extract parts of the string separated by underscores.'''

_CURRENT_YEAR_BASE = date.today().year // 100 * 100
'''Calculate the current century base (e.g., 2000 for the year 2023).'''

@dataclass(frozen=True)
class Direction:
    '''Class to represent a direction (field of study) in an academic context.'''

    name: str
    '''The name of the direction (field of study).'''

    code: str
    '''The code associated with the direction (field of study).'''

    @staticmethod
    def from_str(value: str) -> 'Direction':
        '''Create a Direction instance from a string.

        Args:
            value (str): A string containing the code and name of the direction, separated by underscores.

        Returns:
            Direction: A Direction instance with the extracted code and name.
        '''

        code, name = _IDENTIFICATOR_PATTERN.findall(value.strip())
        return Direction(code, name)


@dataclass(frozen=True)
class Identificator:
    '''Class to represent a student's identificator, including faculty, direction, group, start year, form, and current year.'''

    faculty: str
    '''The faculty to which the student belongs.'''

    direction: Direction
    '''The direction (field of study) associated with the student.'''

    group: int
    '''The group number of the student.'''

    start_year: int
    '''The year the student started their studies.'''

    form: str
    '''The form of study (e.g., full-time, part-time).'''

    current_year: int
    '''The current year of study.'''

    @staticmethod
    def from_str(value: str) -> 'Identificator':
        '''Create an Identificator instance from a string.

        Args:
            value (str): A string containing the identificator details, separated by underscores.

        Returns:
            Identificator: An Identificator instance with the extracted details.
        '''

        faculty, direction_code, direction_name, group, start_year, form, current_year = _IDENTIFICATOR_PATTERN.findall(value.strip())
        direction = Direction.from_str(f'{direction_code}_{direction_name}')

        group = int(group)
        start_year = _CURRENT_YEAR_BASE + int(start_year)
        current_year = int(current_year)

        return Identificator(faculty, direction, group, start_year, form, current_year)


@dataclass(frozen=True)
class Student:
    '''Class to represent a student.'''

    fullname: str
    '''The full name of the student.'''

    subject: str
    '''The subject the student is studying.'''


@dataclass(frozen=True)
class Report:
    '''Class to represent a report, which maps group numbers to students.'''

    groups: Mapping[int, Student]
    '''A mapping of group numbers to Student instances.'''
