#!/usr/bin/env python3
"""Generate videos with Higgsfield's Seedance 2.5 text-to-video model.

Requires `pip install higgsfield-client` and HF_KEY="KEY_ID:KEY_SECRET" in the
environment (not needed for --dry-run).
"""
import argparse
import json
import math
import sys

MODEL_ID = "bytedance/seedance-2.5/text-to-video"

RESOLUTIONS = ("480p", "720p", "1080p")
ASPECT_RATIOS = ("16:9", "4:3", "1:1", "3:4", "9:16", "21:9")
BITRATE_MODES = ("standard", "high")
OUTPUT_FORMATS = ("mp4", "mov")
MIN_DURATION, MAX_DURATION = 4, 30

# 16:9 output dimensions and USD price per 1,000 video tokens, per resolution.
DIMENSIONS_16_9 = {"480p": (854, 480), "720p": (1280, 720), "1080p": (1920, 1080)}
PRICE_PER_1K_TOKENS = {"480p": 0.0214, "720p": 0.0214, "1080p": 0.0234}


def build_input(prompt, duration=5, resolution="720p", aspect_ratio="16:9",
                bitrate_mode="high", output_format="mp4", generate_audio=True):
    """Validate arguments against the model's input schema and return the request body."""
    if not prompt or not prompt.strip():
        raise ValueError("prompt must be a non-empty string")
    if isinstance(duration, bool) or not isinstance(duration, int):
        raise ValueError("duration must be an integer")
    if not MIN_DURATION <= duration <= MAX_DURATION:
        raise ValueError(f"duration must be between {MIN_DURATION} and {MAX_DURATION} seconds")
    for name, value, allowed in (
        ("resolution", resolution, RESOLUTIONS),
        ("aspect_ratio", aspect_ratio, ASPECT_RATIOS),
        ("bitrate_mode", bitrate_mode, BITRATE_MODES),
        ("output_format", output_format, OUTPUT_FORMATS),
    ):
        if value not in allowed:
            raise ValueError(f"{name} must be one of {', '.join(allowed)}")
    return {
        "prompt": prompt,
        "duration": duration,
        "resolution": resolution,
        "aspect_ratio": aspect_ratio,
        "bitrate_mode": bitrate_mode,
        "output_format": output_format,
        "generate_audio": bool(generate_audio),
    }


def estimate_cost(duration, resolution="720p", input_video_duration=0):
    """Estimate cost in USD as ceil(w * h * total_seconds * 24 / 1024) tokens.

    Exact for 16:9 output. Other aspect ratios use the 16:9 pixel count, so
    treat their estimate as approximate.
    """
    width, height = DIMENSIONS_16_9[resolution]
    tokens = math.ceil(width * height * (input_video_duration + duration) * 24 / 1024)
    return tokens, tokens / 1000 * PRICE_PER_1K_TOKENS[resolution]


def generate(arguments):
    import higgsfield_client  # imported lazily so --dry-run works without the SDK

    return higgsfield_client.subscribe(MODEL_ID, arguments=arguments)


def main(argv=None):
    p = argparse.ArgumentParser(description="Generate a video with Seedance 2.5.")
    p.add_argument("prompt")
    p.add_argument("--duration", type=int, default=5, help="seconds, 4-30 (default 5)")
    p.add_argument("--resolution", choices=RESOLUTIONS, default="720p")
    p.add_argument("--aspect-ratio", choices=ASPECT_RATIOS, default="16:9")
    p.add_argument("--bitrate-mode", choices=BITRATE_MODES, default="high")
    p.add_argument("--output-format", choices=OUTPUT_FORMATS, default="mp4")
    p.add_argument("--no-audio", action="store_true", help="disable audio generation")
    p.add_argument("--dry-run", action="store_true",
                   help="print the request body and cost estimate without calling the API")
    args = p.parse_args(argv)

    try:
        body = build_input(args.prompt, args.duration, args.resolution, args.aspect_ratio,
                           args.bitrate_mode, args.output_format, not args.no_audio)
    except ValueError as e:
        p.error(str(e))

    tokens, cost = estimate_cost(body["duration"], body["resolution"])
    approx = "" if body["aspect_ratio"] == "16:9" else " (approximate for non-16:9)"
    print(f"Estimated cost: ${cost:.4f} for {tokens} video tokens{approx}", file=sys.stderr)

    if args.dry_run:
        print(json.dumps(body, indent=2))
        return 0

    result = generate(body)
    status = result.get("status") if isinstance(result, dict) else None
    if status == "completed":
        print(result["video"]["url"])
        return 0
    print(json.dumps(result, indent=2, default=str), file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
