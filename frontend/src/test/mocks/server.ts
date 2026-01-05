/**
 * MSW server setup for tests.
 *
 * Import and use in your test setup to enable API mocking.
 */

import { setupServer } from 'msw/node';
import { handlers } from './handlers';

// Create the mock server with default handlers
export const server = setupServer(...handlers);

// Optional: Export helper to reset handlers between tests
export function resetHandlers() {
  server.resetHandlers();
}

// Optional: Export helper to add handlers at runtime
export function useHandlers(...newHandlers: Parameters<typeof server.use>) {
  server.use(...newHandlers);
}
