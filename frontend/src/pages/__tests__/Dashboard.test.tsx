/**
 * Tests for Dashboard page.
 */

import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';
import { renderWithProviders } from '@/test/utils';
import { Dashboard } from '../Dashboard';

// Mock data - matches getDashboard API response
const mockDashboardData = {
  stats: {
    total_persons: 42,
    total_relationships: 58,
    total_anecdotes: 127,
    total_photos: 23,
  },
  upcoming_birthdays: [
    {
      id: 'p1',
      full_name: 'John Smith',
      date: '2024-02-15',
      turning_age: 35,
      days_until: 3,
    },
    {
      id: 'p2',
      full_name: 'Jane Doe',
      date: '2024-02-20',
      turning_age: 40,
      days_until: 8,
    },
  ],
  recent_anecdotes: [
    {
      id: 'a1',
      title: 'Funny story',
      content: 'Had a great laugh at dinner',
      anecdote_type: 'memory',
      persons: ['Bob Johnson'],
    },
    {
      id: 'a2',
      title: null,
      content: 'Important meeting notes',
      anecdote_type: 'note',
      persons: ['Alice Brown'],
    },
  ],
  recent_persons: [
    {
      id: 'p3',
      full_name: 'New Person',
      relationship_to_me: 'Friend',
    },
  ],
  relationship_distribution: [
    { name: 'Friend', count: 20 },
    { name: 'Family', count: 15 },
    { name: 'Colleague', count: 10 },
  ],
};

// MSW server setup
const server = setupServer(
  http.get('/api/v1/dashboard/', () => {
    return HttpResponse.json(mockDashboardData);
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('Dashboard', () => {
  describe('loading state', () => {
    it('shows loading indicator initially', () => {
      renderWithProviders(<Dashboard />);
      expect(screen.getByText('Loading...')).toBeInTheDocument();
    });
  });

  describe('stats display', () => {
    it('displays total people count', async () => {
      renderWithProviders(<Dashboard />);
      await waitFor(() => {
        expect(screen.getByText('42')).toBeInTheDocument();
      });
      expect(screen.getByText('People')).toBeInTheDocument();
    });

    it('displays total relationships count', async () => {
      renderWithProviders(<Dashboard />);
      await waitFor(() => {
        expect(screen.getByText('58')).toBeInTheDocument();
      });
      expect(screen.getByText('Relationships')).toBeInTheDocument();
    });

    it('displays total anecdotes count', async () => {
      renderWithProviders(<Dashboard />);
      await waitFor(() => {
        expect(screen.getByText('127')).toBeInTheDocument();
      });
      expect(screen.getByText('Anecdotes')).toBeInTheDocument();
    });

    it('displays total photos count', async () => {
      renderWithProviders(<Dashboard />);
      await waitFor(() => {
        expect(screen.getByText('23')).toBeInTheDocument();
      });
      expect(screen.getByText('Photos')).toBeInTheDocument();
    });
  });

  describe('upcoming birthdays', () => {
    it('displays section title', async () => {
      renderWithProviders(<Dashboard />);
      await waitFor(() => {
        expect(screen.getByText('Upcoming Birthdays')).toBeInTheDocument();
      });
    });

    it('displays upcoming birthday names', async () => {
      renderWithProviders(<Dashboard />);
      await waitFor(() => {
        expect(screen.getByText('John Smith')).toBeInTheDocument();
        expect(screen.getByText('Jane Doe')).toBeInTheDocument();
      });
    });

    it('displays days until birthday', async () => {
      renderWithProviders(<Dashboard />);
      await waitFor(() => {
        expect(screen.getByText('In 3 days')).toBeInTheDocument();
        expect(screen.getByText('In 8 days')).toBeInTheDocument();
      });
    });

    it('shows empty state when no upcoming birthdays', async () => {
      server.use(
        http.get('/api/v1/dashboard/', () => {
          return HttpResponse.json({
            ...mockDashboardData,
            upcoming_birthdays: [],
          });
        })
      );

      renderWithProviders(<Dashboard />);
      await waitFor(() => {
        expect(screen.getByText(/No upcoming birthdays in the next 30 days/i)).toBeInTheDocument();
      });
    });
  });

  describe('recent anecdotes', () => {
    it('displays section title', async () => {
      renderWithProviders(<Dashboard />);
      await waitFor(() => {
        expect(screen.getByText('Recent Anecdotes')).toBeInTheDocument();
      });
    });

    it('displays anecdote titles', async () => {
      renderWithProviders(<Dashboard />);
      await waitFor(() => {
        expect(screen.getByText('Funny story')).toBeInTheDocument();
      });
    });

    it('displays anecdote content', async () => {
      renderWithProviders(<Dashboard />);
      await waitFor(() => {
        expect(screen.getByText('Had a great laugh at dinner')).toBeInTheDocument();
      });
    });

    it('displays person names with anecdotes', async () => {
      renderWithProviders(<Dashboard />);
      await waitFor(() => {
        expect(screen.getByText('About: Bob Johnson')).toBeInTheDocument();
      });
    });

    it('displays anecdote types', async () => {
      renderWithProviders(<Dashboard />);
      await waitFor(() => {
        expect(screen.getByText('memory')).toBeInTheDocument();
        expect(screen.getByText('note')).toBeInTheDocument();
      });
    });

    it('shows empty state when no recent anecdotes', async () => {
      server.use(
        http.get('/api/v1/dashboard/', () => {
          return HttpResponse.json({
            ...mockDashboardData,
            recent_anecdotes: [],
          });
        })
      );

      renderWithProviders(<Dashboard />);
      await waitFor(() => {
        expect(
          screen.getByText(/No anecdotes yet. Start by adding memories about your contacts!/i)
        ).toBeInTheDocument();
      });
    });
  });

  describe('recently added people', () => {
    it('displays section title', async () => {
      renderWithProviders(<Dashboard />);
      await waitFor(() => {
        expect(screen.getByText('Recently Added')).toBeInTheDocument();
      });
    });

    it('displays recently added person names', async () => {
      renderWithProviders(<Dashboard />);
      await waitFor(() => {
        expect(screen.getByText('New Person')).toBeInTheDocument();
      });
    });

    it('displays relationship info', async () => {
      renderWithProviders(<Dashboard />);
      await waitFor(() => {
        // "Friend" appears in recent persons and relationship distribution
        const friendTexts = screen.getAllByText('Friend');
        expect(friendTexts.length).toBeGreaterThan(0);
      });
    });
  });

  describe('relationship distribution', () => {
    it('displays section title', async () => {
      renderWithProviders(<Dashboard />);
      await waitFor(() => {
        expect(screen.getByText('Relationship Types')).toBeInTheDocument();
      });
    });

    it('displays relationship type names', async () => {
      renderWithProviders(<Dashboard />);
      await waitFor(() => {
        // Note: Friend is also used in recent persons section
        const friendElements = screen.getAllByText('Friend');
        expect(friendElements.length).toBeGreaterThanOrEqual(1);
        expect(screen.getByText('Family')).toBeInTheDocument();
        expect(screen.getByText('Colleague')).toBeInTheDocument();
      });
    });

    it('displays relationship counts', async () => {
      renderWithProviders(<Dashboard />);
      await waitFor(() => {
        expect(screen.getByText('20')).toBeInTheDocument();
        expect(screen.getByText('15')).toBeInTheDocument();
        expect(screen.getByText('10')).toBeInTheDocument();
      });
    });
  });

  describe('navigation', () => {
    it('renders links to people', async () => {
      renderWithProviders(<Dashboard />);
      await waitFor(() => {
        expect(screen.getByText('John Smith')).toBeInTheDocument();
      });
      // Birthday links should be present
      const johnLink = screen.getByText('John Smith').closest('a');
      expect(johnLink).toHaveAttribute('href', '/people/p1');
    });

    it('displays Add Person link', async () => {
      renderWithProviders(<Dashboard />);
      await waitFor(() => {
        expect(screen.getByText('Add Person')).toBeInTheDocument();
      });
    });

    it('displays AI Import link', async () => {
      renderWithProviders(<Dashboard />);
      await waitFor(() => {
        expect(screen.getByText('AI Import')).toBeInTheDocument();
      });
    });
  });

  describe('error handling', () => {
    it('displays error message on API failure', async () => {
      server.use(
        http.get('/api/v1/dashboard/', () => {
          return new HttpResponse(null, { status: 500 });
        })
      );

      renderWithProviders(<Dashboard />);
      await waitFor(() => {
        expect(
          screen.getByText(/Failed to load dashboard. Make sure the backend is running./i)
        ).toBeInTheDocument();
      });
    });
  });
});
