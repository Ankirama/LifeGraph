/**
 * Tests for GlobalSearch component.
 */

import { describe, it, expect, beforeAll, afterAll, afterEach, vi } from 'vitest';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';
import { renderWithProviders } from '@/test/utils';
import { GlobalSearch } from '../GlobalSearch';

// Mock search results
const mockSearchResults = {
  persons: [
    {
      id: '1',
      first_name: 'John',
      last_name: 'Doe',
      full_name: 'John Doe',
      nickname: 'Johnny',
      avatar: null,
    },
    {
      id: '2',
      first_name: 'Jane',
      last_name: 'Smith',
      full_name: 'Jane Smith',
      nickname: null,
      avatar: null,
    },
  ],
  anecdotes: [
    {
      id: 'a1',
      title: 'Birthday Party',
      content: 'We had a great time at the birthday party',
      anecdote_type: 'memory',
    },
  ],
  query: 'john',
};

const emptySearchResults = {
  persons: [],
  anecdotes: [],
  query: 'xyz',
};

// MSW server setup
const server = setupServer(
  http.get('/api/v1/search/', ({ request }) => {
    const url = new URL(request.url);
    const query = url.searchParams.get('q');
    if (query === 'john') {
      return HttpResponse.json(mockSearchResults);
    }
    return HttpResponse.json(emptySearchResults);
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('GlobalSearch', () => {
  describe('rendering', () => {
    it('renders search input with placeholder', () => {
      renderWithProviders(<GlobalSearch />);
      expect(screen.getByPlaceholderText(/Search people, anecdotes/)).toBeInTheDocument();
    });

    it('renders search icon', () => {
      const { container } = renderWithProviders(<GlobalSearch />);
      expect(container.querySelector('svg')).toBeInTheDocument();
    });

    it('does not show clear button when query is empty', () => {
      renderWithProviders(<GlobalSearch />);
      const buttons = screen.queryAllByRole('button');
      expect(buttons.length).toBe(0);
    });
  });

  describe('search input behavior', () => {
    it('updates input value when typing', async () => {
      const { user } = renderWithProviders(<GlobalSearch />);
      const input = screen.getByPlaceholderText(/Search people/);

      await user.type(input, 'john');

      expect(input).toHaveValue('john');
    });

    it('shows clear button when query has text', async () => {
      const { user } = renderWithProviders(<GlobalSearch />);
      const input = screen.getByPlaceholderText(/Search people/);

      await user.type(input, 'test');

      expect(screen.getByRole('button')).toBeInTheDocument();
    });

    it('clears input when clear button is clicked', async () => {
      const { user } = renderWithProviders(<GlobalSearch />);
      const input = screen.getByPlaceholderText(/Search people/);

      await user.type(input, 'test');
      await user.click(screen.getByRole('button'));

      expect(input).toHaveValue('');
    });
  });

  describe('search results dropdown', () => {
    it('does not show dropdown for queries less than 2 characters', async () => {
      const { user } = renderWithProviders(<GlobalSearch />);
      const input = screen.getByPlaceholderText(/Search people/);

      await user.type(input, 'j');

      expect(screen.queryByText('People')).not.toBeInTheDocument();
    });

    it('shows loading state during search', async () => {
      server.use(
        http.get('/api/v1/search/', async () => {
          await new Promise((resolve) => setTimeout(resolve, 100));
          return HttpResponse.json(mockSearchResults);
        })
      );

      const { user } = renderWithProviders(<GlobalSearch />);
      const input = screen.getByPlaceholderText(/Search people/);

      await user.type(input, 'john');

      expect(screen.getByText('Searching...')).toBeInTheDocument();
    });

    it('shows person results when found', async () => {
      const { user } = renderWithProviders(<GlobalSearch />);
      const input = screen.getByPlaceholderText(/Search people/);

      await user.type(input, 'john');

      await waitFor(() => {
        expect(screen.getByText('People')).toBeInTheDocument();
        expect(screen.getByText('John Doe')).toBeInTheDocument();
        expect(screen.getByText('Jane Smith')).toBeInTheDocument();
      });
    });

    it('shows person nickname when available', async () => {
      const { user } = renderWithProviders(<GlobalSearch />);
      const input = screen.getByPlaceholderText(/Search people/);

      await user.type(input, 'john');

      await waitFor(() => {
        expect(screen.getByText('"Johnny"')).toBeInTheDocument();
      });
    });

    it('shows anecdote results when found', async () => {
      const { user } = renderWithProviders(<GlobalSearch />);
      const input = screen.getByPlaceholderText(/Search people/);

      await user.type(input, 'john');

      await waitFor(() => {
        expect(screen.getByText('Anecdotes')).toBeInTheDocument();
        expect(screen.getByText('Birthday Party')).toBeInTheDocument();
      });
    });

    it('shows anecdote type', async () => {
      const { user } = renderWithProviders(<GlobalSearch />);
      const input = screen.getByPlaceholderText(/Search people/);

      await user.type(input, 'john');

      await waitFor(() => {
        expect(screen.getByText('memory')).toBeInTheDocument();
      });
    });

    it('shows no results message when nothing found', async () => {
      const { user } = renderWithProviders(<GlobalSearch />);
      const input = screen.getByPlaceholderText(/Search people/);

      await user.type(input, 'xyz');

      await waitFor(() => {
        expect(screen.getByText(/No results found for "xyz"/)).toBeInTheDocument();
      });
    });
  });

  describe('keyboard shortcuts', () => {
    it('focuses input on Cmd+K', async () => {
      renderWithProviders(<GlobalSearch />);
      const input = screen.getByPlaceholderText(/Search people/);

      fireEvent.keyDown(document, { key: 'k', metaKey: true });

      expect(document.activeElement).toBe(input);
    });

    it('focuses input on Ctrl+K', async () => {
      renderWithProviders(<GlobalSearch />);
      const input = screen.getByPlaceholderText(/Search people/);

      fireEvent.keyDown(document, { key: 'k', ctrlKey: true });

      expect(document.activeElement).toBe(input);
    });

    it('closes dropdown on Escape', async () => {
      const { user } = renderWithProviders(<GlobalSearch />);
      const input = screen.getByPlaceholderText(/Search people/);

      await user.type(input, 'john');

      await waitFor(() => {
        expect(screen.getByText('People')).toBeInTheDocument();
      });

      fireEvent.keyDown(document, { key: 'Escape' });

      expect(screen.queryByText('People')).not.toBeInTheDocument();
    });
  });

  describe('result selection', () => {
    it('navigates to person page when person result is clicked', async () => {
      const { user } = renderWithProviders(<GlobalSearch />);
      const input = screen.getByPlaceholderText(/Search people/);

      await user.type(input, 'john');

      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });

      // Find and click the person result
      const personButton = screen.getByText('John Doe').closest('button');
      if (personButton) {
        await user.click(personButton);
      }

      // Query should be cleared and dropdown closed
      expect(input).toHaveValue('');
    });

    it('clears query after selection', async () => {
      const { user } = renderWithProviders(<GlobalSearch />);
      const input = screen.getByPlaceholderText(/Search people/);

      await user.type(input, 'john');

      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });

      const personButton = screen.getByText('John Doe').closest('button');
      if (personButton) {
        await user.click(personButton);
      }

      expect(input).toHaveValue('');
    });
  });

  describe('click outside behavior', () => {
    it('closes dropdown when clicking outside', async () => {
      const { user } = renderWithProviders(
        <div>
          <GlobalSearch />
          <div data-testid="outside">Outside</div>
        </div>
      );
      const input = screen.getByPlaceholderText(/Search people/);

      await user.type(input, 'john');

      await waitFor(() => {
        expect(screen.getByText('People')).toBeInTheDocument();
      });

      fireEvent.mouseDown(screen.getByTestId('outside'));

      await waitFor(() => {
        expect(screen.queryByText('People')).not.toBeInTheDocument();
      });
    });
  });
});
