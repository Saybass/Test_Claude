import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

const getGenerationStatuses = vi.fn()
vi.mock("@/generation/actions", () => ({ getGenerationStatuses }))

const { POLL_INITIAL_MS, POLL_MAX_MS, stopWatching, watchRequest } = await import(
  "@/generation/poll"
)

describe("watchRequest", () => {
  beforeEach(() => {
    vi.useFakeTimers()
    getGenerationStatuses.mockReset()
  })
  afterEach(() => {
    stopWatching()
    vi.useRealTimers()
  })

  it("keeps polling through transient errors and resolves on a terminal status", async () => {
    getGenerationStatuses
      .mockResolvedValueOnce({ ok: true, value: [{ requestId: "r", status: { status: "in_progress", requestId: "r" } }] })
      .mockResolvedValueOnce({ ok: true, value: [{ requestId: "r", error: "Higgsfield had a server error (502).", retryable: true }] })
      .mockResolvedValueOnce({ ok: true, value: [{ requestId: "r", status: { status: "nsfw", requestId: "r" } }] })
    const done = watchRequest("r")
    await vi.advanceTimersByTimeAsync(POLL_MAX_MS * 4)
    await expect(done).resolves.toEqual({ status: "nsfw", requestId: "r" })
    expect(getGenerationStatuses).toHaveBeenCalledTimes(3)
  })

  it("fails the run on a permanent status error", async () => {
    getGenerationStatuses.mockResolvedValue({
      ok: true,
      value: [{ requestId: "r", error: "Not available", retryable: false }],
    })
    const done = watchRequest("r")
    const assertion = expect(done).rejects.toThrow("Not available")
    await vi.advanceTimersByTimeAsync(POLL_MAX_MS)
    await assertion
  })

  it("backs off from the initial interval toward the maximum", async () => {
    getGenerationStatuses.mockResolvedValue({
      ok: true,
      value: [{ requestId: "r", status: { status: "queued", requestId: "r" } }],
    })
    void watchRequest("r")
    await vi.advanceTimersByTimeAsync(POLL_INITIAL_MS - 1)
    expect(getGenerationStatuses).toHaveBeenCalledTimes(0)
    await vi.advanceTimersByTimeAsync(60_000)
    // 2s, 3s, 4.5s, 6.75s, then ~10s apart (+ jitter): far fewer than 30 fixed 2s polls.
    const calls = getGenerationStatuses.mock.calls.length
    expect(calls).toBeGreaterThanOrEqual(7)
    expect(calls).toBeLessThanOrEqual(10)
  })
})
