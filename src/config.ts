// Centralized configuration for the FastAPI control plane.
// The app defaults to 'http' mode, which talks to the FastAPI backend.
// Set EXPO_PUBLIC_API_MODE=mock to fall back to the in-app mock services for
// isolated UI development.

export const apiConfig = {
  // Configurable via environment. Defaults to localhost for iOS simulator.
  // For Android emulator use http://10.0.2.2:8000. For physical devices use
  // your development machine's LAN address.
  baseUrl: process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8000',
  timeoutMs: 15000,
};

export type ApiMode = 'mock' | 'http';

export const apiMode: ApiMode = (process.env.EXPO_PUBLIC_API_MODE as ApiMode) ?? 'http';
