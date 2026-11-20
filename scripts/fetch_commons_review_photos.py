#!/usr/bin/env python3
"""Fetch allowlisted Commons originals for internal visual review; never publication."""
from __future__ import annotations
import hashlib, json, urllib.parse, urllib.request
from pathlib import Path

OUT = Path("media-review")
MAX_BYTES = 25 * 1024 * 1024
USER_AGENT = "representation-psychology-media-review/1.0"
FILES = (
    "Freud_anuncio_consultorio.jpg",
    "Puerta_Consultorio_Freud.jpg",
    "Freuds_Wartezimmer_in_der_Berggasse_19.jpg",
)

def sha1_base36(data: bytes) -> str:
    value = int.from_bytes(hashlib.sha1(data).digest(), "big")
    alphabet = "0123456789abcdefghijklmnopqrstuvwxyz"
    if value == 0:
        return "0"
    result = ""
    while value:
        value, remainder = divmod(value, 36)
        result = alphabet[remainder] + result
    return result

def validate_url(url: str) -> None:
    parsed = urllib.parse.urlparse(url)
    if (parsed.scheme != "https" or parsed.hostname != "upload.wikimedia.org"\n            or parsed.port not in (None, 443) or parsed.username or parsed.password):
        raise ValueError(f"Unexpected download URL: {url}")

def fetch_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as response:
        if response.status != 200:
            raise RuntimeError(f"Commons API HTTP {response.status}")
        return json.loads(response.read(2 * 1024 * 1024))

def fetch_file(title: str) -> dict:
    params = urllib.parse.urlencode({
        "action": "query", "format": "json", "prop": "imageinfo",
        "iiprop": "url|sha1|size|mime", "titles": f"File:{title}",
    })
    data = fetch_json("https://commons.wikimedia.org/w/api.php?" + params)
    page = next(iter(data.get("query", {}).get("pages", {}).values()), {})
    info = (page.get("imageinfo") or [{}])[0]
    if not info or "missing" in page:
        raise ValueError(f"Commons file not found: {title}")
    url = info.get("url", "")
    validate_url(url)
    size, expected_sha1 = int(info.get("size", 0)), info.get("sha1", "")
    if info.get("mime") != "image/jpeg" or not expected_sha1 or not 0 < size <= MAX_BYTES:
        raise ValueError(f"Unexpected MIME/size/hash metadata for {title}")
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as response:
        if response.status != 200:
            raise RuntimeError(f"Image HTTP {response.status}")
        validate_url(response.geturl())
        content = response.read(MAX_BYTES + 1)
    if len(content) != size or hashlib.sha1(content).hexdigest() != expected_sha1:
        raise ValueError(f"Size/SHA-1 verification failed for {title}")
    if not content.startswith(b"\xff\xd8\xff") or not content.endswith(b"\xff\xd9"):
        raise ValueError(f"Invalid JPEG signature: {title}")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / title).write_bytes(content)
    return {
        "file": title, "commons_title": f"File:{title}",
        "description_url": f"https://commons.wikimedia.org/wiki/File:{urllib.parse.quote(title)}",
        "mime": info["mime"], "size": size, "commons_sha1_hex": expected_sha1,
        "sha256": hashlib.sha256(content).hexdigest(),
        "review_scope": "internal visual/editorial review only; not legal approval",
    }

def main() -> None:
    manifest = {
        "notice": "Review artifact only: not copied to public/, not registered as approved, and not cleared for publication.",
        "files": [fetch_file(title) for title in FILES],
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Fetched and verified {len(manifest['files'])} Commons originals.")

if __name__ == "__main__":
    main()
