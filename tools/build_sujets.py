"""Build site/tuteur/sujets.js: topics and opening questions per subject and class.

Sources: agents/kb/programmes/<matiere>-topics.json (from the official programmes), and
agents/sujets-3e.json (hand-written brevet bank, used for 3e).
Usage: python3 tools/build_sujets.py
"""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROG = ROOT / "agents/kb/programmes"
KEYS = {"histoire": "histoire-geo", "maths": "maths", "francais": "francais"}
brevet = json.loads((ROOT / "agents/sujets-3e.json").read_text(encoding="utf-8"))
out = {}
for key, fname in KEYS.items():
    levels = json.loads((PROG / f"{fname}-topics.json").read_text(encoding="utf-8"))
    levels["3e"] = brevet[key]
    out[key] = levels
    print(key, {k: len(v) for k, v in levels.items()})
(ROOT / "site/tuteur/sujets.js").write_text(
    "// Built by tools/build_sujets.py from agents/kb/programmes/*-topics.json. Do not edit by hand.\n"
    "window.SUJETS = " + json.dumps(out, ensure_ascii=False, indent=1) + ";\n", encoding="utf-8")
