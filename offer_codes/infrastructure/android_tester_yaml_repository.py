"""YAML persistence for Android tester records."""

from pathlib import Path

from offer_codes.domain.models import AndroidTesterRecord
from offer_codes.domain.rules import OfferCodeRules


class AndroidTesterYamlError(Exception):
    """Raised when the Android tester YAML cannot be parsed or saved."""


class AndroidTesterYamlRepository:
    FIELD_NAMES = ("U3A_number", "email", "first_name", "last_name", "device_type", "registered")

    def __init__(self, path: Path) -> None:
        self._path = path

    def load_all(self) -> list[AndroidTesterRecord]:
        try:
            return self._parse(self._path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise AndroidTesterYamlError(f"Could not read {self._path}") from exc

    def save_all(self, records: list[AndroidTesterRecord]) -> None:
        try:
            self._path.write_text(self._render(records), encoding="utf-8")
        except OSError as exc:
            raise AndroidTesterYamlError(f"Could not write {self._path}") from exc

    def _parse(self, text: str) -> list[AndroidTesterRecord]:
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
                raise AndroidTesterYamlError(f"Unexpected YAML content on line {line_number}.")
            self._read_field(raw_line.strip(), current, line_number)
        if current is not None:
            records.append(current)
        return [self._to_record(record) for record in records]

    def _read_field(self, raw_field: str, record: dict[str, str], line_number: int) -> None:
        if ": " not in raw_field:
            raise AndroidTesterYamlError(f"Invalid field on line {line_number}.")
        key, value = raw_field.split(": ", 1)
        if key not in self.FIELD_NAMES:
            raise AndroidTesterYamlError(f"Unknown field {key!r} on line {line_number}.")
        record[key] = self._unquote(value)

    def _to_record(self, record: dict[str, str]) -> AndroidTesterRecord:
        missing = [field_name for field_name in self.FIELD_NAMES if field_name not in record]
        if missing:
            raise AndroidTesterYamlError(f"Missing fields: {', '.join(missing)}.")
        device_type = record["device_type"]
        if device_type and OfferCodeRules.normalize_device_type(device_type) != "Android":
            raise AndroidTesterYamlError("Device type must be blank or Android.")
        return AndroidTesterRecord(
            U3A_number=record["U3A_number"],
            email=record["email"],
            first_name=record["first_name"],
            last_name=record["last_name"],
            device_type=device_type,
            registered=record["registered"],
        )

    def _render(self, records: list[AndroidTesterRecord]) -> str:
        lines: list[str] = []
        for record in records:
            lines.append(f'- U3A_number: "{self._quote(record.U3A_number)}"')
            lines.append(f'  email: "{self._quote(record.email)}"')
            lines.append(f'  first_name: "{self._quote(record.first_name)}"')
            lines.append(f'  last_name: "{self._quote(record.last_name)}"')
            lines.append(f'  device_type: "{self._quote(record.device_type)}"')
            lines.append(f'  registered: "{self._quote(record.registered)}"')
        return "\n".join(lines) + "\n"

    def _unquote(self, value: str) -> str:
        value = value.strip()
        if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
            return value[1:-1].replace('\\"', '"').replace("\\\\", "\\")
        return value

    def _quote(self, value: str) -> str:
        return value.replace("\\", "\\\\").replace('"', '\\"')
