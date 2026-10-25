// Centralized configuration for the FastAPI control plane.
// The app defaults to 'http' mode, which talks to the FastAPI backend.
// Set EXPO_PUBLIC_API_MODE=mock to fall back to the in-app mock services for
// isolated UI development.

import Constants from 'expo-constants';

const getBaseUrl = (): string => {
  if (process.env.EXPO_PUBLIC_API_URL) {
    return process.env.EXPO_PUBLIC_API_URL;
  }
  // When running on a physical phone via Expo Go, auto-resolve Metro host PC's IP
  const hostUri = Constants.expoConfig?.hostUri;
  if (hostUri) {
    const host = hostUri.split(':')[0];
    if (host && host !== 'localhost' && host !== '127.0.0.1') {
      return `http://${host}:8000`;
    }
  }
  return 'http://localhost:8000';
};

export const apiConfig = {
  baseUrl: getBaseUrl(),
  timeoutMs: 120000,
};

export type ApiMode = 'mock' | 'http';

export const apiMode: ApiMode = (process.env.EXPO_PUBLIC_API_MODE as ApiMode) ?? 'http';
