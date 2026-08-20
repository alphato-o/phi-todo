import json
import os
from pathlib import Path

import httpx

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-4o-mini"


def _api_key():
    key = os.environ.get("OPENROUTER_API_KEY")
    if key:
        return key.strip()
    secret = Path(__file__).resolve().parent.parent / "secret.txt"
    if secret.exists():
        for line in secret.read_text().splitlines():
            line = line.strip()
            if line.startswith("sk-"):
                return line
    raise RuntimeError(
        "No OpenRouter API key found. Set OPENROUTER_API_KEY or put the key in secret.txt at the repo root."
    )


def chat_json(system, user):
    """Ask the model a question and get JSON back."""
    resp = httpx.post(
        OPENROUTER_URL,
        headers={"Authorization": f"Bearer {_api_key()}"},
        json={
            "model": os.environ.get("PHI_MODEL", DEFAULT_MODEL),
            "temperature": 1.0,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        },
        timeout=90,
    )
    resp.raise_for_status()
    content = resp.json()["choices"][0]["message"]["content"]
    return json.loads(content)
