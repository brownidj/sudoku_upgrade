"""Tkinter form for assigning offer codes."""

import queue
import threading
import tkinter as tk
from datetime import date
from pathlib import Path
from tkinter import ttk

from offer_codes.domain.models import OfferCodeRecord
from offer_codes.ui.asset_icon import AssetIconError, AssetIconFactory
from offer_codes.ui.date_picker import DatePickerPopup
from offer_codes.ui.hinted_entry import HintedEntry
from offer_codes.ui.offer_code_controller import OfferCodeController, SaveOutcome


class OfferCodeForm(ttk.Frame):
    def __init__(self, parent: tk.Misc, controller: OfferCodeController) -> None:
        super().__init__(parent, padding=24)
        self._controller = controller
        self._offer_number = tk.StringVar()
        self._U3A_number = tk.StringVar()
        self._first_name = tk.StringVar()
        self._last_name = tk.StringVar()
        self._email = tk.StringVar()
        self._device_type = tk.StringVar()
        self._issued = tk.StringVar()
        self._status = tk.StringVar()
        self._dry_run = tk.BooleanVar(value=True)
        self._mode_warning = tk.StringVar()
        self._calendar_icon: tk.PhotoImage | None = None
        self._first_name_entry: HintedEntry | None = None
        self._last_name_entry: HintedEntry | None = None
        self._save_button: ttk.Button | None = None
        self._progress_bar: ttk.Progressbar | None = None
        self._save_queue: queue.Queue[SaveOutcome] = queue.Queue()
        self._build()
        self._bind_validation()
        self.load_next()

    def _build(self) -> None:
        self.columnconfigure(1, weight=1)
        self._build_mode_toggle().grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 14))
        ttk.Label(self, text="Offer number").grid(row=1, column=0, sticky="w", pady=6)
        ttk.Entry(self, textvariable=self._offer_number, state="readonly", width=34).grid(
            row=1, column=1, sticky="ew", pady=6
        )
        ttk.Label(self, text="Name").grid(row=2, column=0, sticky="w", pady=6)
        name_frame = ttk.Frame(self)
        name_frame.grid(row=2, column=1, sticky="ew", pady=6)
        name_frame.columnconfigure(0, weight=1)
        name_frame.columnconfigure(1, weight=1)
        self._first_name_entry = HintedEntry(name_frame, self._first_name, "First", width=16)
        self._first_name_entry.grid(row=0, column=0, sticky="ew")
        self._last_name_entry = HintedEntry(name_frame, self._last_name, "Last", width=16)
        self._last_name_entry.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        ttk.Label(self, text="U3A number").grid(row=3, column=0, sticky="w", pady=6)
        ttk.Entry(self, textvariable=self._U3A_number, width=34).grid(row=3, column=1, sticky="ew", pady=6)
        ttk.Label(self, text="Email").grid(row=4, column=0, sticky="w", pady=6)
        ttk.Entry(self, textvariable=self._email, width=34).grid(row=4, column=1, sticky="ew", pady=6)
        ttk.Label(self, text="Device").grid(row=5, column=0, sticky="w", pady=6)
        ttk.Combobox(
            self,
            textvariable=self._device_type,
            values=self._controller.device_types(),
            state="readonly",
            width=32,
        ).grid(row=5, column=1, sticky="ew", pady=6)
        ttk.Label(self, text="Issued").grid(row=6, column=0, sticky="w", pady=6)
        issued_frame = ttk.Frame(self)
        issued_frame.grid(row=6, column=1, sticky="ew", pady=6)
        issued_frame.columnconfigure(0, weight=1)
        ttk.Entry(issued_frame, textvariable=self._issued, state="readonly", width=34).grid(
            row=0, column=0, sticky="ew"
        )
        self._build_calendar_button(issued_frame).grid(row=0, column=1, padx=(6, 0))
        actions_frame = ttk.Frame(self)
        actions_frame.grid(row=7, column=1, sticky="ew", pady=(14, 6))
        actions_frame.columnconfigure(0, weight=1)
        self._progress_bar = ttk.Progressbar(actions_frame, mode="indeterminate", length=160)
        self._save_button = ttk.Button(actions_frame, text="Save", command=self._save, state="disabled")
        self._save_button.grid(row=0, column=1, sticky="e")
        ttk.Label(self, textvariable=self._status).grid(row=8, column=0, columnspan=2, sticky="w", pady=(8, 0))
        self._refresh_mode_warning()

    def _build_mode_toggle(self) -> ttk.Frame:
        frame = ttk.Frame(self)
        frame.columnconfigure(0, weight=1)
        label = tk.Label(frame, textvariable=self._mode_warning, fg="red", font=("TkDefaultFont", 26, "bold"))
        label.grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(frame, text="Dry run", variable=self._dry_run, value=True, command=self._refresh_mode_warning).grid(
            row=0, column=1, sticky="e"
        )
        ttk.Radiobutton(
            frame, text="Issue", variable=self._dry_run, value=False, command=self._refresh_mode_warning
        ).grid(row=0, column=2, sticky="e", padx=(10, 0))
        return frame

    def _bind_validation(self) -> None:
        self._U3A_number.trace_add("write", self._refresh_save_state)
        self._first_name.trace_add("write", self._refresh_save_state)
        self._last_name.trace_add("write", self._refresh_save_state)
        self._email.trace_add("write", self._refresh_save_state)
        self._device_type.trace_add("write", self._refresh_save_state)
        self._issued.trace_add("write", self._refresh_save_state)

    def load_next(self) -> None:
        record = self._controller.load_next()
        if record is None:
            self._set_record(OfferCodeRecord.blank(""))
            self._status.set("No unissued offer codes remain.")
            self._set_save_enabled(False)
            return
        self._set_record(record)
        self._status.set(f"Ready. {self._controller.remaining_count()} offer codes remaining.")
        self._refresh_save_state()

    def _save(self) -> None:
        self._status.set("Please wait... generating and sending email.")
        self._set_save_enabled(False)
        self._show_progress()
        self._start_email_thread()
        self.after(100, self._poll_save_result)

    def _poll_save_result(self) -> None:
        try:
            outcome = self._save_queue.get_nowait()
        except queue.Empty:
            self.after(100, self._poll_save_result)
            return
        self._hide_progress()
        if not outcome.succeeded:
            self._controller.show_save_error(outcome)
            self._status.set("Email was not sent. Check the error and try again.")
            self._refresh_save_state()
            return
        if outcome.dry_run:
            self._status.set(f"Email sent for {outcome.record.offer_number}. Dry run: no data was written.")
        else:
            self._status.set(f"Offer code issued: {outcome.record.offer_number}.")
        self._clear_assignment_fields()
        self.after(150, self.load_next)

    def _set_record(self, record: OfferCodeRecord) -> None:
        self._offer_number.set(record.offer_number)
        self._U3A_number.set(record.U3A_number)
        self._first_name.set(record.first_name)
        self._last_name.set(record.last_name)
        self._email.set(record.email)
        self._device_type.set(record.device_type)
        self._issued.set(record.issued or self._controller.default_issued_date())
        self._sync_name_hints()

    def _clear_assignment_fields(self) -> None:
        self._U3A_number.set("")
        self._first_name.set("")
        self._last_name.set("")
        self._email.set("")
        self._device_type.set("")
        self._issued.set("")
        self._sync_name_hints()
        self._set_save_enabled(False)

    def _refresh_save_state(self, *_args: object) -> None:
        enabled = self._controller.can_save(
            self._U3A_number.get(),
            self._first_name.get(),
            self._last_name.get(),
            self._email.get(),
            self._device_type.get(),
        ) and bool(self._issued.get())
        self._set_save_enabled(enabled)

    def _show_calendar(self) -> None:
        DatePickerPopup(self, self._current_issued_date(), self._issued.set)

    def _build_calendar_button(self, parent: tk.Misc) -> ttk.Button:
        try:
            self._calendar_icon = AssetIconFactory().create(self._calendar_icon_path(), size=27)
            return ttk.Button(parent, image=self._calendar_icon, width=4, command=self._show_calendar)
        except AssetIconError:
            return ttk.Button(parent, text="📅", width=3, command=self._show_calendar)

    def _calendar_icon_path(self) -> Path:
        return Path(__file__).resolve().parents[2] / "assets" / "icons" / "calendar-icon-symbol-sign-vector.jpg"

    def _current_issued_date(self) -> date:
        try:
            return date.fromisoformat(self._issued.get())
        except ValueError:
            return date.fromisoformat(self._controller.default_issued_date())

    def _start_email_thread(self) -> None:
        U3A_number = self._U3A_number.get()
        first_name = self._first_name.get()
        last_name = self._last_name.get()
        email = self._email.get()
        device_type = self._device_type.get()
        issued = self._issued.get()
        dry_run = self._dry_run.get()
        worker = threading.Thread(
            target=self._send_current_email,
            args=(U3A_number, first_name, last_name, email, device_type, issued, dry_run),
            daemon=True,
        )
        worker.start()

    def _send_current_email(
        self,
        U3A_number: str,
        first_name: str,
        last_name: str,
        email: str,
        device_type: str,
        issued: str,
        dry_run: bool,
    ) -> None:
        self._save_queue.put(
            self._controller.save(U3A_number, first_name, last_name, email, device_type, issued, dry_run)
        )

    def _set_save_enabled(self, enabled: bool) -> None:
        if self._save_button is not None:
            self._save_button.configure(state="normal" if enabled else "disabled")

    def _show_progress(self) -> None:
        if self._progress_bar is None:
            return
        self._progress_bar.grid(row=0, column=0, sticky="w", padx=(0, 12))
        self._progress_bar.start(12)
        self.update()

    def _hide_progress(self) -> None:
        if self._progress_bar is None:
            return
        self._progress_bar.stop()
        self._progress_bar.grid_remove()

    def _refresh_mode_warning(self) -> None:
        if self._dry_run.get():
            self._mode_warning.set("Dry run")
        else:
            self._mode_warning.set("Offer codes will be issued!")

    def _sync_name_hints(self) -> None:
        if self._first_name_entry is not None:
            self._first_name_entry.sync_hint()
        if self._last_name_entry is not None:
            self._last_name_entry.sync_hint()
