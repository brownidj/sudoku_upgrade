"""Tkinter application shell."""

import tkinter as tk
from tkinter import ttk

from offer_codes.ui.offer_code_controller import OfferCodeController
from offer_codes.ui.offer_code_form import OfferCodeForm


class OfferCodeTkinterApp:
    def __init__(self, controller: OfferCodeController) -> None:
        self._controller = controller

    def run(self) -> None:
        root = tk.Tk()
        root.title("Offer Codes")
        root.minsize(480, 260)
        ttk.Style(root).theme_use("clam")
        form = OfferCodeForm(root, self._controller)
        form.pack(fill="both", expand=True)
        root.mainloop()
