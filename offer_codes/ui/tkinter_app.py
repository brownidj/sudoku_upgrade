"""Tkinter application shell."""

import tkinter as tk
from tkinter import ttk

from offer_codes.application.auth_service import AuthService
from offer_codes.ui.login_dialog import LoginDialog
from offer_codes.ui.offer_code_controller import OfferCodeController
from offer_codes.ui.offer_code_form import OfferCodeForm


class OfferCodeTkinterApp:
    def __init__(self, controller: OfferCodeController, auth_service: AuthService) -> None:
        self._controller = controller
        self._auth_service = auth_service

    def run(self) -> None:
        root = tk.Tk()
        root.title("Offer Codes")
        root.minsize(480, 260)
        ttk.Style(root).theme_use("clam")
        if not self._show_login(root):
            root.destroy()
            return
        form = OfferCodeForm(root, self._controller)
        form.pack(fill="both", expand=True)
        root.mainloop()

    def _show_login(self, root: tk.Tk) -> bool:
        dialog = LoginDialog(root, self._auth_service)
        root.wait_window(dialog)
        return dialog.authenticated
