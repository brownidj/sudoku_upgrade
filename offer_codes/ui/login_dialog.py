"""Simple modal login dialog."""

import tkinter as tk
from tkinter import ttk

from offer_codes.application.auth_service import AuthService


class LoginDialog(tk.Toplevel):
    def __init__(self, parent: tk.Tk, auth_service: AuthService) -> None:
        super().__init__(parent)
        self._auth_service = auth_service
        self._user = tk.StringVar()
        self._password = tk.StringVar()
        self._status = tk.StringVar()
        self.authenticated = False
        self.authenticated_user = ""
        self.title("Login")
        self.resizable(False, False)
        self.transient(parent)
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self._build()
        self.grab_set()

    def _build(self) -> None:
        frame = ttk.Frame(self, padding=20)
        frame.grid(row=0, column=0)
        ttk.Label(frame, text="User").grid(row=0, column=0, sticky="w", pady=6)
        user_entry = ttk.Entry(frame, textvariable=self._user, width=28)
        user_entry.grid(row=0, column=1, sticky="ew", pady=6)
        ttk.Label(frame, text="Password").grid(row=1, column=0, sticky="w", pady=6)
        ttk.Entry(frame, textvariable=self._password, show="*", width=28).grid(row=1, column=1, sticky="ew", pady=6)
        ttk.Button(frame, text="Login", command=self._login).grid(row=2, column=1, sticky="e", pady=(12, 4))
        ttk.Label(frame, textvariable=self._status).grid(row=3, column=0, columnspan=2, sticky="w", pady=(8, 0))
        self.bind("<Return>", lambda _event: self._login())
        self.bind("<Escape>", lambda _event: self._cancel())
        user_entry.focus_set()

    def _login(self) -> None:
        authenticated_user = self._auth_service.authenticated_user(self._user.get(), self._password.get())
        if authenticated_user is not None:
            self.authenticated = True
            self.authenticated_user = authenticated_user
            self.destroy()
            return
        self._status.set("Invalid user or password.")
        self._password.set("")

    def _cancel(self) -> None:
        self.authenticated = False
        self.authenticated_user = ""
        self.destroy()
