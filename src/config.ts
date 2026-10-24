// Centralized configuration for the future FastAPI control plane.
// Phase 1 keeps all operations simulated; this base URL is reserved for Phase 2
// so screens never hard-code backend endpoints.
export const apiConfig = {
  baseUrl: '',
  timeoutMs: 15000,
};

export type ApiMode = 'mock' | 'http';

export const apiMode: ApiMode = 'mock';
