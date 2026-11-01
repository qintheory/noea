# Hong Kong reference events

Documented rainfall events used to CHECK the models, never to fit them. Fourteen events, in `noea/climate_pulse/rainfall/events.py`. Each is labelled "tune" or "test" (alternating down the storms, and down the years, with 1967 in "test"), fixed in advance. The rolling model's score rule was chosen on the "tune" half only and reported on the "test" half; with 3 to 4 events in each half this is a rough check, not a validation.

Daily maximum in our own record (`rainfall.csv`, gaps filled as 0 mm) next to each dated storm, as a check that the record and the sources describe the same event.

## Storms and floods (30-day windows)

| Event | In our record | Source |
|---|---|---|
| May 1889 rainstorm, the record 24-hour rainfall | 520.6 mm on 30 May, 320.6 mm on 29 May | Wikipedia, 2023 Hong Kong rainstorm and flood (cites Observatory data; the 1889 figure is not given there) |
| 19 July 1926, the largest daily rainfall on record | 534.1 mm on 19 July | HKO figure as quoted in the Bristol Historical and Photographic Collection captions; no HKO page found directly |
| 11–13 June 1966 rainstorm, 64 dead, about 500 landslides | 382.6 mm on 12 June | Gwulo (383 mm on 12 June); SCMP archive. Totals in sources differ (495 mm and 679.9 mm for the week) |
| 16–18 June 1972, Po Shan Road and Sau Mau Ping landslides | 205.9, 213.8 and 232.6 mm on 16–18 June | CEDD / Wikipedia (death toll varies, about 138 to 156, by source) |
| August 1999, Severe Tropical Storm Sam | 207.4 mm on 23 August | Wikipedia (record wettest storm at the time) |
| 7 June 2008 black rainstorm, 145.5 mm in one hour | 307.1 mm on 7 June | HKO, Interesting Statistics on Rainstorm Warning Signals |
| 7–8 September 2023 black rainstorm, more than 632 mm in 24 hours | 425.0 mm on 8 September | Wikipedia, citing the Observatory |

## Wet and dry years (365-day windows)

| Event | Source |
|---|---|
| 1982, 1997, 2005, extremely wet years (annual total above 3176 mm, 1922–2014) | HKO, projection of extremely wet and dry years |
| 1963, the driest year, 901.1 mm; water supply four hours every four days | HKO blog "Will 2018 be as dry as 1963?"; HKO virtual tour |
| 1895 and 1954, the next two driest years in the 1963 yearbook | Royal Observatory yearbook 1963 (via hkintexts) |
| 1967, supply cut from 24 to 16 hours a day in February 1967 as the dry spell continued | Hong Kong government history archive (via hkintexts); the rainfall total for 1967 was not found |

## Caveats

- Several sources are secondary (Wikipedia, Gwulo, a photo archive). Before anything is published, each should be checked against the Observatory's own record.
- "Documented" means someone noticed and wrote it down, mostly floods and droughts that hurt. A quiet but unusual stretch will not be on this list, so a score that flags it is not a false alarm.
- The 2025 events (August 2025 records) fall after our data end (January 2025) and are not used.
