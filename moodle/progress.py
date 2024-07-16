from abc import ABC, abstractmethod
from typing import Callable, Generic, Self, TypeVar
from customtkinter import CTk 

T = TypeVar("T")

class Bar(Generic[T]):
    _state: T

    def __init__(self, state: T):
        self._state = state

    @abstractmethod
    def update(progress: T) -> None:

        pass

    @abstractmethod
    def close(self) -> None:

        pass

    @abstractmethod
    def start(self) -> None:

        pass

class ProgressHandler(Generic[T], ABC):
    """Abstract base class for handling progress updates."""

    _state: T
    _bar: Bar
    """The state of the progress bar"""

    def __init__(self, bar: Bar, init_state: T):
        """Initialize the progress handler with the given initial state."""
        self._state = bar
        self._state = init_state

    @abstractmethod
    def update(self, progress: T) -> None:
        """Abstract method to update the progress.

        Args:
            progress (T): The progress value to update.
        """

        pass


    @abstractmethod
    def close(self) -> None:
        """Abstract method to close the progress handler."""

        pass

    @abstractmethod
    def prepare_bar(self, root: CTk | None) -> None:
        """Prepare a Bar object."""


    @staticmethod
    def mock[G](init_state: G) -> "ProgressHandler[G]":
        """Create a mock progress handler.

        Args:
            init_state (G): The initial state for the mock progress handler.

        Returns:
            ProgressHandler[G]: An instance of a mock progress handler.
        """

        return _MockProgressHandler[G](init_state)

    def __enter__(self) -> Self:
        """Enter the runtime context related to this object.

        Returns:
            Self: The progress handler instance.
        """

        return self

    def __exit__(self, *_) -> None:
        """Exit the runtime context related to this object.

        Args:
            *_: The exception details (if any).
        """

        self.close()


class _MockProgressHandler(ProgressHandler[T]):
    """Mock base class for handling progress updates."""

    def __init__(self, init_state: T, bar: Bar) -> None:
        """Initialize the progress handler with the given initial state."""

        super().__init__(bar, init_state)

    def update(self, _: T) -> None:
        """Abstract method to update the progress."""

        return

    def close(self) -> None:
        """Abstract method to close the progress handler."""

        return


ProgressHandlerFactory = Callable[[T], ProgressHandler[T]]
"""A factory type for creating ProgressHandler instances."""
