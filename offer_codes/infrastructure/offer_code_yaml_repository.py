"""YAML persistence for offer code records."""

from pathlib import Path

from offer_codes.domain.models import OfferCodeRecord


class OfferCodeYamlError(Exception):
    """Raised when the offer code YAML cannot be parsed or saved."""


class OfferCodeYamlRepository:
    FIELD_NAMES = ("U3A_number", "email", "offer_number", "issued")

    def __init__(self, path: Path) -> None:
        self._path = path

    def load_all(self) -> list[OfferCodeRecord]:
        try:
            return self._parse(self._path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise OfferCodeYamlError(f"Could not read {self._path}") from exc

    def save_all(self, records: list[OfferCodeRecord]) -> None:
        try:
            self._path.write_text(self._render(records), encoding="utf-8")
        except OSError as exc:
            raise OfferCodeYamlError(f"Could not write {self._path}") from exc

    def _parse(self, text: str) -> list[OfferCodeRecord]:
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
                raise OfferCodeYamlError(f"Unexpected YAML content on line {line_number}.")
            self._read_field(raw_line.strip(), current, line_number)
        if current is not None:
            records.append(current)
        return [self._to_record(record) for record in records]

    def _read_field(self, raw_field: str, record: dict[str, str], line_number: int) -> None:
        if ": " not in raw_field:
            raise OfferCodeYamlError(f"Invalid field on line {line_number}.")
        key, value = raw_field.split(": ", 1)
        if key not in self.FIELD_NAMES:
            raise OfferCodeYamlError(f"Unknown field {key!r} on line {line_number}.")
        record[key] = self._unquote(value)

    def _to_record(self, record: dict[str, str]) -> OfferCodeRecord:
        missing = [field_name for field_name in self.FIELD_NAMES if field_name not in record]
        if missing:
            raise OfferCodeYamlError(f"Missing fields: {', '.join(missing)}.")
        return OfferCodeRecord(
            U3A_number=record["U3A_number"],
            email=record["email"],
            offer_number=record["offer_number"],
            issued=record["issued"],
        )

    def _render(self, records: list[OfferCodeRecord]) -> str:
        lines: list[str] = []
        for record in records:
            lines.append(f'- U3A_number: "{self._quote(record.U3A_number)}"')
            lines.append(f'  email: "{self._quote(record.email)}"')
            lines.append(f'  offer_number: "{self._quote(record.offer_number)}"')
            lines.append(f'  issued: "{self._quote(record.issued)}"')
        return "\n".join(lines) + "\n"

    def _unquote(self, value: str) -> str:
        value = value.strip()
        if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
            return value[1:-1].replace('\\"', '"').replace("\\\\", "\\")
        return value

    def _quote(self, value: str) -> str:
        return value.replace("\\", "\\\\").replace('"', '\\"')
