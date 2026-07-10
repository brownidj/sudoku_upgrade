"""Load local environment variables from a .env file."""

import os
from pathlib import Path


class EnvLoaderError(Exception):
    """Raised when a .env file contains invalid syntax."""


class EnvLoader:
    def load(self, path: Path) -> None:
        if not path.exists():
            return
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            raise EnvLoaderError(f"Could not read {path}") from exc
        for line_number, raw_line in enumerate(lines, start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            key, value = self._parse_line(line, line_number)
            os.environ.setdefault(key, value)

    def _parse_line(self, line: str, line_number: int) -> tuple[str, str]:
        if "=" not in line:
            raise EnvLoaderError(f"Invalid .env entry on line {line_number}.")
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            raise EnvLoaderError(f"Missing .env key on line {line_number}.")
        return key, self._unquote(value.strip())

    def _unquote(self, value: str) -> str:
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            return value[1:-1]
        return value
