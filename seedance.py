#!/usr/bin/env python3
"""Generate videos with Higgsfield's Seedance 2.5 models.

Modes map to model endpoints:
  text       bytedance/seedance-2.5/text-to-video
  image      bytedance/seedance-2.5/image-to-video
  reference  bytedance/seedance-2.5/reference-to-video
  edit       bytedance/seedance-2.5/video-edit
  extend     bytedance/seedance-2.5/video-extend

Requires `pip install higgsfield-client` and HF_KEY="KEY_ID:KEY_SECRET" in the
environment (not needed for --dry-run). Media arguments accept public HTTPS
URLs or local files; local files are uploaded through Higgsfield's presigned
upload URLs.
"""
import argparse
import json
import math
import mimetypes
import os
import sys
import urllib.request

API_BASE = "https://api.higgsfield.ai"
MODEL_PREFIX = "bytedance/seedance-2.5/"

RESOLUTIONS = ("480p", "720p", "1080p")
ASPECT_RATIOS = ("16:9", "4:3", "1:1", "3:4", "9:16", "21:9")
BITRATE_MODES = ("standard", "high")
OUTPUT_FORMATS = ("mp4", "mov")
MIN_DURATION, MAX_DURATION = 4, 30
MAX_IMAGES, MAX_VIDEOS, MAX_AUDIOS = 30, 10, 10

# Content types accepted by POST /files/generate-upload-url.
UPLOAD_CONTENT_TYPES = {
    ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp",
    ".gif": "image/gif", ".wav": "audio/wav", ".mp4": "video/mp4",
}

# Which optional fields each endpoint accepts, and which it requires.
MODES = {
    "text": {"model": "text-to-video", "required": {"prompt"},
             "fields": {"prompt", "duration", "aspect_ratio", "output_format"}},
    "image": {"model": "image-to-video", "required": {"image_url"},
              "fields": {"prompt", "duration", "image_url", "end_image_url"}},
    "reference": {"model": "reference-to-video", "required": set(),
                  "fields": {"prompt", "duration", "aspect_ratio",
                             "image_urls", "video_urls", "audio_urls"}},
    "edit": {"model": "video-edit", "required": {"prompt", "video_url"},
             "fields": {"prompt", "video_url", "image_urls", "video_urls", "audio_urls"}},
    "extend": {"model": "video-extend", "required": {"prompt", "video_url"},
               "fields": {"prompt", "duration", "video_url",
                          "image_urls", "video_urls", "audio_urls"}},
}
COMMON_FIELDS = {"resolution", "bitrate_mode", "generate_audio"}

# 16:9 output dimensions; USD per 1,000 video tokens without and with video input.
DIMENSIONS_16_9 = {"480p": (854, 480), "720p": (1280, 720), "1080p": (1920, 1080)}
PRICE_PER_1K_TOKENS = {"480p": 0.0214, "720p": 0.0214, "1080p": 0.0234}
VIDEO_INPUT_RATE_MULTIPLIER = 0.6


def model_id(mode):
    return MODEL_PREFIX + MODES[mode]["model"]


def build_input(mode, **fields):
    """Validate fields against the endpoint's input schema and return the request body.

    Fields left as None are omitted so the API applies its defaults.
    """
    if mode not in MODES:
        raise ValueError(f"mode must be one of {', '.join(MODES)}")
    spec = MODES[mode]
    body = {k: v for k, v in fields.items() if v is not None and v != []}
    allowed = spec["fields"] | COMMON_FIELDS
    unexpected = sorted(set(body) - allowed)
    if unexpected:
        raise ValueError(f"{mode} mode does not accept: {', '.join(unexpected)}")
    missing = sorted(spec["required"] - set(body))
    if missing:
        raise ValueError(f"{mode} mode requires: {', '.join(missing)}")
    if mode == "reference" and not any(k in body for k in ("image_urls", "video_urls", "audio_urls")):
        raise ValueError("reference mode requires at least one image, video or audio reference")

    if "prompt" in body and not str(body["prompt"]).strip():
        raise ValueError("prompt must be a non-empty string")
    if "duration" in body:
        d = body["duration"]
        if isinstance(d, bool) or not isinstance(d, int) or not MIN_DURATION <= d <= MAX_DURATION:
            raise ValueError(f"duration must be an integer between {MIN_DURATION} and {MAX_DURATION}")
    for name, choices in (("resolution", RESOLUTIONS), ("aspect_ratio", ASPECT_RATIOS),
                          ("bitrate_mode", BITRATE_MODES), ("output_format", OUTPUT_FORMATS)):
        if name in body and body[name] not in choices:
            raise ValueError(f"{name} must be one of {', '.join(choices)}")
    for name, limit in (("image_urls", MAX_IMAGES), ("video_urls", MAX_VIDEOS), ("audio_urls", MAX_AUDIOS)):
        if name in body and len(body[name]) > limit:
            raise ValueError(f"{name} accepts at most {limit} items")
    if "generate_audio" in body:
        body["generate_audio"] = bool(body["generate_audio"])
    return body


def estimate_cost(duration, resolution="720p", input_video_seconds=0, video_input=False):
    """Estimate cost in USD as ceil(w * h * total_seconds * 24 / 1024) tokens.

    Video input (edit, extend, reference with videos) bills its own duration
    too, at 0.6x the token rate. Exact for 16:9 output; other aspect ratios
    use the 16:9 pixel count, so treat their estimate as approximate.
    """
    width, height = DIMENSIONS_16_9[resolution]
    tokens = math.ceil(width * height * (input_video_seconds + duration) * 24 / 1024)
    rate = PRICE_PER_1K_TOKENS[resolution] * (VIDEO_INPUT_RATE_MULTIPLIER if video_input else 1)
    return tokens, tokens / 1000 * rate


def credentials():
    key = os.environ.get("HF_KEY")
    if not key and os.environ.get("HF_API_KEY_ID") and os.environ.get("HF_API_KEY_SECRET"):
        key = f"{os.environ['HF_API_KEY_ID']}:{os.environ['HF_API_KEY_SECRET']}"
    if not key:
        raise RuntimeError('set HF_KEY="KEY_ID:KEY_SECRET"')
    return key


def upload_file(path):
    """Upload a local file via a presigned URL and return its public URL."""
    content_type = UPLOAD_CONTENT_TYPES.get(os.path.splitext(path)[1].lower())
    if not content_type:
        raise ValueError(f"{path}: unsupported file type; use one of {', '.join(UPLOAD_CONTENT_TYPES)}")
    req = urllib.request.Request(
        f"{API_BASE}/files/generate-upload-url",
        data=json.dumps({"content_type": content_type}).encode(),
        headers={"Authorization": f"Key {credentials()}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        upload = json.load(resp)
    with open(path, "rb") as f:
        # The presigned storage URL must not receive Higgsfield credentials.
        put = urllib.request.Request(upload["upload_url"], data=f.read(),
                                     headers=upload.get("upload_headers") or {"Content-Type": content_type},
                                     method="PUT")
    with urllib.request.urlopen(put, timeout=600):
        pass
    return upload["public_url"]


def resolve_media(value, upload=upload_file):
    """Return value unchanged if it is a URL, otherwise upload the local file."""
    if value is None or value.startswith(("https://", "http://")):
        return value
    if not os.path.isfile(value):
        raise ValueError(f"{value}: not a URL or an existing file")
    return upload(value)


def generate(mode, arguments):
    import higgsfield_client  # imported lazily so --dry-run works without the SDK

    return higgsfield_client.subscribe(model_id(mode), arguments=arguments)


def parse_args(argv):
    p = argparse.ArgumentParser(description="Generate a video with Seedance 2.5.")
    sub = p.add_subparsers(dest="mode", required=True)

    def add(mode, help_text):
        sp = sub.add_parser(mode, help=help_text)
        fields = MODES[mode]["fields"]
        prompt_required = "prompt" in MODES[mode]["required"]
        sp.add_argument("prompt", nargs=None if prompt_required else "?")
        if "duration" in fields:
            sp.add_argument("--duration", type=int, help="seconds, 4-30 (default 5)")
        sp.add_argument("--resolution", choices=RESOLUTIONS, help="default 720p")
        if "aspect_ratio" in fields:
            sp.add_argument("--aspect-ratio", choices=ASPECT_RATIOS, help="default 16:9")
        sp.add_argument("--bitrate-mode", choices=BITRATE_MODES, help="default high")
        if "output_format" in fields:
            sp.add_argument("--output-format", choices=OUTPUT_FORMATS, help="default mp4")
        if "image_url" in fields:
            sp.add_argument("--image", required=True, help="start frame (URL or local file)")
            sp.add_argument("--end-image", help="optional end frame (URL or local file)")
        if "video_url" in fields:
            sp.add_argument("--video", required=True, help="source video (URL or local .mp4)")
        if "image_urls" in fields:
            sp.add_argument("--ref-image", action="append", default=[],
                            help=f"reference image, repeatable (max {MAX_IMAGES})")
            sp.add_argument("--ref-video", action="append", default=[],
                            help=f"reference video, repeatable (max {MAX_VIDEOS})")
            sp.add_argument("--ref-audio", action="append", default=[],
                            help=f"reference audio (.wav), repeatable (max {MAX_AUDIOS})")
        if "video_url" in fields or "image_urls" in fields:
            sp.add_argument("--input-video-seconds", type=float, default=0,
                            help="total length of input videos, for the cost estimate")
        sp.add_argument("--no-audio", action="store_true", help="disable audio generation")
        sp.add_argument("--dry-run", action="store_true",
                        help="print the request body and cost estimate without uploading or calling the API")

    add("text", "text to video")
    add("image", "animate a start image (and optional end image)")
    add("reference", "generate from image, video and/or audio references")
    add("edit", "edit an existing video")
    add("extend", "extend an existing video")
    return p, p.parse_args(argv)


def main(argv=None):
    parser, args = parse_args(argv)
    mode = args.mode
    dry = args.dry_run
    media = (lambda v: v) if dry else resolve_media

    try:
        fields = {
            "prompt": args.prompt,
            "duration": getattr(args, "duration", None),
            "resolution": args.resolution,
            "aspect_ratio": getattr(args, "aspect_ratio", None),
            "bitrate_mode": args.bitrate_mode,
            "output_format": getattr(args, "output_format", None),
            "generate_audio": False if args.no_audio else None,
        }
        if hasattr(args, "image"):
            fields["image_url"] = media(args.image)
            fields["end_image_url"] = media(args.end_image)
        if hasattr(args, "video"):
            fields["video_url"] = media(args.video)
        if hasattr(args, "ref_image"):
            fields["image_urls"] = [media(v) for v in args.ref_image]
            fields["video_urls"] = [media(v) for v in args.ref_video]
            fields["audio_urls"] = [media(v) for v in args.ref_audio]
        body = build_input(mode, **fields)
    except ValueError as e:
        parser.error(str(e))

    video_input = bool(body.get("video_url") or body.get("video_urls"))
    input_seconds = getattr(args, "input_video_seconds", 0)
    resolution = body.get("resolution", "720p")
    if mode == "edit":
        # video-edit has no duration parameter; assume output length matches the input.
        duration = input_seconds
    else:
        duration = body.get("duration", 5)
    if video_input and not input_seconds:
        print("Cost estimate skipped: pass --input-video-seconds to include video input.",
              file=sys.stderr)
    else:
        tokens, cost = estimate_cost(duration, resolution, input_seconds, video_input)
        approx = "" if body.get("aspect_ratio", "16:9") == "16:9" and mode != "edit" else " (approximate)"
        print(f"Estimated cost: ${cost:.4f} for {tokens} video tokens{approx}", file=sys.stderr)

    if dry:
        print(json.dumps({"model": model_id(mode), "input": body}, indent=2))
        return 0

    result = generate(mode, body)
    status = result.get("status") if isinstance(result, dict) else None
    if status == "completed":
        print(result["video"]["url"])
        return 0
    print(json.dumps(result, indent=2, default=str), file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
