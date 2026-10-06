import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

import seedance


def run(argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = seedance.main(argv)
    return code, out.getvalue(), err.getvalue()


class BuildInputTest(unittest.TestCase):
    def test_text_omits_unset_fields(self):
        self.assertEqual(seedance.build_input("text", prompt="sunset", duration=None),
                         {"prompt": "sunset"})

    def test_required_fields_per_mode(self):
        for mode, fields in (("text", {}), ("image", {"prompt": "x"}),
                             ("edit", {"prompt": "x"}), ("extend", {"video_url": "https://v"}),
                             ("reference", {"prompt": "x"})):
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                seedance.build_input(mode, **fields)

    def test_rejects_fields_endpoint_does_not_accept(self):
        with self.assertRaisesRegex(ValueError, "aspect_ratio"):
            seedance.build_input("image", image_url="https://i", aspect_ratio="16:9")
        with self.assertRaisesRegex(ValueError, "duration"):
            seedance.build_input("edit", prompt="x", video_url="https://v", duration=5)

    def test_rejects_invalid_values(self):
        for fields in ({"prompt": ""}, {"prompt": "x", "duration": 3}, {"prompt": "x", "duration": 31},
                       {"prompt": "x", "duration": 5.0}, {"prompt": "x", "resolution": "4k"},
                       {"prompt": "x", "aspect_ratio": "2:1"}, {"prompt": "x", "bitrate_mode": "low"},
                       {"prompt": "x", "output_format": "gif"}):
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                seedance.build_input("text", **fields)

    def test_reference_list_limits(self):
        seedance.build_input("reference", audio_urls=["https://a"] * 10)
        with self.assertRaises(ValueError):
            seedance.build_input("reference", video_urls=["https://v"] * 11)


class EstimateCostTest(unittest.TestCase):
    def test_matches_documented_per_second_rates(self):
        for resolution, per_second, with_video in (("480p", 0.2056, 0.1234), ("720p", 0.4622, 0.2773),
                                                   ("1080p", 1.1372, 0.6823)):
            with self.subTest(resolution=resolution):
                self.assertAlmostEqual(seedance.estimate_cost(1, resolution)[1], per_second, places=4)
                self.assertAlmostEqual(seedance.estimate_cost(1, resolution, video_input=True)[1],
                                       with_video, places=4)

    def test_counts_input_video_duration(self):
        tokens, _ = seedance.estimate_cost(5, "720p", input_video_seconds=5)
        self.assertEqual(tokens, 1280 * 720 * 10 * 24 // 1024)

    def test_applies_account_discount(self):
        # 5 s at 480p was billed $0.87 on an account with 15% off list price.
        _, cost = seedance.estimate_cost(5, "480p", discount=15)
        self.assertAlmostEqual(cost, 0.874, places=3)


class ResolveMediaTest(unittest.TestCase):
    def test_urls_pass_through(self):
        upload = mock.Mock()
        self.assertEqual(seedance.resolve_media("https://x/a.png", upload), "https://x/a.png")
        upload.assert_not_called()

    def test_local_file_is_uploaded(self):
        with tempfile.NamedTemporaryFile(suffix=".png") as f:
            upload = mock.Mock(return_value="https://cdn/a.png")
            self.assertEqual(seedance.resolve_media(f.name, upload), "https://cdn/a.png")
            upload.assert_called_once_with(f.name)

    def test_missing_file_is_an_error(self):
        with self.assertRaises(ValueError):
            seedance.resolve_media("/nope/missing.png", mock.Mock())

    def test_upload_rejects_unsupported_type(self):
        with self.assertRaisesRegex(ValueError, "unsupported"):
            seedance.upload_file("clip.mov")


class UploadFileTest(unittest.TestCase):
    def test_requests_presigned_url_then_puts_file_without_credentials(self):
        upload = {"public_url": "https://cdn/x.jpg", "upload_url": "https://s3/put",
                  "upload_headers": {"Content-Type": "image/jpeg", "x-amz-tagging": "retention=temporary"}}
        calls = []

        def fake_urlopen(req, timeout):
            calls.append(req)
            resp = mock.MagicMock()
            resp.__enter__.return_value = io.BytesIO(json.dumps(upload).encode())
            return resp

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(b"img")
        try:
            with mock.patch.dict(os.environ, {"HF_KEY": "id:secret"}), \
                    mock.patch("urllib.request.urlopen", fake_urlopen):
                self.assertEqual(seedance.upload_file(f.name), "https://cdn/x.jpg")
        finally:
            os.unlink(f.name)
        post, put = calls
        self.assertEqual(post.full_url, "https://api.higgsfield.ai/files/generate-upload-url")
        self.assertEqual(post.get_header("Authorization"), "Key id:secret")
        self.assertEqual(json.loads(post.data), {"content_type": "image/jpeg"})
        self.assertEqual((put.full_url, put.get_method(), put.data), ("https://s3/put", "PUT", b"img"))
        self.assertIsNone(put.get_header("Authorization"))
        self.assertEqual(put.get_header("X-amz-tagging"), "retention=temporary")


class MainTest(unittest.TestCase):
    def test_dry_run_does_not_upload_or_call_api(self):
        with mock.patch.object(seedance, "generate") as gen, \
                mock.patch.object(seedance, "upload_file") as up:
            code, out, _ = run(["image", "--image", "start.png", "--dry-run"])
        self.assertEqual(code, 0)
        gen.assert_not_called()
        up.assert_not_called()
        self.assertEqual(json.loads(out), {"model": "bytedance/seedance-2.5/image-to-video",
                                           "input": {"image_url": "start.png"}})

    def test_reference_mode_builds_lists(self):
        code, out, _ = run(["reference", "two cats", "--ref-image", "https://a", "--ref-image",
                            "https://b", "--ref-audio", "https://c.wav", "--dry-run"])
        self.assertEqual(code, 0)
        body = json.loads(out)["input"]
        self.assertEqual(body["image_urls"], ["https://a", "https://b"])
        self.assertEqual(body["audio_urls"], ["https://c.wav"])
        self.assertNotIn("video_urls", body)

    def test_cost_estimate_uses_video_input_rate(self):
        _, _, err = run(["extend", "keep going", "--video", "https://v.mp4", "--duration", "5",
                         "--input-video-seconds", "5", "--dry-run"])
        tokens, cost = seedance.estimate_cost(5, "720p", 5, video_input=True)
        self.assertIn(f"${cost:.4f} for {tokens}", err)

    def test_cost_estimate_skipped_without_input_seconds(self):
        _, _, err = run(["edit", "make it night", "--video", "https://v.mp4", "--dry-run"])
        self.assertIn("skipped", err)

    def test_prints_video_url_on_success(self):
        result = {"status": "completed", "request_id": "r", "video": {"url": "https://v/x.mp4"}}
        with mock.patch.object(seedance, "generate", return_value=result) as gen:
            code, out, _ = run(["text", "hello", "--no-audio", "--duration", "10"])
        self.assertEqual(code, 0)
        self.assertEqual(gen.call_args.args, ("text", {"prompt": "hello", "duration": 10,
                                                       "generate_audio": False}))
        self.assertEqual(out.strip(), "https://v/x.mp4")

    def test_nonzero_exit_on_failure(self):
        for status in ("failed", "nsfw", "canceled"):
            with self.subTest(status=status), \
                    mock.patch.object(seedance, "generate", return_value={"status": status, "request_id": "r"}):
                self.assertEqual(run(["text", "hello"])[0], 1)


if __name__ == "__main__":
    unittest.main()
