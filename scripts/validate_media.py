#!/usr/bin/env python3
"""Fail the build if media publication metadata or approval gates are incomplete."""

from __future__ import annotations

import json
from pathlib import Path
from datetime import date
import sys
from typing import Any
from urllib.parse import urlparse

import yaml

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "media-assets.yml"
PUBLIC_MEDIA = ROOT / "public" / "media"
PUBLIC_DATA = ROOT / "public" / "data"
ALLOWED_STATUSES = {"candidate", "pending_review", "approved", "rejected"}
ALLOWED_KINDS = {"film_still", "photograph"}
APPROVED_FIELDS = (
    "source_url",
    "creator_or_rightsholder",
    "analysis_purpose",
    "alt",
    "caption",
    "attribution",
    "legal_basis",
)


def fail(errors: list[str]) -> None:
    for error in errors:
        print(f"MEDIA ERROR: {error}", file=sys.stderr)
    raise SystemExit(1)


def inside(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        fail([f"required generated data not found: {path.relative_to(ROOT)}; run npm run data first"])
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    if not MANIFEST.exists():
        fail([f"manifest not found: {MANIFEST.relative_to(ROOT)}"])

    data: dict[str, Any] = yaml.safe_load(MANIFEST.read_text(encoding="utf-8")) or {}
    assets = data.get("assets", [])
    errors: list[str] = []
    ids: set[str] = set()
    approved_paths: set[str] = set()

    if not isinstance(assets, list):
        fail(["assets must be a YAML list"])

    works = load_json(PUBLIC_DATA / "works.json").get("works", [])
    scenes = load_json(PUBLIC_DATA / "scenes.json").get("scenes", [])
    work_ids = {w.get("id") for w in works}
    scene_by_id = {s.get("id"): s for s in scenes}

    for index, asset in enumerate(assets, start=1):
        prefix = f"assets[{index}]"
        if not isinstance(asset, dict):
            errors.append(f"{prefix} must be an object")
            continue

        asset_id = asset.get("id")
        if not asset_id or not isinstance(asset_id, str):
            errors.append(f"{prefix}: missing id")
        elif asset_id in ids:
            errors.append(f"{prefix}: duplicate id {asset_id}")
        else:
            ids.add(asset_id)

        kind = asset.get("kind")
        if kind not in ALLOWED_KINDS:
            errors.append(f"{prefix} ({asset_id}): invalid kind {kind!r}")
        status = asset.get("status")
        if status not in ALLOWED_STATUSES:
            errors.append(f"{prefix} ({asset_id}): invalid status {status!r}")

        source_file = asset.get("source_file")
        if source_file:
            candidate_path = (ROOT / source_file).resolve()
            if not inside(candidate_path, ROOT):
                errors.append(f"{prefix} ({asset_id}): source_file escapes repository")
            elif not candidate_path.is_file():
                errors.append(f"{prefix} ({asset_id}): source_file does not exist: {source_file}")

        work_id = asset.get("work_id")
        if work_id is not None and work_id not in work_ids:
            errors.append(f"{prefix} ({asset_id}): unknown work_id {work_id!r}")

        scene_id = asset.get("scene_id")
        if scene_id is not None:
            scene = scene_by_id.get(scene_id)
            if scene is None:
                errors.append(f"{prefix} ({asset_id}): unknown scene_id {scene_id!r}")
            elif work_id and scene.get("work_id") != work_id:
                errors.append(f"{prefix} ({asset_id}): scene_id does not belong to work_id")

        analysis_unit = asset.get("analysis_unit")
        if analysis_unit is not None and analysis_unit not in {"scene", "work_overall"}:
            errors.append(f"{prefix} ({asset_id}): invalid analysis_unit {analysis_unit!r}")

        public_path = asset.get("public_path")
        source_url = asset.get("source_url")
        if source_url is not None:
            parsed_source_url = urlparse(source_url) if isinstance(source_url, str) else None
            if not parsed_source_url or parsed_source_url.scheme != "https" or not parsed_source_url.netloc:
                errors.append(f"{prefix} ({asset_id}): source_url must be an absolute HTTPS URL")

        if kind == "photograph" and source_url:
            for field in ("creator_or_rightsholder", "license", "license_url"):
                value = asset.get(field)
                if not isinstance(value, str) or not value.strip():
                    errors.append(f"{prefix} ({asset_id}): sourced photograph requires {field}")
            license_url = asset.get("license_url")
            parsed_license_url = urlparse(license_url) if isinstance(license_url, str) else None
            if not parsed_license_url or parsed_license_url.scheme != "https" or not parsed_license_url.netloc:
                errors.append(f"{prefix} ({asset_id}): license_url must be an absolute HTTPS URL")

        if status == "approved":
            for field in APPROVED_FIELDS:
                value = asset.get(field)
                if not isinstance(value, str) or not value.strip():
                    errors.append(f"{prefix} ({asset_id}): approved asset requires {field}")

            if kind == "photograph":
                for field in ("license", "license_url"):
                    value = asset.get(field)
                    if not isinstance(value, str) or not value.strip():
                        errors.append(f"{prefix} ({asset_id}): approved photograph requires {field}")

            legal_review = asset.get("legal_review")
            if not isinstance(legal_review, dict):
                errors.append(f"{prefix} ({asset_id}): approved asset requires legal_review object")
                legal_review = {}
            for field in ("reference", "reviewer", "reviewed_at"):
                value = legal_review.get(field)
                if not isinstance(value, str) or not value.strip():
                    errors.append(f"{prefix} ({asset_id}): approved asset requires legal_review.{field}")
            if legal_review.get("status") != "approved":
                errors.append(f"{prefix} ({asset_id}): legal_review.status must be 'approved'")
            reviewed_at = legal_review.get("reviewed_at")
            if isinstance(reviewed_at, str) and reviewed_at.strip():
                try:
                    date.fromisoformat(reviewed_at[:10])
                except ValueError:
                    errors.append(f"{prefix} ({asset_id}): legal_review.reviewed_at must start with an ISO date (YYYY-MM-DD)")

            if not isinstance(public_path, str) or not public_path.startswith("/media/"):
                errors.append(f"{prefix} ({asset_id}): approved asset public_path must start with /media/")
            else:
                if public_path in approved_paths:
                    errors.append(f"{prefix} ({asset_id}): public_path is already assigned to another asset: {public_path}")
                relative = public_path.lstrip("/")
                target = (ROOT / "public" / relative).resolve()
                if not inside(target, PUBLIC_MEDIA):
                    errors.append(f"{prefix} ({asset_id}): public_path escapes public/media")
                elif not target.is_file():
                    errors.append(f"{prefix} ({asset_id}): approved public file does not exist: {public_path}")
                elif target.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp", ".avif"}:
                    errors.append(f"{prefix} ({asset_id}): public_path must use a supported image extension")
                approved_paths.add(public_path)

            if not isinstance(work_id, str) or work_id not in work_ids:
                errors.append(f"{prefix} ({asset_id}): approved asset requires a valid work_id")
            if kind == "film_still":
                if not asset.get("screen_time_reference"):
                    errors.append(f"{prefix} ({asset_id}): film_still requires an exact episode/timecode reference")
                if asset.get("screen_time_verified") is not True:
                    errors.append(f"{prefix} ({asset_id}): film_still requires screen_time_verified: true")
                if analysis_unit == "scene":
                    if not scene_id:
                        errors.append(f"{prefix} ({asset_id}): analysis_unit='scene' requires scene_id")
                    elif scene_by_id.get(scene_id, {}).get("analysis_unit") != "scene":
                        errors.append(f"{prefix} ({asset_id}): film_still scene_id must reference a scene analysis unit")
                elif analysis_unit == "work_overall":
                    if scene_id:
                        errors.append(f"{prefix} ({asset_id}): work_overall film_still must not set scene_id")
                else:
                    errors.append(f"{prefix} ({asset_id}): film_still requires explicit analysis_unit='scene' or 'work_overall'")
        elif public_path:
            errors.append(f"{prefix} ({asset_id}): non-approved asset must not have public_path")

    if PUBLIC_MEDIA.exists():
        for file_path in PUBLIC_MEDIA.rglob("*"):
            if file_path.is_file():
                public_path = "/" + file_path.relative_to(ROOT / "public").as_posix()
                if public_path not in approved_paths:
                    errors.append(f"unregistered or unapproved public media file: {public_path}")

    if errors:
        fail(errors)

    pending = sum(1 for a in assets if a.get("status") in {"candidate", "pending_review"})
    approved = sum(1 for a in assets if a.get("status") == "approved")
    print(f"Media validation OK: {len(assets)} assets, {approved} approved, {pending} awaiting review.")


if __name__ == "__main__":
    main()
