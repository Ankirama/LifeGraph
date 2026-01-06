/**
 * Tests for AnecdotesPage page.
 */

import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';
import { renderWithProviders } from '@/test/utils';
import { AnecdotesPage } from '../AnecdotesPage';

// Mock data
const mockAnecdotes = {
  results: [
    {
      id: 'a1',
      title: 'Funny Story',
      content: 'This is a hilarious story about the office party.',
      anecdote_type: 'joke',
      date: '2023-06-15',
      location: 'New York',
      persons: [
        { id: 'p1', full_name: 'John Doe', first_name: 'John' },
        { id: 'p2', full_name: 'Jane Smith', first_name: 'Jane' },
      ],
      tags: [{ id: 't1', name: 'Work', color: '#3b82f6' }],
    },
    {
      id: 'a2',
      title: 'Beach Trip Memory',
      content: 'We had an amazing time at the beach last summer.',
      anecdote_type: 'memory',
      date: '2023-08-20',
      location: 'Miami Beach',
      persons: [{ id: 'p1', full_name: 'John Doe', first_name: 'John' }],
      tags: [
        { id: 't2', name: 'Travel', color: '#22c55e' },
        { id: 't3', name: 'Summer', color: '#eab308' },
      ],
    },
    {
      id: 'a3',
      title: '',
      content: "Life is what happens when you're busy making other plans.",
      anecdote_type: 'quote',
      date: null,
      location: null,
      persons: [],
      tags: [],
    },
    {
      id: 'a4',
      title: 'Meeting Notes',
      content: 'Discussed project timeline and deliverables.',
      anecdote_type: 'note',
      date: '2024-01-10',
      location: null,
      persons: [{ id: 'p3', full_name: 'Bob Johnson', first_name: 'Bob' }],
      tags: [{ id: 't1', name: 'Work', color: '#3b82f6' }],
    },
  ],
};

// MSW server setup
const server = setupServer(
  http.get('/api/v1/anecdotes/', ({ request }) => {
    const url = new URL(request.url);
    const type = url.searchParams.get('anecdote_type');
    const search = url.searchParams.get('search');

    let results = mockAnecdotes.results;

    if (type) {
      results = results.filter((a) => a.anecdote_type === type);
    }
    if (search) {
      results = results.filter(
        (a) =>
          a.title?.toLowerCase().includes(search.toLowerCase()) ||
          a.content.toLowerCase().includes(search.toLowerCase())
      );
    }

    return HttpResponse.json({ results });
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('AnecdotesPage', () => {
  describe('loading state', () => {
    it('shows loading indicator initially', () => {
      renderWithProviders(<AnecdotesPage />);
      expect(screen.getByText('Loading anecdotes...')).toBeInTheDocument();
    });
  });

  describe('page header', () => {
    it('displays page title', async () => {
      renderWithProviders(<AnecdotesPage />);
      await waitFor(() => {
        expect(screen.getByRole('heading', { name: 'Anecdotes' })).toBeInTheDocument();
      });
    });

    it('displays page description', async () => {
      renderWithProviders(<AnecdotesPage />);
      await waitFor(() => {
        expect(
          screen.getByText(/Memories, jokes, quotes, and notes about people/i)
        ).toBeInTheDocument();
      });
    });

    it('displays Add Anecdote button', async () => {
      renderWithProviders(<AnecdotesPage />);
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Add Anecdote/i })).toBeInTheDocument();
      });
    });
  });

  describe('filters', () => {
    it('renders search input', async () => {
      renderWithProviders(<AnecdotesPage />);
      await waitFor(() => {
        expect(screen.getByPlaceholderText('Search anecdotes...')).toBeInTheDocument();
      });
    });

    it('renders type filter dropdown', async () => {
      renderWithProviders(<AnecdotesPage />);
      await waitFor(() => {
        expect(screen.getByRole('combobox')).toBeInTheDocument();
      });
    });

    it('has All Types as default option', async () => {
      renderWithProviders(<AnecdotesPage />);
      await waitFor(() => {
        const select = screen.getByRole('combobox');
        expect(select).toHaveValue('');
      });
    });

    it('filters by type when dropdown changes', async () => {
      const { user } = renderWithProviders(<AnecdotesPage />);

      await waitFor(() => {
        expect(screen.getByText('Funny Story')).toBeInTheDocument();
      });

      const select = screen.getByRole('combobox');
      await user.selectOptions(select, 'memory');

      await waitFor(() => {
        expect(screen.getByText('Beach Trip Memory')).toBeInTheDocument();
        expect(screen.queryByText('Funny Story')).not.toBeInTheDocument();
      });
    });

    it('filters by search text', async () => {
      const { user } = renderWithProviders(<AnecdotesPage />);

      await waitFor(() => {
        expect(screen.getByText('Funny Story')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText('Search anecdotes...');
      await user.type(searchInput, 'beach');

      await waitFor(() => {
        expect(screen.getByText('Beach Trip Memory')).toBeInTheDocument();
        expect(screen.queryByText('Funny Story')).not.toBeInTheDocument();
      });
    });
  });

  describe('anecdote cards', () => {
    it('displays anecdote titles', async () => {
      renderWithProviders(<AnecdotesPage />);
      await waitFor(() => {
        expect(screen.getByText('Funny Story')).toBeInTheDocument();
        expect(screen.getByText('Beach Trip Memory')).toBeInTheDocument();
        expect(screen.getByText('Meeting Notes')).toBeInTheDocument();
      });
    });

    it('displays anecdote content', async () => {
      renderWithProviders(<AnecdotesPage />);
      await waitFor(() => {
        expect(screen.getByText(/hilarious story about the office party/i)).toBeInTheDocument();
        expect(screen.getByText(/amazing time at the beach/i)).toBeInTheDocument();
      });
    });

    it('displays type badges', async () => {
      renderWithProviders(<AnecdotesPage />);
      await waitFor(() => {
        expect(screen.getByText('joke')).toBeInTheDocument();
        expect(screen.getByText('memory')).toBeInTheDocument();
        expect(screen.getByText('quote')).toBeInTheDocument();
        expect(screen.getByText('note')).toBeInTheDocument();
      });
    });

    it('displays dates when available', async () => {
      renderWithProviders(<AnecdotesPage />);
      await waitFor(() => {
        expect(screen.getByText('Jun 15, 2023')).toBeInTheDocument();
        expect(screen.getByText('Aug 20, 2023')).toBeInTheDocument();
      });
    });

    it('displays locations when available', async () => {
      renderWithProviders(<AnecdotesPage />);
      await waitFor(() => {
        expect(screen.getByText('New York')).toBeInTheDocument();
        expect(screen.getByText('Miami Beach')).toBeInTheDocument();
      });
    });

    it('displays person links', async () => {
      renderWithProviders(<AnecdotesPage />);
      await waitFor(() => {
        const johnLinks = screen.getAllByRole('link', { name: 'John Doe' });
        expect(johnLinks.length).toBeGreaterThan(0);
        expect(screen.getByRole('link', { name: 'Jane Smith' })).toBeInTheDocument();
      });
    });

    it('displays tags', async () => {
      renderWithProviders(<AnecdotesPage />);
      await waitFor(() => {
        // Work tag appears on multiple anecdotes
        const workTags = screen.getAllByText('Work');
        expect(workTags.length).toBeGreaterThanOrEqual(1);
        expect(screen.getByText('Travel')).toBeInTheDocument();
        expect(screen.getByText('Summer')).toBeInTheDocument();
      });
    });
  });

  describe('empty state', () => {
    it('shows empty state when no anecdotes', async () => {
      server.use(
        http.get('/api/v1/anecdotes/', () => {
          return HttpResponse.json({ results: [] });
        })
      );

      renderWithProviders(<AnecdotesPage />);
      await waitFor(() => {
        expect(screen.getByText('No anecdotes yet')).toBeInTheDocument();
      });
    });

    it('shows add first anecdote button in empty state', async () => {
      server.use(
        http.get('/api/v1/anecdotes/', () => {
          return HttpResponse.json({ results: [] });
        })
      );

      renderWithProviders(<AnecdotesPage />);
      await waitFor(() => {
        expect(
          screen.getByRole('button', { name: /Add your first anecdote/i })
        ).toBeInTheDocument();
      });
    });

    it('shows helpful description in empty state', async () => {
      server.use(
        http.get('/api/v1/anecdotes/', () => {
          return HttpResponse.json({ results: [] });
        })
      );

      renderWithProviders(<AnecdotesPage />);
      await waitFor(() => {
        expect(
          screen.getByText(/Start capturing memories, jokes, and notes/i)
        ).toBeInTheDocument();
      });
    });
  });

  describe('type filter options', () => {
    it('shows all type filter options', async () => {
      renderWithProviders(<AnecdotesPage />);
      await waitFor(() => {
        expect(screen.getByRole('option', { name: 'All Types' })).toBeInTheDocument();
        expect(screen.getByRole('option', { name: 'Memory' })).toBeInTheDocument();
        expect(screen.getByRole('option', { name: 'Joke' })).toBeInTheDocument();
        expect(screen.getByRole('option', { name: 'Quote' })).toBeInTheDocument();
        expect(screen.getByRole('option', { name: 'Note' })).toBeInTheDocument();
      });
    });
  });
});
