#!/usr/bin/env python3
"""Fetch allowlisted Commons originals for internal visual review; never publication."""
from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

OUT = Path("media-review")
MAX_BYTES = 25 * 1024 * 1024
USER_AGENT = (
    "RepresentationPsychologyMediaReview/1.0 "
    "(https://github.com/uralmetal/representation-psychology)"
)
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


def retry_delay(headers, attempt: int) -> int:
    """Honor Retry-After; otherwise use the Wikimedia-recommended backoff."""
    value = headers.get("Retry-After") if headers else None
    if value:
        try:
            return max(0, int(value))
        except ValueError:
            try:
                retry_at = parsedate_to_datetime(value)
                if retry_at.tzinfo is None:
                    retry_at = retry_at.replace(tzinfo=timezone.utc)
                return max(0, int((retry_at - datetime.now(timezone.utc)).total_seconds()))
            except (TypeError, ValueError, OverflowError):
                pass
    return min(60, 5 * (2 ** attempt))


def open_with_retry(opener, request, timeout: int, label: str):
    """Retry only throttling/transient errors and never retry sooner than requested."""
    for attempt in range(4):
        try:
            return opener.open(request, timeout=timeout)
        except urllib.error.HTTPError as error:
            if error.code not in {429, 503} or attempt == 3:
                raise
            delay = retry_delay(error.headers, attempt)
            print(
                f"{label}: HTTP {error.code}; honoring Retry-After/backoff "
                f"for {delay}s before retry {attempt + 1}/3",
                flush=True,
            )
            error.close()
            time.sleep(delay)
    raise RuntimeError(f"{label}: retry loop ended unexpectedly")


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
    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Api-User-Agent": USER_AGENT},
    )
    opener = urllib.request.build_opener()
    with open_with_retry(opener, req, timeout=30, label="Commons API") as response:
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
    with open_with_retry(opener, req, timeout=60, label=title) as response:
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
