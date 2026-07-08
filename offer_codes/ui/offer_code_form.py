"""Tkinter form for assigning offer codes."""

import tkinter as tk
from tkinter import ttk

from offer_codes.domain.models import OfferCodeRecord
from offer_codes.ui.offer_code_controller import OfferCodeController


class OfferCodeForm(ttk.Frame):
    def __init__(self, parent: tk.Misc, controller: OfferCodeController) -> None:
        super().__init__(parent, padding=24)
        self._controller = controller
        self._offer_number = tk.StringVar()
        self._U3A_number = tk.StringVar()
        self._email = tk.StringVar()
        self._issued = tk.StringVar()
        self._status = tk.StringVar()
        self._save_button: ttk.Button | None = None
        self._build()
        self._bind_validation()
        self.load_next()

    def _build(self) -> None:
        self.columnconfigure(1, weight=1)
        ttk.Label(self, text="Offer number").grid(row=0, column=0, sticky="w", pady=6)
        ttk.Entry(self, textvariable=self._offer_number, state="readonly", width=34).grid(
            row=0, column=1, sticky="ew", pady=6
        )
        ttk.Label(self, text="U3A number").grid(row=1, column=0, sticky="w", pady=6)
        ttk.Entry(self, textvariable=self._U3A_number, width=34).grid(row=1, column=1, sticky="ew", pady=6)
        ttk.Label(self, text="Email").grid(row=2, column=0, sticky="w", pady=6)
        ttk.Entry(self, textvariable=self._email, width=34).grid(row=2, column=1, sticky="ew", pady=6)
        ttk.Label(self, text="Issued").grid(row=3, column=0, sticky="w", pady=6)
        ttk.Entry(self, textvariable=self._issued, state="readonly", width=34).grid(
            row=3, column=1, sticky="ew", pady=6
        )
        self._save_button = ttk.Button(self, text="Save", command=self._save, state="disabled")
        self._save_button.grid(row=4, column=1, sticky="e", pady=(14, 6))
        ttk.Label(self, textvariable=self._status).grid(row=5, column=0, columnspan=2, sticky="w", pady=(8, 0))

    def _bind_validation(self) -> None:
        self._U3A_number.trace_add("write", self._refresh_save_state)
        self._email.trace_add("write", self._refresh_save_state)

    def load_next(self) -> None:
        record = self._controller.load_next()
        if record is None:
            self._set_record(OfferCodeRecord.blank(""))
            self._status.set("No unissued offer codes remain.")
            self._set_save_enabled(False)
            return
        self._set_record(record)
        self._status.set("Ready.")
        self._refresh_save_state()

    def _save(self) -> None:
        saved = self._controller.save(self._U3A_number.get(), self._email.get())
        if saved is None:
            return
        self._status.set(f"Saved {saved.offer_number}.")
        self._clear_assignment_fields()
        self.after(150, self.load_next)

    def _set_record(self, record: OfferCodeRecord) -> None:
        self._offer_number.set(record.offer_number)
        self._U3A_number.set(record.U3A_number)
        self._email.set(record.email)
        self._issued.set(record.issued)

    def _clear_assignment_fields(self) -> None:
        self._U3A_number.set("")
        self._email.set("")
        self._issued.set("")
        self._set_save_enabled(False)

    def _refresh_save_state(self, *_args: object) -> None:
        enabled = self._controller.can_save(self._U3A_number.get(), self._email.get())
        self._set_save_enabled(enabled)

    def _set_save_enabled(self, enabled: bool) -> None:
        if self._save_button is not None:
            self._save_button.configure(state="normal" if enabled else "disabled")
