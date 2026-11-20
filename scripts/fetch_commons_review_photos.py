#!/usr/bin/env python3
"""Fetch allowlisted Commons originals for internal visual review; never publication."""
from __future__ import annotations

import hashlib
import json
import urllib.parse
import urllib.request
from pathlib import Path

OUT = Path("media-review")
MAX_BYTES = 25 * 1024 * 1024
USER_AGENT = "representation-psychology-media-review/1.0"
FILES = (
    "Freud_anuncio_consultorio.jpg",
    "Puerta_Consultorio_Freud.jpg",
    "Freuds_Wartezimmer_in_der_Berggasse_19.jpg",
)
PROVENANCE = {
    "Freud_anuncio_consultorio.jpg": {
        "creator": "Marjorie Apel",
        "license": "CC BY-SA 3.0",
        "license_url": "https://creativecommons.org/licenses/by-sa/3.0/",
    },
    "Puerta_Consultorio_Freud.jpg": {
        "creator": "Marjorie Apel",
        "license": "CC BY-SA 3.0",
        "license_url": "https://creativecommons.org/licenses/by-sa/3.0/",
    },
    "Freuds_Wartezimmer_in_der_Berggasse_19.jpg": {
        "creator": "Siesta",
        "license": "CC BY-SA 4.0",
        "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
    },
}


def sha1_matches(data: bytes, expected_hex: str) -> bool:
    return hashlib.sha1(data).hexdigest() == expected_hex


def validate_url(url: str) -> None:
    parsed = urllib.parse.urlparse(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname != "upload.wikimedia.org"
        or parsed.port not in (None, 443)
        or parsed.username is not None
        or parsed.password is not None
    ):
        raise ValueError(f"Unexpected download URL: {url}")


class CommonsRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Reject redirects to any host except the exact Commons upload host."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as response:
        if response.status != 200:
            raise RuntimeError(f"Commons API HTTP {response.status}")
        payload = response.read(2 * 1024 * 1024 + 1)
    if len(payload) > 2 * 1024 * 1024:
        raise ValueError("Commons API response exceeded 2 MiB limit")
    return json.loads(payload)


def fetch_file(title: str) -> dict:
    params = urllib.parse.urlencode({
        "action": "query",
        "format": "json",
        "prop": "imageinfo",
        "iiprop": "url|sha1|size|mime",
        "titles": f"File:{title}",
    })
    data = fetch_json("https://commons.wikimedia.org/w/api.php?" + params)
    pages = data.get("query", {}).get("pages", {})
    page = next(iter(pages.values()), {})
    info = (page.get("imageinfo") or [{}])[0]
    if not info or "missing" in page:
        raise ValueError(f"Commons file not found: {title}")

    url = info.get("url", "")
    validate_url(url)
    size = int(info.get("size", 0))
    expected_sha1 = info.get("sha1", "")
    if info.get("mime") != "image/jpeg" or not expected_sha1:
        raise ValueError(f"Unexpected MIME/SHA-1 metadata for {title}")
    if not 0 < size <= MAX_BYTES:
        raise ValueError(f"Unsafe file size for {title}: {size}")

    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    opener = urllib.request.build_opener(CommonsRedirectHandler())
    with opener.open(req, timeout=60) as response:
        if response.status != 200:
            raise RuntimeError(f"Image HTTP {response.status}")
        validate_url(response.geturl())
        content = response.read(MAX_BYTES + 1)

    if len(content) != size or not sha1_matches(content, expected_sha1):
        raise ValueError(f"Size/SHA-1 verification failed for {title}")
    if not content.startswith(b"\xff\xd8\xff") or not content.endswith(b"\xff\xd9"):
        raise ValueError(f"Invalid JPEG signature: {title}")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / title).write_bytes(content)
    return {
        "file": title,
        "commons_title": f"File:{title}",
        "description_url": f"https://commons.wikimedia.org/wiki/File:{urllib.parse.quote(title)}",
        **PROVENANCE[title],
        "mime": info["mime"],
        "size": size,
        "commons_sha1_hex": expected_sha1,
        "sha256": hashlib.sha256(content).hexdigest(),
        "review_scope": "internal visual/editorial review only; not legal approval",
    }


def main() -> None:
    manifest = {
        "notice": (
            "Review artifact only: not copied to public/, not registered as approved, "
            "and not cleared for publication."
        ),
        "files": [fetch_file(title) for title in FILES],
    }
    (OUT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Fetched and verified {len(manifest['files'])} Commons originals.")


if __name__ == "__main__":
    main()
