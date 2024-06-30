from typing import Any, Self, Sequence
from customtkinter import CTkBaseClass


class DisabledContext:
    """Context manager to temporarily disable a sequence of widgets."""

    _widgets: Sequence[CTkBaseClass]
    _prev_states: list[str]

    def __init__(self, widgets: Sequence[CTkBaseClass]) -> None:
        """Initialize the context manager with the widgets to be disabled.

        Args:
            widgets (Sequence[CTkBaseClass]): The widgets to be disabled.
        """

        self._widgets = widgets
        self._prev_states = []

    def __enter__(self) -> Self:
        """Enter the context and disable the widgets.

        Returns:
            Self: The instance of the context manager.
        """

        for widget in self._widgets:
            self._prev_states.append(str(widget.cget("state")))
            widget.configure(state="disabled")

        return self

    def __exit__(self, *_) -> Any:
        """Exit the context and restore the previous states of the widgets.

        Args:
            *_: Optional arguments (ignored).
        """

        for widget, state in zip(self._widgets, self._prev_states):
            widget.configure(state=state)
