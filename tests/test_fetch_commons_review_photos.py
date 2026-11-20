import importlib.util
import hashlib
import tempfile
import unittest
import urllib.error
from email.message import Message
from pathlib import Path
from unittest.mock import patch

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

    def test_open_with_retry_honors_retry_after_before_next_request(self):
        headers = Message()
        headers["Retry-After"] = "7"
        error = urllib.error.HTTPError(
            "https://upload.wikimedia.org/example.jpg", 429,
            "Too Many Requests", headers, None,
        )

        class Response:
            status = 200

        class Opener:
            calls = 0

            def open(self, request, timeout):
                self.calls += 1
                if self.calls == 1:
                    raise error
                return Response()

        opener = Opener()
        with patch.object(MODULE.time, "sleep") as sleep:
            response = MODULE.open_with_retry(opener, object(), 60, "test-file")

        self.assertEqual(response.status, 200)
        self.assertEqual(opener.calls, 2)
        sleep.assert_called_once_with(7)

    def test_copies_local_png_into_review_artifact_with_checksum(self):
        payload = b"\x89PNG\r\n\x1a\nreview-only"
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "candidate.png"
            source.write_bytes(payload)
            output = root / "artifact"
            with patch.object(MODULE, "OUT", output):
                result = MODULE.copy_local_png_candidate(
                    "candidate.png", "analyze-this-still-02", "analyze-this",
                    "analyze-this-still-02.png", repo_root=root,
                )
            copied = output / result["file"]
            self.assertEqual(copied.read_bytes(), payload)
            self.assertEqual(result["sha256"], hashlib.sha256(payload).hexdigest())
            self.assertEqual(result["registry_status"], "candidate")

    def test_rejects_local_png_path_escape(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            outside = root.parent / "outside.png"
            outside.write_bytes(b"\x89PNG\r\n\x1a\n")
            with self.assertRaises(ValueError):
                MODULE.copy_local_png_candidate(
                    "../outside.png", "test-asset", "analyze-this",
                    "test.png", repo_root=root,
                )
            outside.unlink(missing_ok=True)

    def test_rejects_non_png_local_source(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "bad.png").write_bytes(b"not a PNG")
            with self.assertRaises(ValueError):
                MODULE.copy_local_png_candidate(
                    "bad.png", "test-asset", "analyze-this",
                    "test.png", repo_root=root,
                )


if __name__ == "__main__":
    unittest.main()
