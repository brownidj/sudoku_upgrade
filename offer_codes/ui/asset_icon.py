"""Image asset helper for Tkinter controls."""

from pathlib import Path
import tkinter as tk

from PIL import Image, ImageTk


class AssetIconError(Exception):
    """Raised when an image asset cannot be loaded."""


class AssetIconFactory:
    def create(self, path: Path, size: int = 18) -> tk.PhotoImage:
        try:
            image = Image.open(path).convert("RGBA")
        except OSError as exc:
            raise AssetIconError(f"Could not load icon asset: {path}") from exc
        image.thumbnail((size, size), Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(image)
