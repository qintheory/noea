"""Build the combined Noéa page into docs/ (served by GitHub Pages, embedded in Webflow as one iframe).

    python3 docs/source/explorers/build_site.py            # run from the repository root
    python3 docs/source/explorers/build_site.py --assets   # only the scripts, styles and page (keeps the data files as they are)

Writes docs/index.html and docs/explore/ (engine.js, site.js, site.css, data/*.json). The data is computed
from the pipeline, the same way the standalone pages are. The L'Aire chapter needs the OCEau data
(python3 -m noea.human_water_interface.fetch); without it the site is built without that chapter's data file
and the page says the chapter is not published yet. docs/explore/data/hwi.json is git-ignored on purpose:
add it to a commit only once the OCEau data may be republished.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, ".")
from build_explorers import PAGES                                   # noqa: E402

DOCS = Path("docs")


def main():
    out = DOCS / "explore"; (out / "data").mkdir(parents=True, exist_ok=True)
    for key, page in ({} if "--assets" in sys.argv else PAGES).items():
        p = dict(page); fn = p.pop("fn")
        try:
            payload = dict(p, **fn())
        except Exception as e:                                       # e.g. the OCEau files have not been fetched
            print(f"skipped {key}: {type(e).__name__}: {e}")
            continue
        (out / "data" / f"{ {'rainfall': 'rainfall', 'river': 'river', 'hwi': 'hwi'}[key] }.json").write_text(
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        print("data", key)
    (out / "engine.js").write_text((HERE / "engine.js").read_text(encoding="utf-8"), encoding="utf-8")
    (out / "noea-wordmark.png").write_bytes((HERE.parent / "assets" / "noea_wordmark_web.png").read_bytes())          # the Noéa logo, top left
    (out / "heart.js").write_text((HERE / "heart.js").read_text(encoding="utf-8"), encoding="utf-8")
    (out / "site.js").write_text((HERE / "site.js").read_text(encoding="utf-8"), encoding="utf-8")
    (out / "site.css").write_text((HERE / "engine.css").read_text(encoding="utf-8") + "\n" + (HERE / "site.css").read_text(encoding="utf-8"), encoding="utf-8")
    page = (HERE / "site.html").read_text(encoding="utf-8").replace("/*__FRAGMENT__*/", (HERE / "fragment.html").read_text(encoding="utf-8"))
    (DOCS / "index.html").write_text(page, encoding="utf-8")
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")
    print("wrote docs/index.html and docs/explore/")


if __name__ == "__main__":
    main()
