# Reel Studio

A web studio for cinematic video, built on the Higgsfield Studio template. Seedance 2.5 is the default model, and the full Higgsfield model catalog (30 video and 8 image models) is available in the picker.

## Run it

```bash
pnpm install
echo "HF_API_BASE_URL=https://api.higgsfield.ai" > .env.local
pnpm dev            # or: pnpm build && pnpm start
```

Open http://localhost:3000, click **Connect API key** in the sidebar and paste the key copied from [open.higgsfield.ai](https://open.higgsfield.ai/api-keys) exactly as copied.

- The key is stored in an HTTP-only cookie and used only by the server. It never reaches browser code, localStorage or the logs.
- Each user brings their own key, so generations are billed to that user's Higgsfield account.

In a Claude Code cloud environment, start the server with `NODE_USE_ENV_PROXY=1`. Without it, Node's `fetch` bypasses the environment proxy and Higgsfield requests fail with `403 Host not in allowlist`.

## How generation works

- **Submit.** `generation/actions.ts` sends `POST /<model-path>` with `Authorization: Key <key>` and a fresh `Idempotency-Key` for each Generate click.
  - A network error or a 5xx is replayed up to three times with the same key. Higgsfield then returns the original request instead of starting, and charging for, a second one.
  - Other errors are not retried.
- **Poll.** `generation/poll.ts` checks every request in flight together. The interval starts at 2 seconds and grows to 10, with jitter.
  - Transient status errors are asked again on the next round.
  - `completed`, `failed`, `nsfw` and `canceled` are final.
- **Cancel.** `POST /requests/<id>/cancel` reaches the platform. Only queued requests can be canceled.
- **Uploads.** `app/api/upload/route.ts` gets a signed upload URL with the saved key. The browser then uploads the file with the returned headers and without credentials.
- **Errors.** Server actions return errors as values, so their messages survive production builds. Users see clear messages for an invalid key (the key dialog reopens), a lack of credits, too many concurrent requests, a blocked or unavailable model, and validation errors.

## Checks

```bash
pnpm typecheck && pnpm lint && pnpm test && pnpm build
```

## Verification status

- **Tested without a real key:**
  - unit tests;
  - in the browser: presets, the settings dialog, key connect/replace/remove, a fake key rejected by the live API (401), exactly one submission on double click, upload errors, all 38 models in the pickers, and a narrow viewport.
- **Not yet tested:** a real generation, reference uploads, and canceling a live request. All of these need a real API key.
- **Seedance 2.5** (text, image, reference, edit, extend): the request bodies validate against the documented schemas.
  - The catalog offers 480p and 720p, while the docs also list 1080p.
- **Request bodies that do not match the documentation** (the API would reject them):
  - `kling-3-motion-std` and `kling-3-motion-pro`: allow prompt-only requests, but the docs require `image_url` and `video_url`.
  - `kling-2.5`: allows prompt-only requests, but the docs require `image_url`.
  - `kling-o1`: allows prompt-only requests, but the docs require `first_frame_url`.
  - `kling-o3`: allows prompt-only requests, but the docs require `first_frame_url` and `multi_prompt`.
  - `minimax-h3`: sends `720p`, but the docs accept only `2K`.
  - `minimax-hailuo-2.3`: default duration is 5, but the docs accept only 6 or 10.
  - `ltx-2.5-fast` and `ltx-2.5-pro`: default duration is 5, but the docs accept only 6, 8 or 10.
  - `ideogram-4`: sends `resolution`, which the docs do not accept.
  - Some image models offer `auto` aspect or resolutions that the docs do not list.
- **Endpoints not found in the documentation pages linked from open.higgsfield.ai/explore:**
  - `soul-cinema`, `seedance-2-fast`, `seedance-2-mini`, `flux-2`, `flux-3`, `pixverse-6` and `dop`.
  - Their availability is unverified, not disproved.
- **Kept on purpose:** all the models above stay in the picker until they are fixed or confirmed.
