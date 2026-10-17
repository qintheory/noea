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
       unusual year      a year with a high anomaly score (PCA reconstruction error)

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
    "Output: valence and arousal. Set by design judgement and checked against named historical "
    "events; not yet tested with viewers.",
])

# ---- 6. machine learning --------------------------------------------------------
ML_TITLE = "Machine learning finds unusual years"
ML_SUBTITLE = "Unsupervised: learn what a typical year looks like for each record, then score how badly each year fits."
ML_CALLOUT_BOLD = "Outlined: each station's highest-scoring year, 1951–2020."
ML_CALLOUT_REST = "The model was never told what happened in any of them."
ML_CHART_ALT = ("The Rhine ribbon redrawn with colour showing the model's anomaly score per year; the highest-scoring "
                "year at Lustenau (2005), Basel (1972), Köln and Lobith (1993) is outlined")
ML_METHOD = ("Method: PCA reconstruction error, one model per station. 1993: Christmas Rhine flood (Köln, Lobith). "
             "2005: Alpine floods (Lustenau). 1972: a drought year in Issue 6.")
ML_LIMIT = ("Limit: it flags unusual combinations, not extremes. 1976 drought: 3rd of 70 years at Lustenau, "
            "187th of 208 at Köln. 1995 Köln flood: 101st.")

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
        "chosen by design and checked against named historical events. It has not been tested with people."),
    6: ("Machine learning has one job so far: finding unusual years. For each record an unsupervised model learns what a "
        "typical year looks like, then scores how badly each year fails to fit. The ribbon is the one from Issue 6, but coloured by "
        "the model's score instead of by discharge. At Lustenau the highest-scoring year is the August 2005 flood and at Köln "
        "and Lobith the Christmas 1993 flood; none was told to the model. At Basel it is 1972, a drought year in Issue 6. "
        "It is not a drought detector, though: 1976 ranks third of 70 at Lustenau but 187th of 208 at Köln, and the 1995 Köln "
        "flood ranks 101st. In Hong Kong the same model ranks 1926 seventh and 2023 nineteenth of 134 complete years, "
        "and the 1963 drought 98th. It flags unusual combinations of features, not every extreme. "
        "On the Aare at Thun, not shown, the highest year is the May 1999 Swiss flood."),
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
# * The XRParameters table (size, glow, texture, tempo) is deliberately NOT on the slides: it is unconfirmed
#   scaffolding (see README), not from the Issues, and glow (luminosity) is a constant 0.5 without temperature data.
# * PCA anomaly model, 2 components, one model per record. Fitted years only: Hong Kong 1926 ranks 7th
#   and 2023 19th of 134; the 1963 drought ranks 98th (checked 2026-10-17).
# * Anomaly ribbon (slide 6), fitted-year ranks, checked 2026-10-17: highest in 1951-2020 is Lustenau 2005, Basel 1972
#   (Basel's all-time highest is 1881, outside the window), Köln 1993, Lobith 1993. 1976 ranks 3rd of 70 (Lustenau),
#   13th of 152 (Basel), 187th of 208 (Köln), 116th of 120 (Lobith). 1995 at Köln ranks 101st. So droughts are caught
#   at some stations and missed at others: never write "does not flag droughts" without that qualifier.
# * The project's images (river close-up on slide 2, blue atmosphere on slide 7) are decorative design material:
#   never labelled, captioned or used as evidence.
