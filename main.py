#!/usr/bin/env python3
"""Generate one Seedance 2.5 video with the official Higgsfield SDK.

Reads HF_KEY ("key-id:key-secret") from the environment or from .env.local.
This makes a billable generation request.
"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load before importing the SDK; variables already set in the environment win.
load_dotenv(Path(__file__).with_name(".env.local"), override=False)

import higgsfield_client  # noqa: E402

MODEL_ID = "bytedance/seedance-2.5/text-to-video"
ARGUMENTS = {
    "prompt": "A cinematic scene at sunset",
    "duration": 5,
    "resolution": "720p",
    "aspect_ratio": "16:9",
}


def main():
    if not os.environ.get("HF_KEY", "").strip():
        print("HF_KEY is not set. Add it to .env.local as HF_KEY=key-id:key-secret.", file=sys.stderr)
        return 2

    try:
        result = higgsfield_client.subscribe(MODEL_ID, arguments=ARGUMENTS)
    except higgsfield_client.CredentialsMissedError as e:
        print(f"Credentials error: {e}", file=sys.stderr)
        return 2
    except higgsfield_client.HiggsfieldClientError as e:
        print(f"Request rejected by the API: {e}", file=sys.stderr)
        return 1

    status = result.get("status")
    request_id = result.get("request_id")
    if status == "completed":
        print(result["video"]["url"])
        return 0
    if status == "nsfw":
        print(f"Request {request_id} was blocked by moderation (nsfw); no video was produced.", file=sys.stderr)
    elif status == "canceled":
        print(f"Request {request_id} was canceled; no video was produced.", file=sys.stderr)
    elif status == "failed":
        print(f"Request {request_id} failed: {result.get('error', 'no error message')}", file=sys.stderr)
    else:
        print(f"Request {request_id} ended with unexpected status {status!r}.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
