"""Regression tests for the media publication gate.

Run with: python3 -m unittest discover -s tests -v
Only the Python standard library and project runtime dependencies are required.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import yaml


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_media.py"
SPEC = importlib.util.spec_from_file_location("validate_media", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


class MediaValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.manifest = self.root / "data" / "media-assets.yml"
        self.public_data = self.root / "public" / "data"
        self.chapters_dir = self.root / "src" / "content" / "chapters"
        self.public_media = self.root / "public" / "media"
        self.manifest.parent.mkdir(parents=True)
        self.public_data.mkdir(parents=True)
        self.chapters_dir.mkdir(parents=True)
        self.chapters_dir.joinpath("01-space.md").write_text("---\nanchor: space\n---\n", encoding="utf-8")
        self.public_data.joinpath("works.json").write_text(
            json.dumps({"works": [{"id": "demo-work"}]}), encoding="utf-8"
        )
        self.public_data.joinpath("scenes.json").write_text(
            json.dumps({"scenes": [{"id": "demo-scene", "work_id": "demo-work", "analysis_unit": "scene"}]}),
            encoding="utf-8",
        )
        self.patches = (
            patch.object(validator, "ROOT", self.root),
            patch.object(validator, "MANIFEST", self.manifest),
            patch.object(validator, "PUBLIC_DATA", self.public_data),
            patch.object(validator, "PUBLIC_MEDIA", self.public_media),
            patch.object(validator, "CHAPTERS_DIR", self.chapters_dir),
        )
        for item in self.patches:
            item.start()
        self.addCleanup(self._stop_patches)

    def _stop_patches(self) -> None:
        for item in reversed(self.patches):
            item.stop()
        self.temp.cleanup()

    def base_asset(self, **overrides: object) -> dict:
        asset = {
            "id": "demo-photo",
            "kind": "photograph",
            "status": "candidate",
            "work_id": "demo-work",
            "scene_id": None,
            "source_file": None,
            "public_path": None,
            "source_url": None,
            "creator_or_rightsholder": None,
            "license": None,
            "license_url": None,
            "analysis_purpose": None,
            "alt": None,
            "caption": None,
            "attribution": None,
            "legal_basis": None,
            "legal_review": {
                "status": "not_reviewed",
                "reference": None,
                "reviewer": None,
                "reviewed_at": None,
            },
        }
        asset.update(overrides)
        return asset

    def write_manifest(self, *assets: dict) -> None:
        self.manifest.write_text(
            yaml.safe_dump({"version": 1, "assets": list(assets)}, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

    def approved_photo(self, **overrides: object) -> dict:
        asset = self.base_asset(
            status="approved",
            source_url="https://commons.wikimedia.org/wiki/File:Example.jpg",
            creator_or_rightsholder="Example Photographer",
            license="CC BY-SA 4.0",
            license_url="https://creativecommons.org/licenses/by-sa/4.0/",
            analysis_purpose="Documentary context for the analysis.",
            alt="A documentary photograph.",
            caption="Documentary photograph, dated 2010.",
            attribution="Photo: Example Photographer, CC BY-SA 4.0.",
            legal_basis="Re-use under the photographer's CC BY-SA 4.0 license.",
            public_path="/media/example.jpg",
            legal_review={
                "status": "approved",
                "reference": "https://commons.wikimedia.org/wiki/File:Example.jpg",
                "reviewer": "Rights checklist reviewer (license and source verified)",
                "reviewed_at": "2026-11-20",
            },
        )
        asset.update(overrides)
        return asset

    def test_candidate_manifest_passes_without_public_images(self) -> None:
        self.write_manifest(self.base_asset())
        validator.main()

    def test_unregistered_public_image_blocks_build(self) -> None:
        self.write_manifest(self.base_asset())
        self.public_media.mkdir(parents=True)
        (self.public_media / "unregistered.jpg").write_bytes(b"not-a-real-image")
        with self.assertRaises(SystemExit):
            validator.main()

    def test_duplicate_asset_ids_block_build(self) -> None:
        self.write_manifest(self.base_asset(), self.base_asset())
        with self.assertRaises(SystemExit):
            validator.main()

    def test_unknown_chapter_anchor_blocks_build(self) -> None:
        self.write_manifest(self.base_asset(chapter_anchor="missing-chapter"))
        with self.assertRaises(SystemExit):
            validator.main()

    def test_valid_chapter_anchor_is_accepted(self) -> None:
        self.write_manifest(self.base_asset(chapter_anchor="space"))
        validator.main()

    def test_non_https_source_blocks_build(self) -> None:
        self.write_manifest(self.base_asset(source_url="http://example.org/image.jpg"))
        with self.assertRaises(SystemExit):
            validator.main()

    def test_sourced_photograph_requires_creator_and_license(self) -> None:
        self.write_manifest(self.base_asset(source_url="https://example.org/image.jpg"))
        with self.assertRaises(SystemExit):
            validator.main()

    def test_approved_photo_requires_existing_public_file_and_review(self) -> None:
        asset = self.approved_photo()
        self.write_manifest(asset)
        with self.assertRaises(SystemExit):
            validator.main()

        self.public_media.mkdir(parents=True)
        (self.public_media / "example.jpg").write_bytes(b"test fixture")
        validator.main()

    def test_approved_photo_rejects_duplicate_public_path(self) -> None:
        self.public_media.mkdir(parents=True)
        (self.public_media / "example.jpg").write_bytes(b"test fixture")
        first = self.approved_photo()
        second = self.approved_photo(id="another-id")
        self.write_manifest(first, second)
        with self.assertRaises(SystemExit):
            validator.main()

    def test_approved_photo_rejects_invalid_review_date(self) -> None:
        self.public_media.mkdir(parents=True)
        (self.public_media / "example.jpg").write_bytes(b"test fixture")
        asset = self.approved_photo(
            legal_review={
                "status": "approved",
                "reference": "https://commons.wikimedia.org/wiki/File:Example.jpg",
                "reviewer": "Reviewer",
                "reviewed_at": "yesterday",
            }
        )
        self.write_manifest(asset)
        with self.assertRaises(SystemExit):
            validator.main()

    def test_film_still_requires_verified_exact_scene_reference(self) -> None:
        self.public_media.mkdir(parents=True)
        (self.public_media / "frame.jpg").write_bytes(b"test fixture")
        asset = self.approved_photo(
            id="demo-frame",
            kind="film_still",
            scene_id="demo-scene",
            analysis_unit="scene",
            screen_time_reference="S1E1 00:12:34",
            screen_time_verified=False,
            public_path="/media/frame.jpg",
        )
        self.write_manifest(asset)
        with self.assertRaises(SystemExit):
            validator.main()

    def test_film_still_requires_explicit_unit_and_scene_link(self) -> None:
        self.public_media.mkdir(parents=True)
        (self.public_media / "frame.jpg").write_bytes(b"test fixture")
        asset = self.approved_photo(
            id="demo-frame",
            kind="film_still",
            scene_id=None,
            analysis_unit="scene",
            screen_time_reference="S1E1 00:12:34",
            screen_time_verified=True,
            public_path="/media/frame.jpg",
        )
        self.write_manifest(asset)
        with self.assertRaises(SystemExit):
            validator.main()

    def test_work_overall_film_still_can_be_approved_without_fabricated_scene(self) -> None:
        self.public_media.mkdir(parents=True)
        (self.public_media / "frame.jpg").write_bytes(b"test fixture")
        asset = self.approved_photo(
            id="demo-frame",
            kind="film_still",
            scene_id=None,
            analysis_unit="work_overall",
            screen_time_reference="S1E1 00:12:34",
            screen_time_verified=True,
            public_path="/media/frame.jpg",
        )
        self.write_manifest(asset)
        validator.main()


if __name__ == "__main__":
    unittest.main()
