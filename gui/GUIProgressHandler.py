from moodle.progress import ProgressHandler, Bar
from typing import TypeVar
from customtkinter import CTkProgressBar, CTk
from gui.constants import SCALE_FACTOR

T = TypeVar("T")
V = TypeVar("V")

class TkinterProgressBar(Bar[CTkProgressBar]):
    
    def __init__(self,root) -> None:
        self._state=CTkProgressBar(master=root, width=140, height=28)
        self._state.grid(row=4,
            column=0,
            columnspan=2,
            padx=(SCALE_FACTOR, SCALE_FACTOR),
            pady=(2 * SCALE_FACTOR, 0),
            sticky="ew")
        self._state.set(0)

    def update(self, progress: int) -> None:
        self._state.set(progress)

    def close(self) -> None:
        self._state.grid_remove()

class GUIProgressHandler(ProgressHandler[T]):
    _root= CTk
    _bar = Bar
    def __init__(self, bar: Bar, total: int):
        self._state = total
        self._bar = bar

    def prepare_bar(self, root) -> None:
        self._root = root

        self._bar = TkinterProgressBar(root)

    def update(self, progress: int) -> None:
        self._bar.update(progress/self._state)
        self._root.update_idletasks()
        
    def close(self) -> None:
        self._bar.close()