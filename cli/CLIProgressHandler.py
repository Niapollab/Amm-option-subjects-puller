from moodle.progress import ProgressHandler, Bar
from tqdm import tqdm
from typing import TypeVar

T = TypeVar("T")

class TQDMProgressBar(Bar[tqdm]):
    
    def __init__(self, count) -> None:
        self._state = tqdm(total=count, desc="Создание отчетов")

    
    def update(self) -> None:
        self._state.update()

    def close(self) -> None:
        self._state.close()

class CLIProgressHandler(ProgressHandler[T]):
    """Progress bar handler for the command-line interface."""

    def __init__(self, bar: Bar, total: int):
        self._state = total
        self._bar = bar
    
    def prepare_bar(self, _) -> None:
        self._bar = TQDMProgressBar(count=self._state)

    def update(self, _) -> None:
        self._bar.update()
        
    def close(self) -> None:
        self._bar.close()