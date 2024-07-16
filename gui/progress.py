from moodle.progress import ProgressHandler
from typing import Any, TypeVar
from customtkinter import CTkProgressBar
from gui.constants import SCALE_FACTOR


T = TypeVar("T")


class ProgressHandlerContext(ProgressHandler[int]):
    """A context for handling progress using a custom progress bar."""

    _bar: CTkProgressBar
    """An instance of the custom progress bar used to display progress."""

    _size: int
    """The total size or number of steps for the progress bar."""

    def __init__(self, master: Any, size: int) -> None:
        """Initialize the progress handler with the given initial state."""

        super().__init__(0)
        self._size = size

        self._bar = CTkProgressBar(master=master, height=28)
        self._bar.grid(
            row=4,
            column=0,
            columnspan=2,
            padx=(SCALE_FACTOR, SCALE_FACTOR),
            pady=(2 * SCALE_FACTOR, 0),
            sticky="ew",
        )
        self._bar.set(self._state)

    def update(self, new_value: int) -> None:
        """Abstract method to update the progress.

        Args:
            new_value (int): The progress value to update.
        """

        self._bar.set(new_value / self._size)
        self._bar.update_idletasks()

        self._state = new_value

    def close(self) -> None:
        """Abstract method to close the progress handler."""

        self._bar.grid_remove()
