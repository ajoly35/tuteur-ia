"""Create (or update) the four ElevenLabs agents from agents/agents.json, then write their IDs into the site.

Run it with the API key of the account that should own the agents (personal account, not the LSE workspace):
    ELEVENLABS_API_KEY=sk_... python3 tools/create_agents.py
Re-running updates the existing agents (IDs kept in agents/created.json) instead of creating duplicates.
Standard library only. Untested against the live API: if a field is rejected, the error is printed and
the script moves on, so read the output.
"""
import json
import os
import pathlib
import re
import subprocess
import sys
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
API = "https://api.elevenlabs.io/v1"
KEY = os.environ.get("ELEVENLABS_API_KEY")
if not KEY:
    sys.exit("Set ELEVENLABS_API_KEY to the personal account's key.")

cfg = json.loads((ROOT / "agents/agents.json").read_text(encoding="utf-8"))
state_path = ROOT / "agents/created.json"
state = json.loads(state_path.read_text()) if state_path.exists() else {"kb": {}, "tools": {}, "agents": {}}


def call(method, path, body=None):
    req = urllib.request.Request(API + path, method=method, headers={"xi-api-key": KEY, "Content-Type": "application/json"},
                                 data=json.dumps(body).encode() if body is not None else None)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        print(f"  ! {method} {path} -> {e.code}: {e.read().decode()[:800]}")
        return None


def kb_doc(fname):
    if fname in state["kb"]:
        return state["kb"][fname]
    p = ROOT / "agents/kb" / fname
    if not p.exists():
        print(f"  ! missing knowledge file {p}")
        return None
    r = call("POST", "/convai/knowledge-base/text", {"name": fname, "text": p.read_text(encoding="utf-8")})
    if r and r.get("id"):
        state["kb"][fname] = {"id": r["id"], "name": fname}
        print(f"  + knowledge {fname}: {r['id']}")
        return state["kb"][fname]
    return None


def client_tool(t):
    if t["name"] in state["tools"]:
        return state["tools"][t["name"]]
    props = {k: {"type": "string", "description": v} for k, v in t["parameters"].items()}
    body = {"tool_config": {"type": "client", "name": t["name"], "description": t["description"], "expects_response": True,
                            "response_timeout_secs": 10,
                            "parameters": {"type": "object", "properties": props, "required": [list(props)[0]]}}}
    r = call("POST", "/convai/tools", body)
    if r and r.get("id"):
        state["tools"][t["name"]] = r["id"]
        print(f"  + tool {t['name']}: {r['id']}")
        return r["id"]
    return None


def guardrails():
    g = cfg["guardrails"]
    return {
        "version": "1",
        "focus": {"is_enabled": True},
        "prompt_injection": {"is_enabled": True},
        "moderation": {"config": {k: {"is_enabled": True, "threshold": 0.3} for k in
                                  ["sexual", "sexual_minors", "self_harm_instructions", "violence_graphic", "hate", "hate_threatening", "harassment_threatening"]}},
        "custom": {"config": {"configs": [{
            "name": "Pas de devoirs à la place de l'élève", "prompt": g["homework"], "is_enabled": True,
            "execution_mode": "blocking", "history_message_count": 2, "model": "gemini-3.1-flash-lite",
            "trigger_action": {"type": "retry", "feedback": g["homework_feedback"]}}]}},
    }


def save():
    state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False))


subprocess.run([sys.executable, str(ROOT / "tools/build_prompts.py")], check=True)
for key, a in cfg["agents"].items():
    print(f"\n== {key}")
    kb = [dict(type="text", usage_mode="auto", **d) for d in (kb_doc(f) for f in a["kb_files"]) if d]
    tools = [tid for tid in (client_tool(t) for t in a.get("client_tools", [])) if tid]
    save()
    prompt = (ROOT / "agents/build" / f"{key}.txt").read_text(encoding="utf-8")
    body = {
        "name": a["name"],
        "tags": ["tuteur-ia", "prototype"],
        "conversation_config": {
            "agent": {
                "first_message": a["first_message"],
                "language": cfg["language"],
                "dynamic_variables": {"dynamic_variable_placeholders": a["dynamic_variables"]},
                "prompt": {"prompt": prompt, "llm": cfg["llm"], "temperature": 0.3, "knowledge_base": kb, "tool_ids": tools,
                           "timezone": "Europe/Paris",
                           # Lets the agent switch language mid-call when the pupil speaks or asks for English.
                           "built_in_tools": {"language_detection": {"name": "language_detection", "description": "",
                                                                     "params": {"system_tool_type": "language_detection"}}}},
            },
            "language_presets": {lang: {"overrides": {"agent": {"language": lang, "first_message": a[f"first_message_{lang}"]}}}
                                 for lang in cfg.get("extra_languages", [])},
            "tts": {"voice_id": a["voice_id"], "model_id": cfg.get("tts_model", "eleven_flash_v2_5")},
            "conversation": {"max_duration_seconds": 600},  # 10 min: public links, pay-as-you-go plan
        },
        "platform_settings": {
            "overrides": {"conversation_config_override": {"tts": {"voice_id": bool(a.get("allow_voice_override"))}}},
            "guardrails": guardrails(),
            # Cost ceiling for public links: 20 conversations a day, 2 at once, no paid bursting.
            "call_limits": {"agent_concurrency_limit": 2, "daily_limit": 20, "bursting_enabled": False},
        },
    }
    if key in state["agents"]:
        r = call("PATCH", f"/convai/agents/{state['agents'][key]}", body)
        print("  ~ updated" if r is not None else "  ! update failed")
    else:
        r = call("POST", "/convai/agents/create", body)
        if r and r.get("agent_id"):
            state["agents"][key] = r["agent_id"]
            print(f"  + agent {r['agent_id']}")
    save()

# Write the IDs into the site config.
js = ROOT / "site/assets/voix.js"
text = js.read_text(encoding="utf-8")
for key, aid in state["agents"].items():
    text = re.sub(rf'({key}: )"[^"]*"', rf'\1"{aid}"', text, count=1)
js.write_text(text, encoding="utf-8")
print("\nAgent IDs written to site/assets/voix.js:", json.dumps(state["agents"], indent=2))
