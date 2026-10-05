"use server"

import { cookies } from "next/headers"

import { getModel, parseSettings } from "./catalog"
import type { GenerationPlane } from "./catalog/types"
import {
  MissingCredentialsError,
  PLATFORM_KEY_COOKIE,
  PLATFORM_KEY_COOKIE_OPTIONS,
  decodeCredentials,
  encodeCredentials,
  parseCredentialInput,
} from "./credentials"
import {
  PlatformError,
  createPlatformClient,
  describePlatformError,
  isIdempotencyKey,
} from "./platform"
import type { QueuedGeneration, StatusResult } from "./platform"
import { toPlatform } from "./to-platform"

export async function savePlatformCredentials(data: unknown) {
  const { apiKey } = parseCredentialInput(data)
  const jar = await cookies()
  jar.set(
    PLATFORM_KEY_COOKIE,
    encodeCredentials(apiKey),
    PLATFORM_KEY_COOKIE_OPTIONS
  )
}

export async function clearPlatformCredentials() {
  const jar = await cookies()
  jar.set(PLATFORM_KEY_COOKIE, "", {
    ...PLATFORM_KEY_COOKIE_OPTIONS,
    maxAge: 0,
  })
}

export async function hasPlatformCredentials() {
  return (await readStoredCredentials()) !== null
}

/** Server actions return failures as values: Next replaces the message of an
    error thrown from a server action in production builds, and the dock has
    to tell a missing key from a rejected one or an empty credit balance. */
export type ActionResult<T> =
  | { ok: true; value: T }
  | { ok: false; error: string; needsKey?: boolean }

/** `idempotencyKey` identifies one intended generation (one Generate click);
    a replay with the same key never starts or charges a second generation. */
export async function submitGeneration(
  plane: GenerationPlane,
  idempotencyKey: string
): Promise<ActionResult<QueuedGeneration>> {
  let request: { path: string; body: Record<string, unknown> }
  try {
    if (!isIdempotencyKey(idempotencyKey))
      throw new Error("Invalid submission. Reload the page and try again.")
    const model = getModel(plane.model)
    const parsed: GenerationPlane = {
      ...plane,
      settings: parseSettings(model, plane.settings),
    }
    request = toPlatform(parsed)
  } catch (caught) {
    return { ok: false, error: errorMessage(caught) }
  }
  return run(async (client) =>
    client.submit(request.path, request.body, idempotencyKey)
  )
}

/** Every request in flight, answered in one round trip. Next dispatches server
    actions one at a time per client, so a poll per run would queue ahead of the
    next submit — the fan-out belongs on this side of the call, where it is
    genuinely parallel. */
export async function getGenerationStatuses(
  data: unknown
): Promise<ActionResult<StatusResult[]>> {
  let requestIds: string[]
  try {
    requestIds = parseRequestIds(data)
  } catch (caught) {
    return { ok: false, error: errorMessage(caught) }
  }
  return run((client) =>
    Promise.all(
      requestIds.map(async (requestId): Promise<StatusResult> => {
        try {
          return { requestId, status: await client.status(requestId) }
        } catch (caught) {
          return {
            requestId,
            error: describePlatformError(caught),
            // Network failures, 429 and 5xx are worth asking again; a 401 or
            // 404 will not change on the next round.
            retryable:
              !(caught instanceof PlatformError) ||
              caught.status === 429 ||
              caught.status >= 500,
          }
        }
      })
    )
  )
}

/** Cancel reaches the platform; only queued requests can still be canceled. */
export async function cancelGeneration(
  data: unknown
): Promise<ActionResult<null>> {
  let requestId: string
  try {
    ;[requestId] = parseRequestIds(data) as [string]
  } catch (caught) {
    return { ok: false, error: errorMessage(caught) }
  }
  return run(async (client) => {
    try {
      await client.cancel(requestId)
    } catch (caught) {
      // Requests that already started processing can no longer be canceled.
      if (caught instanceof PlatformError && caught.status < 500)
        throw new PlatformError(caught.status, {
          detail: `This generation can no longer be canceled: ${caught.message}`,
        })
      throw caught
    }
    return null
  })
}

async function run<T>(
  action: (client: ReturnType<typeof createPlatformClient>) => Promise<T>
): Promise<ActionResult<T>> {
  let client: ReturnType<typeof createPlatformClient>
  try {
    client = createPlatformClient(await readCredentials())
  } catch (caught) {
    if (caught instanceof MissingCredentialsError)
      return { ok: false, error: caught.message, needsKey: true }
    return { ok: false, error: errorMessage(caught) }
  }
  try {
    return { ok: true, value: await action(client) }
  } catch (caught) {
    if (caught instanceof PlatformError && caught.status === 401)
      return { ok: false, error: describePlatformError(caught), needsKey: true }
    if (caught instanceof PlatformError && /can no longer be canceled/.test(caught.message))
      return { ok: false, error: caught.message }
    return { ok: false, error: describePlatformError(caught) }
  }
}

function errorMessage(caught: unknown): string {
  return caught instanceof Error ? caught.message : String(caught)
}

async function readStoredCredentials() {
  const jar = await cookies()
  return decodeCredentials(jar.get(PLATFORM_KEY_COOKIE)?.value)
}

async function readCredentials() {
  const stored = await readStoredCredentials()
  if (!stored) throw new MissingCredentialsError()
  const baseUrl = process.env.HF_API_BASE_URL
  if (!baseUrl) throw new Error("Missing HF_API_BASE_URL")
  return { ...stored, baseUrl }
}

function parseRequestIds(data: unknown): string[] {
  const payload = asObject(data, "Invalid status payload")
  const requestIds = payload.requestIds
  if (!Array.isArray(requestIds) || requestIds.length === 0) {
    throw new Error("Invalid request ids")
  }
  return requestIds.map((requestId) => {
    if (typeof requestId !== "string" || !requestId)
      throw new Error("Invalid request id")
    return requestId
  })
}

function asObject(data: unknown, message: string): Record<string, unknown> {
  if (data === null || typeof data !== "object" || Array.isArray(data))
    throw new Error(message)
  return data as Record<string, unknown>
}
