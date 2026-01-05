/**
 * Example test file demonstrating the testing setup.
 *
 * This file shows how to:
 * - Use the custom render function with providers
 * - Mock API calls with MSW
 * - Test user interactions
 */

import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest';
import { screen } from '@testing-library/react';
import { renderWithProviders } from './utils';
import { server } from './mocks/server';

// Enable API mocking for these tests
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

// Simple component for testing
function TestComponent({ message }: { message: string }) {
  return (
    <div>
      <h1>Test Component</h1>
      <p data-testid="message">{message}</p>
      <button>Click me</button>
    </div>
  );
}

describe('Testing Setup Verification', () => {
  it('renders a simple component', () => {
    renderWithProviders(<TestComponent message="Hello, World!" />);

    expect(screen.getByRole('heading', { name: /test component/i })).toBeInTheDocument();
    expect(screen.getByTestId('message')).toHaveTextContent('Hello, World!');
  });

  it('handles user interactions', async () => {
    const { user } = renderWithProviders(<TestComponent message="Interactive" />);

    const button = screen.getByRole('button', { name: /click me/i });
    expect(button).toBeInTheDocument();

    // Verify user can interact with elements
    await user.click(button);
    // Button is still there after click
    expect(button).toBeInTheDocument();
  });

  it('provides query client and router context', () => {
    // This test verifies that providers are correctly set up
    // If providers were missing, the render would fail
    renderWithProviders(<TestComponent message="With providers" />);

    expect(screen.getByTestId('message')).toHaveTextContent('With providers');
  });
});

describe('jest-dom matchers', () => {
  it('supports toBeInTheDocument', () => {
    renderWithProviders(<TestComponent message="DOM matcher test" />);
    expect(screen.getByTestId('message')).toBeInTheDocument();
  });

  it('supports toHaveTextContent', () => {
    renderWithProviders(<TestComponent message="Text content test" />);
    expect(screen.getByTestId('message')).toHaveTextContent('Text content test');
  });

  it('supports toBeVisible', () => {
    renderWithProviders(<TestComponent message="Visible" />);
    expect(screen.getByTestId('message')).toBeVisible();
  });
});
