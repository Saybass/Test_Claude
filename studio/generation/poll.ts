import { getGenerationStatuses } from "./actions"
import type { GenerationStatus, StatusResult } from "./platform"

/** Statuses the platform never moves off again. */
const TERMINAL = new Set(["completed", "failed", "nsfw", "canceled"])

/** Backoff per the polling docs: start at two seconds, grow toward ten, with
    jitter. A newly watched request resets the interval to the start. */
export const POLL_INITIAL_MS = 2000
export const POLL_MAX_MS = 10_000
const POLL_GROWTH = 1.5
const POLL_JITTER_MS = 500
export const POLL_DEADLINE_MS = 10 * 60_000
/** Rounds allowed to fail back to back before the watches are given up on. One
    dropped round must not end every generation in flight. */
const MAX_MISSES = 3

type Waiter = {
  deadline: number
  resolve: (status: GenerationStatus) => void
  reject: (reason: Error) => void
}

const waiting = new Map<string, Waiter>()
const inflight = new Map<string, Promise<GenerationStatus>>()
let timer: ReturnType<typeof setTimeout> | null = null
let polling = false
let misses = 0
let interval = POLL_INITIAL_MS

/** Resolves when the platform reports a terminal status for this request.
    Every request in flight is asked for together, in one server action per
    interval: Next dispatches server actions one at a time per client, so a
    poll per run would queue ahead of the next submit and the composer would
    stall again — with the lock gone and the queue doing the same work. */
export function watchRequest(
  requestId: string,
  opts?: { deadline?: number }
): Promise<GenerationStatus> {
  const existing = inflight.get(requestId)
  if (existing) return existing
  const promise = new Promise<GenerationStatus>((resolve, reject) => {
    waiting.set(requestId, {
      deadline: opts?.deadline ?? Date.now() + POLL_DEADLINE_MS,
      resolve: (status) => {
        inflight.delete(requestId)
        resolve(status)
      },
      reject: (reason) => {
        inflight.delete(requestId)
        reject(reason)
      },
    })
    interval = POLL_INITIAL_MS
    schedule()
  })
  inflight.set(requestId, promise)
  return promise
}

/** Drops every watch without settling it: the studio unmounted and there is
    nobody left to hand a result to. In-flight jobs stay in history and the
    next mount starts a fresh watch. */
export function stopWatching(): void {
  if (timer !== null) clearTimeout(timer)
  timer = null
  misses = 0
  waiting.clear()
  inflight.clear()
  interval = POLL_INITIAL_MS
}

function schedule(): void {
  if (timer !== null || polling || waiting.size === 0) return
  const delay = interval + Math.random() * POLL_JITTER_MS
  interval = Math.min(interval * POLL_GROWTH, POLL_MAX_MS)
  timer = setTimeout(() => void round(), delay)
}

async function round(): Promise<void> {
  timer = null
  polling = true
  try {
    const answer = await getGenerationStatuses({
      requestIds: [...waiting.keys()],
    })
    if (!answer.ok) throw new Error(answer.error)
    misses = 0
    for (const result of answer.value) deliver(result)
    sweep()
  } catch (caught) {
    if (++misses < MAX_MISSES) return
    settleAll(caught instanceof Error ? caught : new Error(String(caught)))
  } finally {
    polling = false
    schedule()
  }
}

function deliver(result: StatusResult): void {
  const waiter = waiting.get(result.requestId)
  if (!waiter) return
  if ("error" in result) {
    // Transient failures are asked again next round; the deadline still applies.
    if (result.retryable) return
    waiting.delete(result.requestId)
    waiter.reject(new Error(result.error))
    return
  }
  if (!TERMINAL.has(result.status.status)) return
  waiting.delete(result.requestId)
  waiter.resolve(result.status)
}

/* A run the platform never finishes would otherwise hold its skeleton open for
   the rest of the session. */
function sweep(): void {
  const now = Date.now()
  for (const [requestId, waiter] of [...waiting]) {
    if (now <= waiter.deadline) continue
    waiting.delete(requestId)
    waiter.reject(new Error("timed out waiting for the platform"))
  }
}

function settleAll(reason: Error): void {
  const waiters = [...waiting.values()]
  waiting.clear()
  misses = 0
  for (const waiter of waiters) waiter.reject(reason)
}
