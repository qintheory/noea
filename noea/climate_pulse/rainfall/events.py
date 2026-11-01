"""
Documented Hong Kong rainfall events, used only to CHECK the models, never to fit them.
Sources and caveats are in docs/hk-reference-events.md. `scale` is the window length that suits the event: dated
storms are checked with 30-day windows, wet and dry years with 365-day windows. `group` splits the list in two in
advance (alternating down the list), so a setting chosen on one half can be tested on the other.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Event:
    label: str
    kind: str          # "wet" or "dry"
    start: date
    end: date
    scale: int         # days
    group: str         # "tune" or "test"


def _year(y: int) -> tuple[date, date]:
    return date(y, 1, 1), date(y, 12, 31)


_STORMS = [
    ("1889 May rainstorm (record 24 h)", date(1889, 5, 30)),
    ("1926 Jul rainstorm (534 mm day)", date(1926, 7, 19)),
    ("1966 Jun rainstorm and floods", date(1966, 6, 12)),
    ("1972 Jun landslides (Po Shan)", date(1972, 6, 18)),
    ("1999 Aug Severe Tropical Storm Sam", date(1999, 8, 23)),
    ("2008 Jun black rainstorm", date(2008, 6, 7)),
    ("2023 Sep black rainstorm", date(2023, 9, 8)),
]
_YEARS = [
    ("1982 extremely wet year", "wet", 1982), ("1997 extremely wet year", "wet", 1997), ("2005 extremely wet year", "wet", 2005),
    ("1963 drought (driest year)", "dry", 1963), ("1895 dry year", "dry", 1895), ("1954 dry year", "dry", 1954),
]

EVENTS: list[Event] = []
for i, (label, day) in enumerate(_STORMS):                                     # a storm is checked over the 30 days around its date
    EVENTS.append(Event(label, "wet", date.fromordinal(day.toordinal() - 15), date.fromordinal(day.toordinal() + 15), 30, "tune" if i % 2 == 0 else "test"))
for i, (label, kind, y) in enumerate(_YEARS):
    EVENTS.append(Event(label, kind, *_year(y), 365, "tune" if i % 2 == 0 else "test"))
EVENTS.append(Event("1967 dry spell (supply cut Feb 1967)", "dry", date(1966, 10, 1), date(1967, 9, 30), 365, "test"))
