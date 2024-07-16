from moodle.progress import ProgressHandler
from tqdm import tqdm
from typing import TypeVar


T = TypeVar("T")


class TDQMProgressHandler(ProgressHandler[int]):
    """A handler that integrates with the tqdm library to display a progress bar."""

    _bar: tqdm
    """An instance of the tqdm progress bar used to display progress."""

    def __init__(self, size: int) -> None:
        """Initialize the progress handler with the given initial state."""

        super().__init__(0)
        self._bar = tqdm(total=size)

    def update(self, new_value: int) -> None:
        """Abstract method to update the progress.

        Args:
            new_value (int): The progress value to update.
        """

        delta = max(0, new_value - self._state)
        self._bar.update(delta)

        self._state = new_value

    def close(self) -> None:
        """Abstract method to close the progress handler."""

        self._bar.close()
