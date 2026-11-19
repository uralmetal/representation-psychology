#!/usr/bin/env python3
"""Fail the build if media publication metadata or approval gates are incomplete."""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "media-assets.yml"
PUBLIC_MEDIA = ROOT / "public" / "media"
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

        if asset.get("kind") not in ALLOWED_KINDS:
            errors.append(f"{prefix} ({asset_id}): invalid kind")
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

        public_path = asset.get("public_path")
        if status == "approved":
            for field in APPROVED_FIELDS:
                value = asset.get(field)
                if not isinstance(value, str) or not value.strip():
                    errors.append(f"{prefix} ({asset_id}): approved asset requires {field}")

            legal_review = asset.get("legal_review") or {}
            for field in ("reference", "reviewer", "reviewed_at"):
                value = legal_review.get(field)
                if not isinstance(value, str) or not value.strip():
                    errors.append(f"{prefix} ({asset_id}): approved asset requires legal_review.{field}")
            if legal_review.get("status") != "approved":
                errors.append(f"{prefix} ({asset_id}): legal_review.status must be 'approved'")

            if not isinstance(public_path, str) or not public_path.startswith("/media/"):
                errors.append(f"{prefix} ({asset_id}): approved asset public_path must start with /media/")
            else:
                relative = public_path.lstrip("/")
                target = (ROOT / "public" / relative).resolve()
                if not inside(target, PUBLIC_MEDIA):
                    errors.append(f"{prefix} ({asset_id}): public_path escapes public/media")
                elif not target.is_file():
                    errors.append(f"{prefix} ({asset_id}): approved public file does not exist: {public_path}")
                approved_paths.add(public_path)
            if not isinstance(asset.get("work_id"), str) or not asset["work_id"].strip():
                errors.append(f"{prefix} ({asset_id}): approved asset requires work_id")
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
