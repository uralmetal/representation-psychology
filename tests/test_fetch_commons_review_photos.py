import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "fetch_commons_review_photos.py"
SPEC = importlib.util.spec_from_file_location("fetch_commons_review_photos", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class CommonsReviewFetcherTests(unittest.TestCase):
    def test_sha1_base36_round_trip(self):
        import hashlib
        payload = b"representation-psychology"
        encoded = MODULE.sha1_base36(payload)
        alphabet = "0123456789abcdefghijklmnopqrstuvwxyz"
        decoded = 0
        for char in encoded:
            decoded = decoded * 36 + alphabet.index(char)
        self.assertEqual(decoded, int.from_bytes(hashlib.sha1(payload).digest(), "big"))

    def test_accepts_only_upload_wikimedia_https(self):
        MODULE.validate_url("https://upload.wikimedia.org/wikipedia/commons/a/a1/example.jpg")
        for url in (
            "http://upload.wikimedia.org/example.jpg",
            "https://commons.wikimedia.org/example.jpg",
            "https://example.com/example.jpg",
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                MODULE.validate_url(url)


if __name__ == "__main__":
    unittest.main()
