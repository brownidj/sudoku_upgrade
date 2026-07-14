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
        self._device_type = tk.StringVar(value="iPhone")
        self._issued = tk.StringVar()
        self._status = tk.StringVar()
        self._dry_run = tk.BooleanVar(value=True)
        self._mode_warning = tk.StringVar()
        self._calendar_icon: tk.PhotoImage | None = None
        self._first_name_entry: HintedEntry | None = None
        self._last_name_entry: HintedEntry | None = None
        self._offer_number_widgets: tuple[ttk.Label, ttk.Entry] | None = None
        self._issue_mode_button: ttk.Radiobutton | None = None
        self._cancel_button: ttk.Button | None = None
        self._save_button: ttk.Button | None = None
        self._progress_bar: ttk.Progressbar | None = None
        self._save_queue: queue.Queue[tuple[int, SaveOutcome]] = queue.Queue()
        self._next_save_id = 0
        self._active_save_id: int | None = None
        self._cancelled_save_ids: set[int] = set()
        self._save_cancel_event: threading.Event | None = None
        self._polling_save_queue = False
        self._build()
        self._bind_validation()
        self.load_next()

    def _build(self) -> None:
        self.columnconfigure(1, weight=1)
        self._build_mode_toggle().grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 14))
        ttk.Label(self, text="Device").grid(row=1, column=0, sticky="w", pady=6)
        self._build_device_selector().grid(row=1, column=1, sticky="w", pady=6)
        offer_label = ttk.Label(self, text="Offer number")
        offer_entry = ttk.Entry(self, textvariable=self._offer_number, state="readonly", width=34)
        offer_label.grid(row=2, column=0, sticky="w", pady=6)
        offer_entry.grid(row=2, column=1, sticky="ew", pady=6)
        self._offer_number_widgets = (offer_label, offer_entry)
        ttk.Label(self, text="Name").grid(row=3, column=0, sticky="w", pady=6)
        name_frame = ttk.Frame(self)
        name_frame.grid(row=3, column=1, sticky="ew", pady=6)
        for column in (0, 1):
            name_frame.columnconfigure(column, weight=1)
        self._first_name_entry = HintedEntry(name_frame, self._first_name, "First", width=16)
        self._last_name_entry = HintedEntry(name_frame, self._last_name, "Last", width=16)
        self._first_name_entry.grid(row=0, column=0, sticky="ew")
        self._last_name_entry.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        for row, label, variable in (
            (4, "U3A number", self._U3A_number),
            (5, "Email", self._email),
        ):
            ttk.Label(self, text=label).grid(row=row, column=0, sticky="w", pady=6)
            ttk.Entry(self, textvariable=variable, width=34).grid(row=row, column=1, sticky="ew", pady=6)
        ttk.Label(self, text="Issued").grid(row=6, column=0, sticky="w", pady=6)
        issued_frame = ttk.Frame(self)
        issued_frame.grid(row=6, column=1, sticky="ew", pady=6)
        issued_frame.columnconfigure(0, weight=1)
        ttk.Entry(issued_frame, textvariable=self._issued, state="readonly", width=34).grid(row=0, column=0, sticky="ew")
        self._build_calendar_button(issued_frame).grid(row=0, column=1, padx=(6, 0))
        actions = ttk.Frame(self)
        actions.grid(row=7, column=1, sticky="ew", pady=(14, 6))
        actions.columnconfigure(1, weight=1)
        self._cancel_button = ttk.Button(actions, text="Cancel", command=self._cancel_save, state="disabled")
        self._cancel_button.grid(row=0, column=0, sticky="w", padx=(0, 12))
        self._progress_bar = ttk.Progressbar(actions, mode="indeterminate", length=160)
        self._save_button = ttk.Button(actions, text="Save", command=self._save, state="disabled")
        self._save_button.grid(row=0, column=2, sticky="e")
        ttk.Label(self, textvariable=self._status).grid(row=8, column=0, columnspan=2, sticky="w", pady=(8, 0))
        self._refresh_mode_warning()
        self._refresh_device_fields()

    def _build_mode_toggle(self) -> ttk.Frame:
        frame = ttk.Frame(self)
        frame.columnconfigure(0, weight=1)
        tk.Label(frame, textvariable=self._mode_warning, fg="red", font=("TkDefaultFont", 26, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(frame, text="Dry run", variable=self._dry_run, value=True, command=self._refresh_mode_warning).grid(row=0, column=1, sticky="e")
        self._issue_mode_button = ttk.Radiobutton(frame, text="Issue", variable=self._dry_run, value=False, command=self._refresh_mode_warning)
        self._issue_mode_button.grid(row=0, column=2, sticky="e", padx=(10, 0))
        return frame

    def _build_device_selector(self) -> ttk.Frame:
        frame = ttk.Frame(self)
        for index, device_type in enumerate(self._controller.device_types()):
            ttk.Radiobutton(frame, text=device_type, variable=self._device_type, value=device_type, command=self._refresh_device_fields).grid(row=0, column=index, sticky="w", padx=(14 if index else 0, 0))
        return frame

    def _bind_validation(self) -> None:
        for variable, callback in ((self._U3A_number, self._refresh_save_state), (self._first_name, self._refresh_save_state), (self._last_name, self._refresh_save_state), (self._email, self._refresh_save_state), (self._issued, self._refresh_save_state), (self._device_type, self._refresh_device_fields)):
            variable.trace_add("write", callback)

    def load_next(self) -> None:
        record = self._controller.load_next()
        if record is None:
            self._set_record(OfferCodeRecord.blank(""))
            self._status.set("No unissued offer codes remain.")
            self._set_action_state(False, False)
            return
        self._set_record(record)
        self._refresh_ready_status()
        self._refresh_save_state()

    def _save(self) -> None:
        self._next_save_id += 1
        self._active_save_id = self._next_save_id
        self._save_cancel_event = threading.Event()
        self._status.set(self._save_status())
        self._set_action_state(False, True)
        self._show_progress()
        worker = threading.Thread(target=self._send_current_email, args=(self._active_save_id, self._U3A_number.get(), self._first_name.get(), self._last_name.get(), self._email.get(), self._device_type.get(), self._issued.get(), self._dry_run.get(), self._save_cancel_event), daemon=True)
        worker.start()
        self._schedule_save_poll()

    def _send_current_email(self, save_id: int, U3A_number: str, first_name: str, last_name: str, email: str, device_type: str, issued: str, dry_run: bool, cancel_event: threading.Event) -> None:
        outcome = self._controller.save(U3A_number, first_name, last_name, email, device_type, issued, dry_run, cancel_event)
        self._save_queue.put((save_id, outcome))

    def _poll_save_result(self) -> None:
        try:
            save_id, outcome = self._save_queue.get_nowait()
        except queue.Empty:
            self._schedule_save_poll()
            return
        if save_id in self._cancelled_save_ids:
            self._cancelled_save_ids.discard(save_id)
        elif save_id == self._active_save_id:
            self._finish_save(save_id)
            self._apply_outcome(outcome)
        self._schedule_save_poll()

    def _apply_outcome(self, outcome: SaveOutcome) -> None:
        if not outcome.succeeded:
            self._controller.show_save_error(outcome)
            self._status.set("Email was not sent. Check the error and try again.")
            self._refresh_save_state()
            return
        if outcome.android_tester:
            self._status.set("Dry run: Android email sent. No data was written." if outcome.dry_run else "Android email sent and tester recorded.")
            self._show_android_email_sent()
        elif outcome.dry_run and isinstance(outcome.record, OfferCodeRecord):
            self._status.set(f"Dry run: email simulated for {outcome.record.offer_number}. No data was written.")
        elif isinstance(outcome.record, OfferCodeRecord):
            self._status.set(f"Offer code issued: {outcome.record.offer_number}.")
        self._clear_assignment_fields()
        if not outcome.android_tester:
            self.after(150, self.load_next)

    def _cancel_save(self) -> None:
        if self._active_save_id is None or self._save_cancel_event is None:
            return
        self._cancelled_save_ids.add(self._active_save_id)
        self._save_cancel_event.set()
        self._controller.cancel_active_save()
        self._finish_save(self._active_save_id)
        self._clear_assignment_fields(reset_issued=True)
        self._status.set("Cancelled. Ready for the next entry.")
        self.after(1800, self._restore_ready_status)

    def _restore_ready_status(self) -> None:
        if self._active_save_id is None and self._status.get() == "Cancelled. Ready for the next entry.":
            self._refresh_ready_status()

    def _finish_save(self, save_id: int) -> None:
        if save_id != self._active_save_id:
            return
        self._hide_progress()
        self._active_save_id = None
        self._save_cancel_event = None
        self._set_action_state(False, False)

    def _schedule_save_poll(self) -> None:
        if self._polling_save_queue or (self._active_save_id is None and not self._cancelled_save_ids):
            return
        self._polling_save_queue = True
        self.after(100, self._continue_polling)

    def _continue_polling(self) -> None:
        self._polling_save_queue = False
        self._poll_save_result()

    def _set_record(self, record: OfferCodeRecord) -> None:
        self._offer_number.set(record.offer_number)
        self._U3A_number.set(record.U3A_number)
        self._first_name.set(record.first_name)
        self._last_name.set(record.last_name)
        self._email.set(record.email)
        self._issued.set(record.issued or self._controller.default_issued_date())
        self._sync_name_hints()
        self._refresh_device_fields()

    def _clear_assignment_fields(self, reset_issued: bool = False) -> None:
        for variable in (self._U3A_number, self._first_name, self._last_name, self._email):
            variable.set("")
        self._issued.set(self._controller.default_issued_date() if reset_issued else "")
        self._sync_name_hints()
        self._set_action_state(False, False)

    def _refresh_save_state(self, *_args: object) -> None:
        enabled = self._controller.can_save(self._U3A_number.get(), self._first_name.get(), self._last_name.get(), self._email.get(), self._device_type.get()) and bool(self._issued.get())
        self._set_action_state(enabled and self._active_save_id is None, False)

    def _refresh_device_fields(self, *_args: object) -> None:
        if self._offer_number_widgets is not None:
            for widget in self._offer_number_widgets:
                (widget.grid if not self._is_android() else widget.grid_remove)()
        self._refresh_mode_warning()
        self._refresh_ready_status()
        self._refresh_save_state()

    def _refresh_ready_status(self) -> None:
        self._status.set("Ready." if self._is_android() else f"Ready. {self._controller.remaining_count()} offer codes remaining.")

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

    def _set_action_state(self, save_enabled: bool, cancel_enabled: bool) -> None:
        if self._save_button is not None:
            self._save_button.configure(state="normal" if save_enabled else "disabled")
        if self._cancel_button is not None:
            self._cancel_button.configure(state="normal" if cancel_enabled else "disabled")

    def _show_progress(self) -> None:
        if self._progress_bar is None:
            return
        self._progress_bar.grid(row=0, column=1, sticky="w", padx=(0, 12))
        self._progress_bar.start(12)
        self.update()

    def _hide_progress(self) -> None:
        if self._progress_bar is not None:
            self._progress_bar.stop()
            self._progress_bar.grid_remove()

    def _refresh_mode_warning(self) -> None:
        if self._issue_mode_button is not None:
            self._issue_mode_button.configure(text="Send email" if self._is_android() else "Issue")
        warning = "Dry run"
        if not self._dry_run.get():
            warning = "Send email!" if self._is_android() else "Offer codes will be issued!"
        self._mode_warning.set(warning)

    def _show_android_email_sent(self) -> None:
        self._mode_warning.set("Email sent!")
        self.after(3000, self._refresh_mode_warning)

    def _save_status(self) -> str:
        if not self._is_android():
            return "Please wait... generating and sending email."
        return "Please wait... sending Android email." if self._dry_run.get() else "Please wait... sending email and saving Android tester."
    def _is_android(self) -> bool:
        return self._device_type.get() == "Android"
    def _sync_name_hints(self) -> None:
        for entry in (self._first_name_entry, self._last_name_entry):
            if entry is not None:
                entry.sync_hint()
