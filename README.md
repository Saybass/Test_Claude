# Seedance 2.5 client

A small CLI for Higgsfield's [Seedance 2.5 text-to-video](https://console.higgsfield.ai/models/bytedance/seedance-2.5/text-to-video) model (`bytedance/seedance-2.5/text-to-video`).

```bash
pip install higgsfield-client
export HF_KEY="YOUR_KEY_ID:YOUR_KEY_SECRET"

python seedance.py "A cinematic scene at sunset" --duration 8 --resolution 1080p --aspect-ratio 9:16
```

It checks the arguments against the model's input schema, prints a cost estimate to stderr, waits for the result, and prints the video URL.
Use `--dry-run` to see the request body and cost without calling the API (you don't need credentials for that).

| Option | Values | Default |
| --- | --- | --- |
| `--duration` | 4–30 seconds | 5 |
| `--resolution` | 480p, 720p, 1080p | 720p |
| `--aspect-ratio` | 16:9, 4:3, 1:1, 3:4, 9:16, 21:9 | 16:9 |
| `--bitrate-mode` | standard, high | high |
| `--output-format` | mp4, mov | mp4 |
| `--no-audio` | turns off audio generation | audio on |

Cost per second for 16:9: about $0.21 at 480p, $0.46 at 720p and $1.14 at 1080p, before discounts.

Run the tests with `python -m unittest`.
