"""
Documented Rhine and alpine floods and droughts, used only to CHECK the models, never to fit them.
Sources and caveats are in docs/river-reference-events.md. `scale` is the window length that suits the event: a dated flood
is checked with 30-day windows around its date, a summer and autumn drought with 90-day windows over those months, a
dry year with 365-day windows. `group` splits the list in two in advance (alternating down the floods and down the
droughts), so a setting chosen on one half can be tested on the other.
"""
from __future__ import annotations
from datetime import date, timedelta

from ..windows import Event

KOELN, LOBITH, LUSTENAU, THUN = "Koeln", "Lobith", "Lustenau", "Aare-Thun"
BRIENZWILER, LUETSCHINE, REUSS = "Aare-Brienzwiler", "Weisse Lütschine-Zweilütschinen", "Reuss-Andermatt"

_FLOODS = [                                                    # (station, label, date of the event)
    (KOELN, "Christmas flood 1993", date(1993, 12, 24)),
    (KOELN, "Flood of January 1995", date(1995, 1, 30)),
    (LOBITH, "Christmas flood 1993", date(1993, 12, 25)),
    (LOBITH, "Flood of January 1995", date(1995, 1, 30)),
    (LUSTENAU, "Alpine flood of August 2005", date(2005, 8, 22)),
    (BRIENZWILER, "Alpine flood of August 2005", date(2005, 8, 22)),
    (THUN, "Alpine flood of August 2005", date(2005, 8, 22)),
    (LUETSCHINE, "Alpine flood of August 2005", date(2005, 8, 22)),
    (REUSS, "Reuss flood of August 1987", date(1987, 8, 25)),
]
_DROUGHTS = [                                                  # (station, label, start, end, window)
    (KOELN, "Drought of 2003", date(2003, 7, 1), date(2003, 10, 31), 90),
    (KOELN, "Drought of 2018", date(2018, 7, 1), date(2018, 11, 30), 90),
    (LOBITH, "Drought of 2003", date(2003, 7, 1), date(2003, 10, 31), 90),
    (LOBITH, "Drought of 2018", date(2018, 7, 1), date(2018, 11, 30), 90),
    (KOELN, "Dry year 1947", date(1947, 1, 1), date(1947, 12, 31), 365),
    (LOBITH, "Dry year 1947", date(1947, 1, 1), date(1947, 12, 31), 365),
]

EVENTS: list[Event] = []
for i, (st, label, day) in enumerate(_FLOODS):                 # a flood is checked over the 30 days around its date
    EVENTS.append(Event(label, "flood", day - timedelta(15), day + timedelta(15), 30, "tune" if i % 2 == 0 else "test", st))
EVENTS.append(Event("Pentecost flood, May 1999", "flood", date(1999, 5, 1), date(1999, 5, 31), 30, "test", THUN))      # month only: no dated source found
for i, (st, label, a, b, w) in enumerate(_DROUGHTS):
    EVENTS.append(Event(label, "drought", a, b, w, "tune" if i % 2 == 0 else "test", st))
