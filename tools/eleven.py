"""ElevenLabs SDK client for the tutor scripts.

The key lives in .env (ELEVENLABS_API_KEY, gitignored), never in code.
Install: python3 -m pip install -r tools/requirements.txt
"""
import pathlib

from dotenv import load_dotenv

# Load .env before importing the SDK: it reads the key from the environment at import time.
load_dotenv(pathlib.Path(__file__).resolve().parent.parent / ".env")
from elevenlabs.client import ElevenLabs  # noqa: E402
client = ElevenLabs()  # reads ELEVENLABS_API_KEY from the environment

if __name__ == "__main__":
    # Smoke test: list this account's agents.
    for a in client.conversational_ai.agents.list().agents:
        print(a.agent_id, a.name)
