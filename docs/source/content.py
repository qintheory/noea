"""Single source of truth for the text of the Noéa introduction deck.

Both builders (build_pptx.py, build_html.py) read every word from here, so the
PowerPoint, PDF and HTML cannot drift apart. Edit the wording in this file only,
then rebuild (see README.md in this folder).

Rules for the copy (keep them when editing):

  1. Claim only what the code or the cited sources support. If something is
     designed but untested, or planned but not built, the text says so.
  2. One term per concept, used everywhere (including the repository README):

       record            one long daily series for one place: a rainfall record, or a
                         river-discharge record for one station
       diagnostic layer  frameworks.py: objective, science-based diagnostics, never adjusted for art
       curatorial layer  mapping.py: how a result should feel; designed, not measured
       valence           pleasant to unpleasant   (Russell, 1980)
       arousal           calm to activated        (Russell, 1980)
       unusual year      a year that departs far from its own record's typical year (rainfall: a high PCA
                         reconstruction error; rivers: regime.py, the share of the station's years that are less unusual)

  3. Slides carry the written claim; SPEAKER_NOTES carry the spoken version and the
     caveats. They should agree, not repeat each other word for word.
  4. Numbers (years, station counts, ranks) are checked against the data before they
     go in. The checks are listed under CHECKED FACTS at the bottom.
"""

# ---- 1. cover -------------------------------------------------------------------
COVER_TAGLINE = "Reading water as rhythm, memory and mood"
COVER_SUBTITLE = "Affective computing for water systems"
COVER_CAPTION = ("Hong Kong, 1884–2025: one beat per year. Height is the year's peak daily rainfall; "
                 "spacing is the time since the previous peak.")

# ---- 2. the gap -----------------------------------------------------------------
GAP_TITLE = ("Data can show that a river is changing.", "It rarely makes anyone feel it.")      # two lines
GAP_DECOR = "slide2_decor.jpg"      # decorative only: the river close-up, a full-height panel on the right edge
GAP_LINE = "Noéa works in the missing layer: turning measurement into meaning people can experience."

# ---- 3. how it reads ------------------------------------------------------------
READ_TITLE = "It reads a record the way a cardiologist reads an ECG"
# (number, heading, [paragraphs], emphasised)
READ_STEPS = [
    ("01", "A long record",
     ["Daily rainfall or river discharge, covering decades to two centuries."], False),
    ("02", "ECG-inspired diagnostics",
     ["Rainfall: annual peaks, the gaps between them, return periods.",
      "Rivers: flow duration, recession, the seasonal cycle."], False),
    ("03", "Two affective values",
     ["Valence: pleasant to unpleasant.",
      "Arousal: calm to activated.",
      "Set by design in the curatorial layer."], True),
    ("04", "XR experience",
     ["Two XR prototypes exist.",
      "Next: connect them to the analysis and to real scenarios."], False),
]
READ_SOURCE = ("Valence and arousal follow Russell's circumplex model of affect: Russell, J. A. (1980), "
               "Journal of Personality and Social Psychology, 39(6), 1161–1178. Adopted in Noéa Issue 4.")

# ---- 4. universal ---------------------------------------------------------------
UNIV_TITLE = "Designed to be universal"
UNIV_LINE = ("Each record fits its own model on its own history. "
             "Other long rainfall or river records are designed to go through the same pipeline.")
# (name, detail, dimmed)
UNIV_ROWS = [
    ("Hong Kong rainfall", "Public record, Hong Kong Observatory. Daily, 1884–2025.", False),
    ("Rhine and alpine rivers", "Public records, GRDC and FOEN. Daily, 8 stations.", False),
    ("The next record", "TBA", True),
]

# ---- 5. two layers --------------------------------------------------------------
LAYERS_TITLE = "Two layers, kept deliberately apart"
LAYER_SCIENCE = ("Diagnostic layer", "Science", [
    "Rainfall, Hong Kong 1884–2025: annual peaks, the gaps between them, return periods.",
    "Rivers, Rhine and alpine, 8 stations: flow duration, recession, the seasonal cycle.",
    "Measures what happened, and is never changed to suit the design.",
])
LAYER_CURATORIAL = ("Curatorial layer", "Designed", [
    "Decides how a result should feel: how alarming, how heavy.",
    "Developed separately in Unity3D, for presentation and exhibition.",
    "Output: valence and arousal. Designed, and for Hong Kong also learned from the record; checked "
    "against named historical events, not yet tested with viewers.",
])

# ---- 6. machine learning --------------------------------------------------------
ML_TITLE = "Machine learning finds unusual years"
ML_SUBTITLE = "Unsupervised: learn what a typical year looks like for each record, then score how unusual each year is."
ML_CALLOUT_BOLD = "Outlined: each station's most unusual year, 1951–2020."
ML_CALLOUT_REST = "The model was never told what happened in any of them."
ML_CHART_ALT = ("The Rhine ribbon redrawn with colour showing how unusual each year was for its station; the most unusual year at "
                "Lustenau (2005), Basel (2018), and Köln and Lobith (1952) is outlined")
ML_METHOD = ("Method: a probabilistic PCA of each year against its station's own typical year, one model per station. "
             "2005: Alpine floods (Lustenau). 2018: the summer drought (Basel). 1952: much winter water, a dry summer (Köln, Lobith).")
ML_LIMIT = ("Limit: it says how unusual, not which way. Of 30 documented floods and droughts, 22 score 0.70 or higher; a summer-only "
            "drought such as 2003 reads as ordinary at Köln (0.43). Those events were looked at while the model was built.")

# ---- 7. the end -----------------------------------------------------------------
END_TITLE = "The end result is how people respond"
END_LINE = "Noéa links machine intelligence to natural intelligence."
END_RESEARCH = "Do people feel what it flags? That is the research."
END_DECOR = "atmosphere.jpg"      # decorative only: the blue atmosphere piece, about 60% of it visible, bleeding off the right edge, plain white elsewhere
END_URL_TEXT = "meetingofwaters.org/noea"
END_URL = "https://www.meetingofwaters.org/noea"

# ---- speaker notes (spoken version; caveats live here) ---------------------------
SPEAKER_NOTES = {
    1: ("Noéa translates long hydrological records into something people can experience. "
        "The line on screen is real data: Hong Kong's annual peak daily rainfall, 1884 to 2025, one beat per year."),
    2: ("Long records already show that rivers and rainfall are changing, as charts and indices. "
        "Noéa is an attempt to translate that into something people can perceive. "
        "Whether it works is the research question at the end."),
    3: ("Noéa reads a rainfall or river record the way an ECG is read, in the sense of Issue 3: rhythm, memory, shock. "
        "From the diagnostics it derives two affective values, valence and arousal, from Russell's circumplex model of affect: "
        "how pleasant or unpleasant, and how calm or activated. They are design decisions about how a result should feel, "
        "not properties of the water. Two XR prototypes exist; the next step is to connect them to the analysis and to real scenarios."),
    4: ("The method is designed to be universal: every record fits its own model on its own history. "
        "Hong Kong rainfall and the Rhine and alpine rivers are the only two records run so far. "
        "Another rainfall or river record is designed to pass through the same pipeline, but that has not been tested."),
    5: ("There are two layers, kept apart on purpose. The diagnostic layer is plain science: Hong Kong's daily rainfall "
        "since 1884, and discharge at eight Rhine and alpine stations. The curatorial layer decides how a result should feel. "
        "It is separate code, so the feeling can be redesigned without changing any science. Its output is valence and arousal, "
        "chosen by design and checked against named historical events. For Hong Kong rainfall there is also a learned reading: "
        "two PCA factors, storminess and wetness, plus the anomaly score, ranked within the record. Seven of eight checks fixed in advance "
        "pass; valence and arousal correlate at minus 0.71, just past the limit. None of it has been tested with people."),
    6: ("Machine learning has one job so far: finding unusual years. For each record an unsupervised model learns what a "
        "typical year looks like, the rhythm of its months, its floods and its low flows, then scores how unusual each year is, as the "
        "share of that station's own years that are less unusual. The ribbon is the one from Issue 6, but coloured by that score instead "
        "of by discharge. At Lustenau the most unusual year is the August 2005 flood, and at Basel it is 2018, the summer drought. "
        "At Köln and Lobith it is 1952, a year with much winter water and a dry summer, and none of this was told to the model. "
        "It is not a perfect event detector. Checked against 30 documented floods and droughts at six stations, 22 score 0.70 or higher: "
        "Basel 1972 scores 0.95, the 2005 Alpine floods about 0.99 at Lustenau and Thun, the 1976 drought 0.81 at Köln. A summer-only "
        "drought such as 2003 reads as ordinary at Köln, at 0.43, and the 1993 Köln flood scores 0.68. Those events were looked at while "
        "the model was built, so this is a sanity check, not a validation. The earlier model scored only how badly a year's combination "
        "of ratios failed to reconstruct, and left the 1976 drought looking ordinary at Köln. Hong Kong rainfall still uses that earlier "
        "kind of score, and the score does not say which way a year departed."),
    7: ("Noéa connects machine intelligence to natural intelligence: a model learns the rhythm of a river or rainfall record "
        "and flags the years that break it. What nobody has tested is whether people feel what the system intends. "
        "That has to be studied in human labs, with HCI methods. That is the research."),
}

# ---- references (also in the repository README) ------------------------------------
REFERENCES = [
    "Russell, J. A. (1980). A circumplex model of affect. Journal of Personality and Social Psychology, 39(6), 1161–1178.",
    "Noéa Issue 3, “Hong Kong Heartbeat” (March 2025); Issue 4, “Affective Climate” (June 2025); "
    "Issue 6, “River Anatomy” (April 2026). https://www.meetingofwaters.org/noea",
]

# ---- CHECKED FACTS (re-verify when data or models change) --------------------------
# * Hong Kong record: HKO daily rainfall, 1884–2025 (2025 is a partial year, scored but not fitted).
# * River records: 8 stations (4 Rhine, GRDC; 4 alpine, FOEN). Longest: Köln from 1816.
# * Hong Kong valence and arousal (affect.py, checked 2026-10-29): 135 years on record (1940-1946 missing), 134 fitted,
#   2025 partial (26 days). arousal~anomaly +0.65, valence~anomaly -0.64, valence~arousal -0.71 (7 of 8 pre-set checks pass; the
#   limit was |r| <= 0.70). 1926: valence -0.99, arousal 0.97; 2023: -0.95, 0.92; 1963: -0.48, 0.24. Relative ranks, not measurements.
# * The XRParameters table (size, glow, texture, tempo) is deliberately NOT on the slides: it is unconfirmed
#   scaffolding (see README), not from the Issues, and glow (luminosity) is a constant 0.5 without temperature data.
# * Rivers (regime.py, checked 2026-10-29): 22 of 30 documented floods and droughts score 0.70 or higher across six stations
#   (Basel 1972 0.95, Basel 2018 0.99, Köln 1947 0.96, Lustenau 2005 0.99, Köln 1976 0.81; Köln 2003 0.43, Lobith 2003 0.39). Most
#   unusual year in 1951-2020: Lustenau 2005, Basel 2018, Köln 1952, Lobith 1952. The events were looked at while the model was built.
# * Hong Kong rainfall still uses the PCA anomaly model, 2 components. Fitted years only: Hong Kong 1926 ranks 7th
#   and 2023 19th of 134; the 1963 drought ranks 98th (checked 2026-10-17).
# * Anomaly ribbon (slide 6), fitted-year ranks, checked 2026-10-17: highest in 1951-2020 is Lustenau 2005, Basel 1972
#   (Basel's all-time highest is 1881, outside the window), Köln 1993, Lobith 1993. 1976 ranks 3rd of 70 (Lustenau),
#   13th of 152 (Basel), 187th of 208 (Köln), 116th of 120 (Lobith). 1995 at Köln ranks 101st. So droughts are caught
#   at some stations and missed at others: never write "does not flag droughts" without that qualifier.
# * The project's images (river close-up on slide 2, blue atmosphere on slide 7) are decorative design material:
#   never labelled, captioned or used as evidence.
