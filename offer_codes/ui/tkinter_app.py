"""Tkinter application shell."""

import tkinter as tk
from tkinter import ttk
from typing import Callable

from offer_codes.application.auth_service import AuthService
from offer_codes.ui.login_dialog import LoginDialog
from offer_codes.ui.offer_code_controller import OfferCodeController
from offer_codes.ui.offer_code_form import OfferCodeForm


class OfferCodeTkinterApp:
    def __init__(self, controller_factory: Callable[[str], OfferCodeController], auth_service: AuthService) -> None:
        self._controller_factory = controller_factory
        self._auth_service = auth_service

    def run(self) -> None:
        root = tk.Tk()
        root.title(self._window_title())
        root.minsize(530, 260)
        ttk.Style(root).theme_use("clam")
        authenticated_user = self._show_login(root)
        if authenticated_user is None:
            root.destroy()
            return
        root.title(self._window_title(authenticated_user))
        controller = self._controller_factory(authenticated_user)
        form = OfferCodeForm(root, controller)
        form.pack(fill="both", expand=True)
        root.mainloop()

    def _show_login(self, root: tk.Tk) -> str | None:
        dialog = LoginDialog(root, self._auth_service)
        root.wait_window(dialog)
        if dialog.authenticated:
            return dialog.authenticated_user
        return None

    def _window_title(self, user: str = "") -> str:
        title = "SudoKu Playtime Offer Codes"
        if user:
            return f"{title} ({user})"
        return title
