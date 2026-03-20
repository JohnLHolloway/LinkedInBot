import base64
import io
import logging
import random

import aiohttp

from config import XAI_API_KEY

log = logging.getLogger(__name__)

_API_BASE = "https://api.x.ai/v1"
_MODEL = "grok-imagine-image"
_ALLOWED_HOSTS = {
    "cdn.discordapp.com",
    "media.discordapp.net",
    "images-ext-1.discordapp.net",
    "images-ext-2.discordapp.net",
}
_MAX_DOWNLOAD = 10 * 1024 * 1024  # 10 MB
_MAGIC = {
    b"\x89PNG": "png",
    b"\xff\xd8\xff": "jpeg",
    b"GIF8": "gif",
    b"RIFF": "webp",
}


async def _download_image(url: str, session: aiohttp.ClientSession) -> bytes:
    from urllib.parse import urlparse

    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in _ALLOWED_HOSTS:
        raise ValueError("Only Discord CDN images are supported.")

    async with session.get(url) as resp:
        resp.raise_for_status()
        data = await resp.read()

    if len(data) > _MAX_DOWNLOAD:
        raise ValueError("Image too large (max 10 MB).")

    if not any(data.startswith(magic) for magic in _MAGIC):
        raise ValueError("Unsupported image format.")

    return data


async def generate_image(system_prompt: str, user_prompt: str) -> bytes:
    prompt = f"{system_prompt}\n\n{user_prompt}"
    payload = {
        "model": _MODEL,
        "prompt": prompt,
        "n": 1,
        "response_format": "b64_json",
        "seed": random.getrandbits(32),
    }
    headers = {
        "Authorization": f"Bearer {XAI_API_KEY}",
        "Content-Type": "application/json",
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{_API_BASE}/images/generations", json=payload, headers=headers
        ) as resp:
            resp.raise_for_status()
            body = await resp.json()

    b64 = body["data"][0]["b64_json"]
    if b64.startswith("data:"):
        b64 = b64.split(",", 1)[1]
    return base64.b64decode(b64)


async def edit_image(
    system_prompt: str, user_prompt: str, image_url: str
) -> bytes:
    async with aiohttp.ClientSession() as session:
        image_bytes = await _download_image(image_url, session)

    b64_image = base64.b64encode(image_bytes).decode()
    prompt = f"{system_prompt}\n\n{user_prompt}"
    payload = {
        "model": _MODEL,
        "prompt": prompt,
        "n": 1,
        "response_format": "b64_json",
        "seed": random.getrandbits(32),
        "image": {
            "url": f"data:image/png;base64,{b64_image}",
            "type": "image_url",
        },
    }
    headers = {
        "Authorization": f"Bearer {XAI_API_KEY}",
        "Content-Type": "application/json",
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{_API_BASE}/images/edits", json=payload, headers=headers
        ) as resp:
            resp.raise_for_status()
            body = await resp.json()

    b64 = body["data"][0]["b64_json"]
    if b64.startswith("data:"):
        b64 = b64.split(",", 1)[1]
    return base64.b64decode(b64)


async def generate_text(system_prompt: str, user_prompt: str) -> str:
    payload = {
        "model": "grok-3-mini",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.9,
        "max_tokens": 1024,
    }
    headers = {
        "Authorization": f"Bearer {XAI_API_KEY}",
        "Content-Type": "application/json",
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{_API_BASE}/chat/completions", json=payload, headers=headers
        ) as resp:
            resp.raise_for_status()
            body = await resp.json()

    return body["choices"][0]["message"]["content"]
