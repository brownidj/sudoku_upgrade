"""YAML persistence for login users."""

from pathlib import Path

from offer_codes.domain.user import UserCredential


class UserYamlError(Exception):
    """Raised when the user YAML cannot be parsed."""


class UserYamlRepository:
    FIELD_NAMES = ("user", "password")

    def __init__(self, path: Path) -> None:
        self._path = path

    def load_all(self) -> list[UserCredential]:
        try:
            return self._parse(self._path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise UserYamlError(f"Could not read {self._path}") from exc

    def _parse(self, text: str) -> list[UserCredential]:
        records: list[dict[str, str]] = []
        current: dict[str, str] | None = None
        for line_number, raw_line in enumerate(text.splitlines(), start=1):
            if not raw_line.strip():
                continue
            if raw_line.startswith("- "):
                if current is not None:
                    records.append(current)
                current = {}
                self._read_field(raw_line[2:], current, line_number)
                continue
            if current is None:
                raise UserYamlError(f"Unexpected YAML content on line {line_number}.")
            self._read_field(raw_line.strip(), current, line_number)
        if current is not None:
            records.append(current)
        return [self._to_credential(record) for record in records]

    def _read_field(self, raw_field: str, record: dict[str, str], line_number: int) -> None:
        if ": " not in raw_field:
            raise UserYamlError(f"Invalid field on line {line_number}.")
        key, value = raw_field.split(": ", 1)
        if key not in self.FIELD_NAMES:
            raise UserYamlError(f"Unknown field {key!r} on line {line_number}.")
        record[key] = self._unquote(value)

    def _to_credential(self, record: dict[str, str]) -> UserCredential:
        missing = [field_name for field_name in self.FIELD_NAMES if field_name not in record]
        if missing:
            raise UserYamlError(f"Missing fields: {', '.join(missing)}.")
        return UserCredential(user=record["user"], password=record["password"])

    def _unquote(self, value: str) -> str:
        value = value.strip()
        if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
            return value[1:-1].replace('\\"', '"').replace("\\\\", "\\")
        return value
