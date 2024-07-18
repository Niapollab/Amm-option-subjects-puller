from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class Student:
    """Class to represent a student."""

    fullname: str
    """The full name of the student."""

    priority: Sequence[str]
    """List of priority subjects for the student."""


@dataclass(frozen=True)
class Report:
    """Class to represent a report."""

    students: Sequence[Student]
    """A sequence of student objects included in the report."""
