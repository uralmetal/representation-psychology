"""Regression tests for story evidence-card coverage.

Run with: python3 -m unittest discover -s tests -v
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
CHAPTERS = ROOT / "src" / "content" / "chapters"
SCENES = ROOT / "public" / "data" / "scenes.json"


class ChapterEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        payload = json.loads(SCENES.read_text(encoding="utf-8"))
        cls.scene_ids = {scene["id"] for scene in payload.get("scenes", [])}

    def test_every_chapter_scene_link_has_an_evidence_card(self) -> None:
        for path in sorted(CHAPTERS.glob("*.md")):
            raw = path.read_text(encoding="utf-8")
            match = re.match(r"^---\\s*\\n(.*?)\\n---\\s*\\n(.*)$", raw, re.DOTALL)
            self.assertIsNotNone(match, f"{path.name}: missing YAML frontmatter")
            assert match is not None
            metadata = yaml.safe_load(match.group(1)) or {}
            body = match.group(2)
            linked_ids = set(re.findall(r"\\]\\(scene:([a-z0-9-]+)\\)", body))
            evidence_ids = set(metadata.get("scene_ids") or [])

            with self.subTest(chapter=path.name):
                self.assertTrue(
                    linked_ids.issubset(evidence_ids),
                    f"scene links missing from scene_ids: {sorted(linked_ids - evidence_ids)}",
                )

    def test_chapter_evidence_ids_exist_in_published_dataset(self) -> None:
        for path in sorted(CHAPTERS.glob("*.md")):
            raw = path.read_text(encoding="utf-8")
            match = re.match(r"^---\\s*\\n(.*?)\\n---\\s*\\n", raw, re.DOTALL)
            self.assertIsNotNone(match, f"{path.name}: missing YAML frontmatter")
            assert match is not None
            metadata = yaml.safe_load(match.group(1)) or {}
            evidence_ids = set(metadata.get("scene_ids") or [])

            with self.subTest(chapter=path.name):
                self.assertTrue(
                    evidence_ids.issubset(self.scene_ids),
                    f"unknown scene_ids: {sorted(evidence_ids - self.scene_ids)}",
                )


if __name__ == "__main__":
    unittest.main()
