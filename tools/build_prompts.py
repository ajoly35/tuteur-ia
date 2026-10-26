"""Assemble the full system prompt of each agent into agents/build/<key>.txt.

Usage: python3 tools/build_prompts.py
"""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
cfg = json.loads((ROOT / "agents/agents.json").read_text(encoding="utf-8"))
out = ROOT / "agents/build"
out.mkdir(exist_ok=True)
for key, a in cfg["agents"].items():
    parts = []
    for f in a["prompt_files"]:
        text = (ROOT / "agents/prompts" / f).read_text(encoding="utf-8")
        # Drop the file's own top-level title line; keep the rest.
        lines = text.splitlines()
        if lines and lines[0].startswith("# "):
            lines = lines[1:]
        parts.append("\n".join(lines).strip())
    prompt = "\n\n".join(parts[::-1]) if len(parts) > 1 else parts[0]
    (out / f"{key}.txt").write_text(prompt + "\n", encoding="utf-8")
    print(f"{key}: {len(prompt):,} characters")
