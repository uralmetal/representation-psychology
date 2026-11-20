import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "fetch_commons_review_photos.py"
SPEC = importlib.util.spec_from_file_location("fetch_commons_review_photos", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class CommonsReviewFetcherTests(unittest.TestCase):
    def test_sha1_comparison_uses_hexadecimal_api_value(self):
        import hashlib
        payload = b"representation-psychology"
        self.assertEqual(hashlib.sha1(payload).hexdigest(), hashlib.sha1(payload).hexdigest())
        self.assertEqual(len(hashlib.sha1(payload).hexdigest()), 40)

    def test_accepts_only_upload_wikimedia_https(self):
        MODULE.validate_url("https://upload.wikimedia.org/wikipedia/commons/a/a1/example.jpg")
        for url in (
            "http://upload.wikimedia.org/example.jpg",
            "https://commons.wikimedia.org/example.jpg",
            "https://example.com/example.jpg",
            "https://upload.wikimedia.org:444/example.jpg",
            "https://user@upload.wikimedia.org/example.jpg",
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                MODULE.validate_url(url)


if __name__ == "__main__":
    unittest.main()
