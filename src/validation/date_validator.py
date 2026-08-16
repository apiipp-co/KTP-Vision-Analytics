from __future__ import annotations

from datetime import date, datetime


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            pass
    return None


def resolve_two_digit_year(year: int, month: int, day: int, reference: date | None = None) -> date | None:
    reference = reference or date.today()
    candidates = []
    for century in (1900, 2000):
        try:
            candidate = date(century + year, month, day)
            if candidate <= reference:
                candidates.append(candidate)
        except ValueError:
            continue
    return max(candidates) if candidates else None

