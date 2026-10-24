// Centralized API client for the FastAPI backend.
// Handles JSON requests/responses, typed errors, timeouts, and safe parsing
// of error responses across HTTP 401, 403, 404, 409, 422 and 500.

import { apiConfig } from './config';

export interface ApiError {
  code: string;
  message: string;
  requestId?: string;
  details?: unknown;
  status: number;
}

const TIMEOUT_CODE = 'NETWORK_TIMEOUT';
const NETWORK_CODE = 'NETWORK_FAILURE';

function parseError(status: number, body: unknown): ApiError {
  if (body && typeof body === 'object' && 'error' in body) {
    const inner = (body as { error: { code?: string; message?: string; requestId?: string; details?: unknown } }).error;
    return {
      code: inner.code ?? 'UNKNOWN',
      message: inner.message ?? 'An unknown error occurred.',
      requestId: inner.requestId,
      details: inner.details,
      status,
    };
  }
  return { code: 'UNKNOWN', message: 'An unexpected error occurred.', status };
}

async function request<T>(path: string, options: { method: string; body?: unknown; signal?: AbortSignal }): Promise<T> {
  const url = `${apiConfig.baseUrl}${path}`;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), apiConfig.timeoutMs);

  try {
    const res = await fetch(url, {
      method: options.method,
      headers: { 'Content-Type': 'application/json' },
      body: options.body ? JSON.stringify(options.body) : undefined,
      signal: options.signal ?? controller.signal,
    });

    const text = await res.text();
    const body = text ? JSON.parse(text) : null;

    if (!res.ok) {
      throw parseError(res.status, body);
    }
    return body as T;
  } catch (err) {
    if (err instanceof Error && err.name === 'AbortError') {
      const error: ApiError = { code: TIMEOUT_CODE, message: 'The request timed out. Please try again.', status: 0 };
      throw error;
    }
    if (err && typeof err === 'object' && 'code' in err) {
      throw err;
    }
    const error: ApiError = { code: NETWORK_CODE, message: 'Could not reach the server. Please check your connection.', status: 0 };
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}

export const api = {
  get: <T>(path: string) => request<T>(path, { method: 'GET' }),
  post: <T>(path: string, body?: unknown) => request<T>(path, { method: 'POST', body }),
};

export function isApiError(err: unknown): err is ApiError {
  return err !== null && typeof err === 'object' && 'code' in err && 'status' in err;
}
