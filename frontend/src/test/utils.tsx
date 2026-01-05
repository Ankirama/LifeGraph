/**
 * Test utilities for rendering components with all necessary providers.
 */

import { ReactElement, ReactNode } from 'react';
import { render, RenderOptions, RenderResult } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, MemoryRouter, MemoryRouterProps } from 'react-router-dom';
import userEvent from '@testing-library/user-event';

/**
 * Create a fresh QueryClient for testing with sensible defaults.
 * Each test should use a new QueryClient to avoid state leakage.
 */
export function createTestQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: Infinity,
        staleTime: Infinity,
      },
      mutations: {
        retry: false,
      },
    },
  });
}

interface AllProvidersProps {
  children: ReactNode;
  queryClient?: QueryClient;
}

/**
 * Wrapper component with all providers needed for tests.
 */
function AllProviders({ children, queryClient }: AllProvidersProps) {
  const client = queryClient ?? createTestQueryClient();

  return (
    <QueryClientProvider client={client}>
      <BrowserRouter>{children}</BrowserRouter>
    </QueryClientProvider>
  );
}

interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  queryClient?: QueryClient;
  initialEntries?: MemoryRouterProps['initialEntries'];
}

/**
 * Custom render function that wraps the component with all necessary providers.
 *
 * @example
 * ```tsx
 * const { getByText, user } = renderWithProviders(<MyComponent />);
 * await user.click(getByText('Submit'));
 * ```
 */
export function renderWithProviders(
  ui: ReactElement,
  options: CustomRenderOptions = {}
): RenderResult & { user: ReturnType<typeof userEvent.setup> } {
  const { queryClient, initialEntries, ...renderOptions } = options;
  const client = queryClient ?? createTestQueryClient();

  const Wrapper = ({ children }: { children: ReactNode }) => {
    // Use MemoryRouter if initialEntries are provided
    const Router = initialEntries ? (
      <MemoryRouter initialEntries={initialEntries}>{children}</MemoryRouter>
    ) : (
      <BrowserRouter>{children}</BrowserRouter>
    );

    return (
      <QueryClientProvider client={client}>
        {Router}
      </QueryClientProvider>
    );
  };

  const user = userEvent.setup();

  return {
    user,
    ...render(ui, { wrapper: Wrapper, ...renderOptions }),
  };
}

/**
 * Create a mock API response for React Query.
 */
export function createMockApiResponse<T>(data: T) {
  return {
    data,
    status: 200,
    statusText: 'OK',
    headers: {},
    config: {} as any,
  };
}

/**
 * Wait for a condition to be true with a timeout.
 */
export async function waitForCondition(
  condition: () => boolean,
  timeout = 5000,
  interval = 50
): Promise<void> {
  const startTime = Date.now();

  while (!condition()) {
    if (Date.now() - startTime > timeout) {
      throw new Error('Condition not met within timeout');
    }
    await new Promise(resolve => setTimeout(resolve, interval));
  }
}

// Re-export everything from @testing-library/react
export * from '@testing-library/react';
export { userEvent };
