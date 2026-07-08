"""Date provider used by application services."""

from datetime import date


class DateProvider:
    def today_iso(self) -> str:
        return date.today().isoformat()
