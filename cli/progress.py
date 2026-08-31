from typing import TypeVar

from tqdm import tqdm

from moodle.progress import ProgressHandler

T = TypeVar("T")


class TDQMProgressHandler(ProgressHandler[int]):
    """A handler that integrates with the tqdm library to display a progress bar."""

    _bar: tqdm
    """An instance of the tqdm progress bar used to display progress."""

    def __init__(self, size: int) -> None:
        """Initialize the progress handler with the given initial state."""

        super().__init__(0)
        self._bar = tqdm(total=size)

    def update(self, progress: int) -> None:
        """Abstract method to update the progress.

        Args:
            progress (int): The progress value to update.
        """

        delta = max(0, progress - self._state)
        self._bar.update(delta)

        self._state = progress

    def close(self) -> None:
        """Abstract method to close the progress handler."""

        self._bar.close()
