import importlib.util
import hashlib
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "fetch_commons_review_photos.py"
SPEC = importlib.util.spec_from_file_location("fetch_commons_review_photos", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class CommonsReviewFetcherTests(unittest.TestCase):
    def test_sha1_comparison_uses_hexadecimal_api_value(self):
        payload = b"representation-psychology"
        expected = "548d72783ae1e4f1275bd8e54d0abaebd077b89b"
        self.assertEqual(hashlib.sha1(payload).hexdigest(), expected)
        self.assertTrue(MODULE.sha1_matches(payload, expected))
        self.assertFalse(MODULE.sha1_matches(payload, "0" * 40))

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

    def test_retry_after_seconds_are_respected(self):
        self.assertEqual(MODULE.retry_delay({"Retry-After": "27"}, 0), 27)

    def test_fallback_backoff_is_exponential_and_capped(self):
        self.assertEqual(MODULE.retry_delay({}, 0), 5)
        self.assertEqual(MODULE.retry_delay({}, 1), 10)
        self.assertEqual(MODULE.retry_delay({}, 8), 60)


if __name__ == "__main__":
    unittest.main()
