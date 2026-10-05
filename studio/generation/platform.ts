import { toAuthorizationHeader } from "./credentials"
import { parseUploadTicket, requireUploadContentType } from "./upload-contract"
import type { UploadTicket } from "./upload-contract"

const UPLOAD_PATH = "/files/generate-upload-url"
const MODEL_ID = /^[a-z0-9][a-z0-9._/-]*$/i
/** 1–255 visible ASCII characters, per the idempotency docs. */
const IDEMPOTENCY_KEY = /^[\x21-\x7E]{1,255}$/
/** Submissions that fail ambiguously (network error or 5xx) are replayed with
    the same Idempotency-Key, which the platform answers with the original
    request instead of starting and charging a second generation. */
const SUBMIT_ATTEMPTS = 3

export class PlatformError extends Error {
  readonly status: number
  readonly body: unknown

  constructor(status: number, body: unknown) {
    super(messageFromBody(status, body))
    this.name = "PlatformError"
    this.status = status
    this.body = body
  }
}

export type QueuedGeneration = {
  status: string
  requestId: string
  statusUrl: string
  cancelUrl: string
}

export type GenerationStatus = {
  status: string
  requestId: string
  images?: Array<{ url: string }>
  video?: { url: string }
  error?: unknown
}

/** One request's answer inside a batched status poll. A request that errors
    carries its reason alone, so it cannot lose the answers standing beside it. */
export type StatusResult =
  | { requestId: string; status: GenerationStatus }
  | { requestId: string; error: string; retryable: boolean }

export type PlatformClientOptions = {
  apiKey: string
  baseUrl: string
  fetch?: typeof fetch
  /** Delay between submit retries; injectable for tests. */
  sleep?: (ms: number) => Promise<void>
}

export function isIdempotencyKey(value: unknown): value is string {
  return typeof value === "string" && IDEMPOTENCY_KEY.test(value)
}

export function isModelId(model: string): boolean {
  return MODEL_ID.test(model) && !model.includes("..")
}

export function createPlatformClient(options: PlatformClientOptions) {
  const baseUrl = options.baseUrl.replace(/\/$/, "")
  const fetchImpl = options.fetch ?? fetch
  const sleep =
    options.sleep ??
    ((ms: number) => new Promise<void>((resolve) => setTimeout(resolve, ms)))
  const auth = toAuthorizationHeader(options.apiKey)

  async function send(
    method: "GET" | "POST",
    path: string,
    body?: Record<string, unknown>,
    extraHeaders?: Record<string, string>
  ) {
    const url = `${baseUrl}${path}`
    console.info("[platform] request", { method, url, body: body ?? null })
    const response = await fetchImpl(url, {
      method,
      headers: {
        Authorization: auth,
        ...(body ? { "Content-Type": "application/json" } : {}),
        ...extraHeaders,
      },
      ...(body ? { body: JSON.stringify(body) } : {}),
    })

    const payload = await readJson(response)
    // Signed upload URLs are credentials; do not write them to logs.
    console.info("[platform] response", {
      method,
      url,
      status: response.status,
      correlationId: response.headers.get("x-correlation-id"),
      ...(path === UPLOAD_PATH ? {} : { body: payload }),
    })
    if (!response.ok) throw new PlatformError(response.status, payload)
    return payload
  }

  return {
    async createUpload(contentType: unknown): Promise<UploadTicket> {
      const type = requireUploadContentType(contentType)
      return parseUploadTicket(
        await send("POST", UPLOAD_PATH, { content_type: type }),
        type
      )
    },
    async submit(
      model: string,
      input: Record<string, unknown>,
      idempotencyKey: string
    ): Promise<QueuedGeneration> {
      if (!isModelId(model))
        throw new PlatformError(400, { detail: "Invalid model" })
      if (!isIdempotencyKey(idempotencyKey))
        throw new PlatformError(400, { detail: "Invalid idempotency key" })
      for (let attempt = 1; ; attempt++) {
        try {
          return mapQueued(
            await send("POST", `/${model}`, input, {
              "Idempotency-Key": idempotencyKey,
            })
          )
        } catch (caught) {
          const ambiguous =
            !(caught instanceof PlatformError) || caught.status >= 500
          if (!ambiguous || attempt >= SUBMIT_ATTEMPTS) throw caught
          await sleep(1000 * 2 ** (attempt - 1) + Math.random() * 250)
        }
      }
    },
    async status(requestId: string): Promise<GenerationStatus> {
      if (!requestId)
        throw new PlatformError(400, { detail: "Missing request id" })
      return mapStatus(
        await send("GET", `/requests/${encodeURIComponent(requestId)}/status`)
      )
    },
    /** Queued requests only; the platform answers 202 and the status turns "canceled". */
    async cancel(requestId: string): Promise<void> {
      if (!requestId)
        throw new PlatformError(400, { detail: "Missing request id" })
      await send(
        "POST",
        `/requests/${encodeURIComponent(requestId)}/cancel`,
        {}
      )
    },
  }
}

function mapQueued(payload: unknown): QueuedGeneration {
  const data = asRecord(payload)
  const requestId = stringField(data, "request_id")
  if (!requestId)
    throw new PlatformError(502, {
      detail: "Platform response missing request_id",
    })
  return {
    status: stringField(data, "status") ?? "queued",
    requestId,
    statusUrl: stringField(data, "status_url") ?? "",
    cancelUrl: stringField(data, "cancel_url") ?? "",
  }
}

function mapStatus(payload: unknown): GenerationStatus {
  const data = asRecord(payload)
  const requestId = stringField(data, "request_id") ?? ""
  const images = Array.isArray(data.images)
    ? data.images.flatMap((item) => {
        const url = asRecord(item).url
        return typeof url === "string" ? [{ url }] : []
      })
    : undefined
  const videoUrl = asRecord(data.video).url

  return {
    status: stringField(data, "status") ?? "unknown",
    requestId,
    ...(images?.length ? { images } : {}),
    ...(typeof videoUrl === "string" ? { video: { url: videoUrl } } : {}),
    ...(data.error !== undefined ? { error: data.error } : {}),
  }
}

function asRecord(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {}
}

function stringField(
  value: Record<string, unknown>,
  key: string
): string | undefined {
  const field = value[key]
  return typeof field === "string" ? field : undefined
}

async function readJson(response: Response): Promise<unknown> {
  const text = await response.text()
  if (!text) return null
  try {
    return JSON.parse(text) as unknown
  } catch {
    return text
  }
}

function messageFromBody(status: number, body: unknown): string {
  const detail = asRecord(body).detail
  if (typeof detail === "string" && detail) return detail
  // Validation errors carry a list of { loc, msg } entries.
  if (Array.isArray(detail)) {
    const messages = detail.flatMap((entry) => {
      const record = asRecord(entry)
      const msg = record.msg
      if (typeof msg !== "string") return []
      const loc = Array.isArray(record.loc)
        ? record.loc.filter((part) => part !== "body").join(".")
        : ""
      return [loc ? `${loc}: ${msg}` : msg]
    })
    if (messages.length) return messages.join("; ")
  }
  // Non-JSON answers (gateways, proxies) carry their reason as plain text.
  if (typeof body === "string" && body.trim())
    return body.trim().slice(0, 300)
  return `Platform request failed (${status})`
}

/** What the user should read for a failed platform call, by HTTP status. */
export function describePlatformError(caught: unknown): string {
  if (!(caught instanceof PlatformError))
    return "Could not reach Higgsfield. Check your connection and try again."
  const { status, message } = caught
  switch (status) {
    case 400:
      return /concurrent/i.test(message)
        ? "Too many generations are running on this Higgsfield account. Wait for one to finish, then try again."
        : `Higgsfield rejected the request: ${message}`
    case 401:
      return "Higgsfield rejected this API key. Replace it from the sidebar."
    case 403:
      return `Higgsfield refused the request (403): ${message}. If your credit balance is empty, add credits at open.higgsfield.ai.`
    case 404:
      return "This model or request is not available for your Higgsfield account."
    case 422:
      return `Higgsfield could not accept these settings: ${message}`
    case 423:
      return "This model is temporarily blocked. Try again later."
    case 429:
      return "Higgsfield rate limit reached. Wait a moment and try again."
    case 503:
      return "This model is disabled or not ready right now. Try again later."
    default:
      return status >= 500
        ? `Higgsfield had a server error (${status}). Try again shortly.`
        : message
  }
}
