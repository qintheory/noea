# Rhine and alpine reference events

Documented floods and droughts used to CHECK the river models, never to fit them. Sixteen events at seven stations (Basel has none), in
`noea/climate_pulse/river/events.py`. Each is labelled "tune" or "test" (alternating down the floods and down the
droughts), fixed in advance. The rolling model's score rule was chosen on the "tune" half only and reported on the "test"
half; with one to five events per window length in each half this is a rough check, not a validation.

Highest daily flow in our own record (GRDC and FOEN files) next to each flood, as a check that the record and the sources
describe the same event.

## Floods (30-day windows around the date)

| Event | Station | In our record | Source |
|---|---|---|---|
| Christmas flood, 24 December 1993 | Köln | 10,600 m³/s on 24 Dec | [WetterOnline](https://www.wetteronline.de/extremwetter/weihnachtshochwasser-am-rhein-evakuierungen-und-sachschaeden-1993-12-24-wh) (Köln gauge 10.63 m on 24 December) |
| | Lobith | 10,940 m³/s on 25 Dec | same (the crest reached Rees and Emmerich on 25 December) |
| Flood of January 1995 | Köln | 10,700 m³/s on 30 Jan | [WetterOnline](https://www.wetteronline.de/extremwetter/starkes-winterhochwasser-fluten-erreichen-viele-staedte-1995-01-31-jh) (record gauge mark 10.69 m on 30 January) |
| | Lobith | 11,885 m³/s on 31 Jan | same |
| Alpine flood of 21–22 August 2005 | Lustenau, Aare-Thun, Aare-Brienzwiler, Weisse Lütschine | 2,002 m³/s on 23 Aug; 551 on 23 Aug; 317 and 80 on 22 Aug | [WSL major events](https://www.wsl.ch/en/natural-hazards/understanding-and-forecasting-floods/flood-and-landslide-damage-database/major-events/); [Bern thesis](https://occrdata.unibe.ch/students/theses/msc/205.pdf) (rain from the 20th, peak on the 22nd) |
| Reuss flood, 24–25 August 1987 | Reuss-Andermatt | 102 m³/s on 25 Aug | [WSL major events](https://www.wsl.ch/en/natural-hazards/understanding-and-forecasting-floods/flood-and-landslide-damage-database/major-events/) |
| Pentecost flood, May 1999 | Aare-Thun | 560 m³/s on 15 May | Month only: no dated source was found, so the whole of May is used |

## Droughts (90-day windows over the dry months, or 365-day windows over the year)

| Event | Station | Source |
|---|---|---|
| Summer and autumn 2003 (1 July to 31 October) | Köln, Lobith | [ICPR low-water report](https://www.iksr.org/fileadmin/user_upload/DKDM/Dokumente/Fachberichte/EN/rp_En_0248.pdf) (August to September 2003 event at both gauges) |
| Summer and autumn 2018 (1 July to 30 November) | Köln, Lobith | [Phys.org / AFP, October 2018](https://phys.org/news/2018-10-drought-cripples-crucial-german-waterways.pdf) (Köln record-low level); [KNMI](https://www.knmi.nl/over-het-knmi/nieuws/zeer-lage-rijnafvoer-door-aanhoudende-droogte-in-stroomgebied) (Lobith) |
| 1947, the whole year | Köln, Lobith | [DutchNews, 2026](https://www.dutchnews.nl/2026/08/rhines-water-flow-drops-to-near-80-year-low-shipping-curbed/) (the 1947 discharge record at Lobith, 4 November); Köln is by comparison only |

## Caveats

- The earlier yearly river model was checked against a longer list (30 floods and droughts at six stations). That list is
  not in the repository; this one is smaller and every entry has a source, or says it has none.
- The 1976 drought, widely reported, is not used: no source for it was found in this search. Basel is not used for the
  same reason.
- Several sources are news and weather sites. Before anything is published, each should be checked against the gauge
  authorities' own records (BAFU/FOEN, BfG, Rijkswaterstaat).
- "Documented" means someone wrote it down, mostly floods and droughts that hurt. A quiet but unusual stretch will not be
  on this list, so a score that flags it is not a false alarm.
- Köln's record runs to 2024, Lustenau, Basel and Lobith to 2020, and the four alpine stations to 2014. Events outside
  those years, such as the July 2021 flood, cannot be checked at all stations and are not used.
