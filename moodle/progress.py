from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Generic, Self, TypeVar

T = TypeVar("T")


class ProgressHandler(ABC, Generic[T]):
    """Abstract base class for handling progress updates."""

    _state: T
    """The state of the progress handler, type T."""

    def __init__(self, init_state: T) -> None:
        """Initialize the progress handler with the given initial state."""

        self._state = init_state

    @abstractmethod
    def update(self, progress: T) -> None:
        """Abstract method to update the progress.

        Args:
            progress (T): The progress value to update.
        """

    @abstractmethod
    def close(self) -> None:
        """Abstract method to close the progress handler."""

    @staticmethod
    def mock(init_state: T) -> "ProgressHandler[T]":
        """Create a mock progress handler.

        Args:
            init_state (T): The initial state for the mock progress handler.

        Returns:
            ProgressHandler[T]: An instance of a mock progress handler.
        """

        return _MockProgressHandler[T](init_state)

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

    def __init__(self, init_state: T) -> None:
        """Initialize the progress handler with the given initial state."""

        super().__init__(init_state)

    def update(self, _: T) -> None:
        """Abstract method to update the progress."""

        return

    def close(self) -> None:
        """Abstract method to close the progress handler."""

        return


ProgressHandlerFactory = Callable[[T], ProgressHandler[T]]
"""A factory type for creating ProgressHandler instances."""
