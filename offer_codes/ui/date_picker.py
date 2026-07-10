"""Small Tkinter calendar popup."""

from __future__ import annotations

import calendar
from datetime import date
import tkinter as tk
from tkinter import ttk
from typing import Callable


class DatePickerPopup(tk.Toplevel):
    def __init__(self, parent: tk.Misc, selected_date: date, on_select: Callable[[str], None]) -> None:
        super().__init__(parent)
        self._visible_month = selected_date.replace(day=1)
        self._on_select = on_select
        self._title = tk.StringVar()
        self.title("Issued date")
        self.resizable(False, False)
        self.transient(parent.winfo_toplevel())
        self.grab_set()
        self._build()
        self._render_month()

    def _build(self) -> None:
        frame = ttk.Frame(self, padding=12)
        frame.grid(row=0, column=0)
        ttk.Button(frame, text="<", width=3, command=self._previous_month).grid(row=0, column=0, sticky="w")
        ttk.Label(frame, textvariable=self._title, width=18, anchor="center").grid(row=0, column=1, columnspan=5)
        ttk.Button(frame, text=">", width=3, command=self._next_month).grid(row=0, column=6, sticky="e")
        for column, label in enumerate(("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")):
            ttk.Label(frame, text=label, anchor="center").grid(row=1, column=column, padx=2, pady=(8, 2))
        self._days_frame = ttk.Frame(frame)
        self._days_frame.grid(row=2, column=0, columnspan=7)

    def _render_month(self) -> None:
        for child in self._days_frame.winfo_children():
            child.destroy()
        self._title.set(self._visible_month.strftime("%B %Y"))
        weeks = calendar.Calendar(firstweekday=0).monthdatescalendar(
            self._visible_month.year, self._visible_month.month
        )
        for row, week in enumerate(weeks):
            for column, day in enumerate(week):
                button = ttk.Button(
                    self._days_frame,
                    text=str(day.day),
                    width=4,
                    command=lambda value=day: self._select(value),
                )
                if day.month != self._visible_month.month:
                    button.configure(state="disabled")
                button.grid(row=row, column=column, padx=2, pady=2)

    def _previous_month(self) -> None:
        year = self._visible_month.year
        month = self._visible_month.month - 1
        if month == 0:
            year -= 1
            month = 12
        self._visible_month = date(year, month, 1)
        self._render_month()

    def _next_month(self) -> None:
        year = self._visible_month.year
        month = self._visible_month.month + 1
        if month == 13:
            year += 1
            month = 1
        self._visible_month = date(year, month, 1)
        self._render_month()

    def _select(self, selected: date) -> None:
        self._on_select(selected.isoformat())
        self.destroy()
