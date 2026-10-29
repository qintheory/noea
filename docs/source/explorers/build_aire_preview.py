"""Write docs/explore/_aire-preview.html: the local L'Aire page with data/hwi.json inlined, so it opens from a single file
(for example as an attachment to OCEau). The output is git-ignored with the data; it is not for publication.

    python3 docs/source/explorers/build_aire_preview.py
"""
from __future__ import annotations
import json
from pathlib import Path

EXPLORE = Path(__file__).resolve().parents[2] / "explore"


def main():
    page = (EXPLORE / "_aire.html").read_text(encoding="utf-8")
    data = json.dumps(json.loads((EXPLORE / "data" / "hwi.json").read_text(encoding="utf-8")), separators=(",", ":"), ensure_ascii=False)
    marker = "<script>\n(function () {"
    assert marker in page
    out = EXPLORE / "_aire-preview.html"
    out.write_text(page.replace(marker, "<script>window.__HWI__=" + data.replace("</", "<\\/") + ";</script>\n" + marker, 1), encoding="utf-8")
    print(out, f"{out.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
