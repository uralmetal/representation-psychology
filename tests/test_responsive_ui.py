"""Static UI contract tests for responsive and accessible controls."""
from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ResponsiveCatalogTests(unittest.TestCase):
    def test_comparison_table_is_exempt_from_mobile_catalog_table_hiding(self) -> None:
        source = (ROOT / "src" / "islands" / "Catalog.svelte").read_text(encoding="utf-8")
        self.assertIn(
            'class="catalog-table-wrap catalog-table--compare-wrap"',
            source,
            "the comparison table wrapper must opt out of the mobile rule that hides the wide catalog table",
        )
        self.assertIn(
            ".catalog-table-wrap:not(.catalog-table--compare-wrap) { display: none; }",
            source,
            "only the wide catalog table should be hidden on narrow screens",
        )

    def test_global_keyboard_and_motion_preferences_remain_supported(self) -> None:
        styles = (ROOT / "src" / "styles" / "global.css").read_text(encoding="utf-8")
        layout = (ROOT / "src" / "components" / "Layout.astro").read_text(encoding="utf-8")
        self.assertIn(":focus-visible", styles)
        self.assertIn("@media (prefers-reduced-motion: reduce)", styles)
        self.assertIn('class="skip-link" href="#main"', layout)
        self.assertIn('aria-expanded="false"', layout)
        self.assertIn("toggle.setAttribute('aria-expanded'", layout)


if __name__ == "__main__":
    unittest.main()
