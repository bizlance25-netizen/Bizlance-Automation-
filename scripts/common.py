"""
common.py — shared helpers for the Bizlance automation scripts.

All scripts import from here so there's one place to swap the LLM/image
provider later (e.g. from free Pollinations to a paid Claude/OpenAI key)
without touching every script.
"""
import os
import re
import json
import urllib.parse
import requests

POLLINATIONS_TEXT_BASE = "https://text.pollinations.ai"
POLLINATIONS_IMAGE_BASE = "https://image.pollinations.ai/prompt"


def env(key: str, required: bool = True, default: str = None) -> str:
    """Read a config value from environment variables (set as GitHub Actions secrets)."""
    val = os.environ.get(key, default)
    if required and not val:
        raise RuntimeError(f"Missing required environment variable: {key}")
    return val


def generate_text(prompt: str, retries: int = 2) -> str:
    """Free text generation via Pollinations. Returns raw string response."""
    url = f"{POLLINATIONS_TEXT_BASE}/{urllib.parse.quote(prompt)}"
    key = os.environ.get("POLLINATIONS_KEY")
    params = {"key": key} if key else {}
    last_err = None
    for _ in range(retries + 1):
        try:
            r = requests.get(url, params=params, timeout=60)
            r.raise_for_status()
            return r.text
        except Exception as e:
            last_err = e
    raise RuntimeError(f"Pollinations text generation failed: {last_err}")


def generate_text_json(prompt: str) -> dict:
    """Ask the model for JSON and parse it, tolerating stray text around it."""
    raw = generate_text(prompt)
    match = re.search(r"\{[\s\S]*\}", raw)
    try:
        return json.loads(match.group(0) if match else raw)
    except Exception:
        return {"raw": raw}


def generate_image_url(prompt: str, width: int = 1200, height: int = 630) -> str:
    """Free image generation via Pollinations. Returns a hotlinkable URL (no download needed).
    Kept as a free fallback — the social scripts now use OpenAI images by default (see below)."""
    key = os.environ.get("POLLINATIONS_KEY")
    q = urllib.parse.quote(prompt)
    url = f"{POLLINATIONS_IMAGE_BASE}/{q}?width={width}&height={height}&nologo=true"
    if key:
        url += f"&key={key}"
    return url


def generate_image_openai(prompt: str, size: str = "1024x1024") -> bytes:
    """Generate an image via OpenAI's Images API. Returns raw PNG bytes.
    size must be one of the sizes OpenAI's current image model supports
    (e.g. "1024x1024", "1024x1536", "1536x1024" — check platform.openai.com/docs
    if this errors, supported sizes do change between model versions)."""
    api_key = env("OPENAI_API_KEY")
    resp = requests.post(
        "https://api.openai.com/v1/images/generations",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": "gpt-image-1", "prompt": prompt, "size": size, "n": 1},
        timeout=120,
    )
    resp.raise_for_status()
    b64 = resp.json()["data"][0]["b64_json"]
    import base64
    return base64.b64decode(b64)


def upload_image_public(image_bytes: bytes, name: str = "bizlance-post") -> str:
    """Uploads image bytes to a free public host (imgbb) and returns a hotlinkable URL.
    Needed because Instagram/Facebook's Graph API requires a public image_url, and
    OpenAI's image API returns raw bytes, not a hosted URL, unlike Pollinations."""
    api_key = env("IMGBB_API_KEY")
    import base64
    resp = requests.post(
        "https://api.imgbb.com/1/upload",
        data={"key": api_key, "name": name, "image": base64.b64encode(image_bytes).decode()},
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    if not data.get("success"):
        raise RuntimeError(f"imgbb upload failed: {data}")
    return data["data"]["url"]


def load_json_lines(path: str) -> list:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def append_json_line(path: str, obj: dict):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def day_index(length: int, offset: int = 0) -> int:
    """Stable day-of-epoch index for rotating through a list, deterministic across runs."""
    import datetime
    return (datetime.date.today().toordinal() + offset) % max(length, 1)


def pick_alternating(buyer_list: list, provider_list: list):
    """Alternates Buyer/Provider content day by day. Returns (segment, item)."""
    import datetime
    day = datetime.date.today().toordinal()
    if day % 2 == 0:
        return "buyer", buyer_list[day_index(len(buyer_list))]
    else:
        return "provider", provider_list[day_index(len(provider_list))]
