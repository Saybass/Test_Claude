import io
import os
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

import higgsfield_client

import main


def run(result=None, side_effect=None, key="id:secret"):
    out, err = io.StringIO(), io.StringIO()
    with mock.patch.dict(os.environ, {"HF_KEY": key}), \
            mock.patch.object(higgsfield_client, "subscribe", return_value=result,
                              side_effect=side_effect) as sub, \
            redirect_stdout(out), redirect_stderr(err):
        code = main.main()
    return code, out.getvalue(), err.getvalue(), sub


class MainTest(unittest.TestCase):
    def test_completed_prints_url(self):
        code, out, _, sub = run({"status": "completed", "request_id": "r", "video": {"url": "https://v/x.mp4"}})
        self.assertEqual((code, out.strip()), (0, "https://v/x.mp4"))
        sub.assert_called_once_with("bytedance/seedance-2.5/text-to-video", arguments={
            "prompt": "A cinematic scene at sunset", "duration": 5,
            "resolution": "720p", "aspect_ratio": "16:9"})

    def test_terminal_failures_do_not_report_success(self):
        for status in ("failed", "nsfw", "canceled", "weird"):
            with self.subTest(status=status):
                code, out, err, _ = run({"status": status, "request_id": "r", "error": "boom"})
                self.assertEqual((code, out), (1, ""))
                self.assertIn("r", err)

    def test_api_error(self):
        code, out, err, _ = run(side_effect=higgsfield_client.HiggsfieldClientError("Invalid credentials"))
        self.assertEqual((code, out), (1, ""))
        self.assertIn("Invalid credentials", err)

    def test_missing_key_makes_no_request(self):
        code, _, _, sub = run(key="")
        self.assertEqual(code, 2)
        sub.assert_not_called()


if __name__ == "__main__":
    unittest.main()
