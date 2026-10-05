# Seedance 2.5 client

A small CLI for Higgsfield's Seedance 2.5 video models. Each mode calls one endpoint:

| Mode | Endpoint | Required inputs |
| --- | --- | --- |
| `text` | `bytedance/seedance-2.5/text-to-video` | prompt |
| `image` | `bytedance/seedance-2.5/image-to-video` | `--image` (start frame), optional `--end-image` |
| `reference` | `bytedance/seedance-2.5/reference-to-video` | at least one `--ref-image`, `--ref-video` or `--ref-audio` |
| `edit` | `bytedance/seedance-2.5/video-edit` | prompt, `--video` |
| `extend` | `bytedance/seedance-2.5/video-extend` | prompt, `--video` |

```bash
pip install higgsfield-client
export HF_KEY="YOUR_KEY_ID:YOUR_KEY_SECRET"

python seedance.py text "A cinematic scene at sunset" --duration 8 --resolution 1080p --aspect-ratio 9:16
python seedance.py image "She turns and smiles" --image ./start.jpg --end-image ./end.jpg
python seedance.py reference "The two characters meet in a cafe" --ref-image ./a.png --ref-image ./b.png --ref-audio ./voice.wav
python seedance.py edit "Make it night with neon lights" --video ./clip.mp4
python seedance.py extend "The camera keeps pulling back" --video https://example.com/clip.mp4 --duration 6
```

Media options accept a public HTTPS URL or a local file. Local files are uploaded through Higgsfield's presigned upload URLs. Supported types are jpg, png, webp and gif images, wav audio and mp4 video.

The CLI checks your inputs against each endpoint's schema, prints a cost estimate to stderr, waits for the result and prints the video URL. If the request ends as `failed`, `nsfw` or `canceled`, it prints the full response and exits with code 1.

Add `--dry-run` to see the request body and the cost estimate without uploading anything or calling the API. It needs no credentials.

## Options

| Option | Modes | Values | Default |
| --- | --- | --- | --- |
| `--duration` | text, image, reference, extend | 4–30 seconds | 5 |
| `--resolution` | all | 480p, 720p, 1080p | 720p |
| `--aspect-ratio` | text, reference | 16:9, 4:3, 1:1, 3:4, 9:16, 21:9 | 16:9 |
| `--bitrate-mode` | all | standard, high | high |
| `--output-format` | text | mp4, mov | mp4 |
| `--ref-image` / `--ref-video` / `--ref-audio` | reference, edit, extend | repeatable; up to 30 / 10 / 10 | none |
| `--no-audio` | all | turns off audio generation | audio on |
| `--input-video-seconds` | modes with video input | length of the input videos, used only for the cost estimate | 0 |

## Pricing

Video is billed in tokens: `ceil(width × height × (input video seconds + generated seconds) × 24 / 1024)`.
For 16:9 output with no video input, that is about $0.21, $0.46 and $1.14 per second at 480p, 720p and 1080p.
When there is video input (edit, extend, or reference with videos), the token rate drops to 0.6×, but the input video's length is billed too.
Image and audio references are not billed as video.
These are prices before any discount. Estimates for other aspect ratios are approximate, because the docs give exact dimensions only for 16:9.

Run the tests with `python -m unittest`.
