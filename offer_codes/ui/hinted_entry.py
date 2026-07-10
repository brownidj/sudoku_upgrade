"""Entry widget with lightweight placeholder text."""

import tkinter as tk


class HintedEntry(tk.Entry):
    HINT_COLOR = "#777777"
    TEXT_COLOR = "#000000"

    def __init__(self, parent: tk.Misc, textvariable: tk.StringVar, hint: str, width: int) -> None:
        super().__init__(parent, width=width)
        self._textvariable = textvariable
        self._hint = hint
        self._showing_hint = False
        self.bind("<FocusIn>", self._clear_hint)
        self.bind("<FocusOut>", self._show_hint_if_empty)
        self.bind("<KeyRelease>", self._sync_variable)
        self._show_hint_if_empty()

    def _show_hint_if_empty(self, _event: object | None = None) -> None:
        if self._textvariable.get():
            return
        self._showing_hint = True
        self.configure(fg=self.HINT_COLOR)
        self.insert(0, self._hint)

    def _clear_hint(self, _event: object | None = None) -> None:
        if not self._showing_hint:
            return
        self._showing_hint = False
        self.delete(0, tk.END)
        self.configure(fg=self.TEXT_COLOR)

    def _sync_variable(self, _event: object | None = None) -> None:
        if not self._showing_hint:
            self._textvariable.set(self.get())

    def sync_hint(self) -> None:
        self.delete(0, tk.END)
        value = self._textvariable.get()
        if value:
            self._showing_hint = False
            self.configure(fg=self.TEXT_COLOR)
            self.insert(0, value)
            return
        if self.focus_get() == self:
            self._showing_hint = False
            self.configure(fg=self.TEXT_COLOR)
            return
        self._show_hint_if_empty()
