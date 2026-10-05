import unittest
from unittest import mock

import seedance


class BuildInputTest(unittest.TestCase):
    def test_defaults(self):
        self.assertEqual(seedance.build_input("A cinematic scene at sunset"), {
            "prompt": "A cinematic scene at sunset", "duration": 5, "resolution": "720p",
            "aspect_ratio": "16:9", "bitrate_mode": "high", "output_format": "mp4",
            "generate_audio": True,
        })

    def test_rejects_invalid_values(self):
        for kwargs in ({"prompt": ""}, {"prompt": "x", "duration": 3},
                       {"prompt": "x", "duration": 31}, {"prompt": "x", "duration": 5.0},
                       {"prompt": "x", "resolution": "4k"}, {"prompt": "x", "aspect_ratio": "2:1"},
                       {"prompt": "x", "bitrate_mode": "low"}, {"prompt": "x", "output_format": "gif"}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                seedance.build_input(**kwargs)


class EstimateCostTest(unittest.TestCase):
    def test_matches_documented_per_second_rates(self):
        for resolution, per_second in (("480p", 0.2056), ("720p", 0.4622), ("1080p", 1.1372)):
            with self.subTest(resolution=resolution):
                _, cost = seedance.estimate_cost(1, resolution)
                self.assertAlmostEqual(cost, per_second, places=4)

    def test_counts_input_video_duration(self):
        tokens, _ = seedance.estimate_cost(5, "720p", input_video_duration=5)
        self.assertEqual(tokens, 1280 * 720 * 10 * 24 // 1024)


class MainTest(unittest.TestCase):
    def test_dry_run_does_not_call_api(self):
        with mock.patch.object(seedance, "generate") as gen, mock.patch("builtins.print"):
            self.assertEqual(seedance.main(["hello", "--dry-run"]), 0)
        gen.assert_not_called()

    def test_prints_video_url_on_success(self):
        result = {"status": "completed", "request_id": "r", "video": {"url": "https://v/x.mp4"}}
        with mock.patch.object(seedance, "generate", return_value=result) as gen, \
                mock.patch("builtins.print") as out:
            self.assertEqual(seedance.main(["hello", "--no-audio", "--duration", "10"]), 0)
        self.assertFalse(gen.call_args.args[0]["generate_audio"])
        out.assert_any_call("https://v/x.mp4")

    def test_nonzero_exit_on_failure(self):
        result = {"status": "failed", "request_id": "r", "error": "boom"}
        with mock.patch.object(seedance, "generate", return_value=result), mock.patch("builtins.print"):
            self.assertEqual(seedance.main(["hello"]), 1)


if __name__ == "__main__":
    unittest.main()
