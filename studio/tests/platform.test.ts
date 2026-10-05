import { describe, expect, it, vi } from "vitest"

import {
  PlatformError,
  createPlatformClient,
  describePlatformError,
} from "@/generation/platform"

const KEY = "11111111-2222-3333-4444-555555555555"

function json(status: number, body: unknown, headers?: Record<string, string>) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", ...headers },
  })
}

function client(fetchImpl: typeof fetch) {
  return createPlatformClient({
    apiKey: "key-id:key-secret",
    baseUrl: "https://api.higgsfield.ai/",
    fetch: fetchImpl,
    sleep: async () => {},
  })
}

const queued = {
  status: "queued",
  request_id: "req-1",
  status_url: "https://api.higgsfield.ai/requests/req-1/status",
  cancel_url: "https://api.higgsfield.ai/requests/req-1/cancel",
}

describe("submit", () => {
  it("sends the Key scheme, JSON body and Idempotency-Key", async () => {
    const fetchImpl = vi.fn(async () => json(200, queued))
    const result = await client(fetchImpl).submit(
      "bytedance/seedance-2.5/text-to-video",
      { prompt: "A cinematic scene at sunset" },
      KEY
    )
    expect(result.requestId).toBe("req-1")
    const [url, init] = fetchImpl.mock.calls[0] as unknown as [string, RequestInit]
    expect(url).toBe("https://api.higgsfield.ai/bytedance/seedance-2.5/text-to-video")
    expect(init.headers).toMatchObject({
      Authorization: "Key key-id:key-secret",
      "Content-Type": "application/json",
      "Idempotency-Key": KEY,
    })
  })

  it("replays an ambiguous failure with the same key", async () => {
    const fetchImpl = vi
      .fn<typeof fetch>()
      .mockRejectedValueOnce(new TypeError("fetch failed"))
      .mockResolvedValueOnce(json(502, { detail: "Bad gateway" }))
      .mockResolvedValueOnce(json(200, queued))
    await client(fetchImpl).submit("model/path", { prompt: "x" }, KEY)
    expect(fetchImpl).toHaveBeenCalledTimes(3)
    const keys = fetchImpl.mock.calls.map(
      ([, init]) => (init?.headers as Record<string, string>)["Idempotency-Key"]
    )
    expect(new Set(keys)).toEqual(new Set([KEY]))
  })

  it("does not retry a rejected request", async () => {
    const fetchImpl = vi.fn(async () => json(403, { detail: "Not enough credits" }))
    await expect(client(fetchImpl).submit("model/path", {}, KEY)).rejects.toMatchObject({
      status: 403,
    })
    expect(fetchImpl).toHaveBeenCalledTimes(1)
  })

  it("gives up after three ambiguous attempts", async () => {
    const fetchImpl = vi.fn(async () => json(500, { detail: "boom" }))
    await expect(client(fetchImpl).submit("model/path", {}, KEY)).rejects.toBeInstanceOf(
      PlatformError
    )
    expect(fetchImpl).toHaveBeenCalledTimes(3)
  })

  it("refuses a missing idempotency key", async () => {
    const fetchImpl = vi.fn(async () => json(200, queued))
    await expect(client(fetchImpl).submit("model/path", {}, "")).rejects.toThrow()
    expect(fetchImpl).not.toHaveBeenCalled()
  })
})

describe("cancel and status", () => {
  it("cancel POSTs to the platform", async () => {
    const fetchImpl = vi.fn(async () => json(202, {}))
    await client(fetchImpl).cancel("req-1")
    const [url, init] = fetchImpl.mock.calls[0] as unknown as [string, RequestInit]
    expect(url).toBe("https://api.higgsfield.ai/requests/req-1/cancel")
    expect(init.method).toBe("POST")
  })

  it("status maps the completed video URL", async () => {
    const fetchImpl = vi.fn(async () =>
      json(200, { status: "completed", request_id: "req-1", video: { url: "https://cdn/v.mp4" } })
    )
    expect(await client(fetchImpl).status("req-1")).toEqual({
      status: "completed",
      requestId: "req-1",
      video: { url: "https://cdn/v.mp4" },
    })
  })
})

describe("describePlatformError", () => {
  it.each([
    [401, { detail: "Invalid credentials" }, /rejected this API key/],
    [403, { detail: "Insufficient credits" }, /\(403\): Insufficient credits\. .*add credits/],
    [403, "Host not in allowlist", /\(403\): Host not in allowlist/],
    [400, { detail: "Maximum number of concurrent requests (4) has been reached" }, /Too many generations/],
    [422, { detail: [{ loc: ["body", "duration"], msg: "must be <= 30" }] }, /duration: must be <= 30/],
    [503, { detail: "Model not ready" }, /disabled or not ready/],
  ])("maps %i", (status, body, expected) => {
    expect(describePlatformError(new PlatformError(status, body))).toMatch(expected)
  })

  it("describes network failures", () => {
    expect(describePlatformError(new TypeError("fetch failed"))).toMatch(/Could not reach/)
  })
})
