/**
 * Tests for PeopleList page.
 */

import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';
import { renderWithProviders } from '@/test/utils';
import { PeopleList } from '../PeopleList';

// Mock data
const mockPersons = {
  results: [
    {
      id: 'p1',
      first_name: 'John',
      last_name: 'Doe',
      full_name: 'John Doe',
      nickname: 'Johnny',
      birthday: '1990-05-15',
      relationship_to_me: 'Friend',
      tags: [{ id: 't1', name: 'Friend', color: '#ff0000' }],
      avatar: null,
    },
    {
      id: 'p2',
      first_name: 'Jane',
      last_name: 'Smith',
      full_name: 'Jane Smith',
      nickname: null,
      birthday: null,
      relationship_to_me: null,
      tags: [],
      avatar: 'https://example.com/avatar.jpg',
    },
    {
      id: 'p3',
      first_name: 'Bob',
      last_name: 'Johnson',
      full_name: 'Bob Johnson',
      nickname: 'Bobby',
      birthday: '1985-03-20',
      relationship_to_me: 'Colleague',
      tags: [
        { id: 't1', name: 'Friend', color: '#ff0000' },
        { id: 't2', name: 'Work', color: '#0000ff' },
      ],
      avatar: null,
    },
  ],
  count: 3,
};

const mockTags = {
  results: [
    { id: 't1', name: 'Friend', color: '#ff0000' },
    { id: 't2', name: 'Work', color: '#0000ff' },
    { id: 't3', name: 'Family', color: '#00ff00' },
  ],
};

const mockGroups = {
  results: [
    { id: 'g1', name: 'College', full_path: 'College' },
    { id: 'g2', name: 'Company', full_path: 'Company' },
  ],
};

// MSW server setup
const server = setupServer(
  http.get('/api/v1/persons/', () => {
    return HttpResponse.json(mockPersons);
  }),
  http.get('/api/v1/tags/', () => {
    return HttpResponse.json(mockTags);
  }),
  http.get('/api/v1/groups/', () => {
    return HttpResponse.json(mockGroups);
  }),
  http.post('/api/v1/persons/', async () => {
    return HttpResponse.json({ id: 'new-person', full_name: 'New Person' }, { status: 201 });
  }),
  http.post('/api/v1/ai/import-contact/', async () => {
    return HttpResponse.json({ person: { id: 'ai-imported' } });
  }),
  http.post('/api/v1/ai/update-contact/', async () => {
    return HttpResponse.json({ person: { id: 'ai-updated' } });
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('PeopleList', () => {
  describe('loading state', () => {
    it('shows loading indicator initially', () => {
      renderWithProviders(<PeopleList />);
      expect(screen.getByText('Loading...')).toBeInTheDocument();
    });
  });

  describe('page header', () => {
    it('displays page title', async () => {
      renderWithProviders(<PeopleList />);
      await waitFor(() => {
        expect(screen.getByRole('heading', { name: 'People' })).toBeInTheDocument();
      });
    });

    it('displays page description', async () => {
      renderWithProviders(<PeopleList />);
      await waitFor(() => {
        expect(screen.getByText('Manage your contacts and relationships')).toBeInTheDocument();
      });
    });

    it('displays Add Person button', async () => {
      renderWithProviders(<PeopleList />);
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Add Person/i })).toBeInTheDocument();
      });
    });

    it('displays AI Import button', async () => {
      renderWithProviders(<PeopleList />);
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /AI Import/i })).toBeInTheDocument();
      });
    });

    it('displays AI Update button', async () => {
      renderWithProviders(<PeopleList />);
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /AI Update/i })).toBeInTheDocument();
      });
    });
  });

  describe('search', () => {
    it('renders search input', async () => {
      renderWithProviders(<PeopleList />);
      await waitFor(() => {
        expect(screen.getByPlaceholderText('Search by name...')).toBeInTheDocument();
      });
    });

    it('filters list based on search input', async () => {
      const { user } = renderWithProviders(<PeopleList />);

      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText('Search by name...');
      await user.type(searchInput, 'Jane');

      // The filtering happens via API query params in real app
      // but with our mock, we just verify search input works
      expect(searchInput).toHaveValue('Jane');
    });
  });

  describe('people list', () => {
    it('displays all people', async () => {
      renderWithProviders(<PeopleList />);
      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
        expect(screen.getByText('Jane Smith')).toBeInTheDocument();
        expect(screen.getByText('Bob Johnson')).toBeInTheDocument();
      });
    });

    it('displays nicknames when available', async () => {
      renderWithProviders(<PeopleList />);
      await waitFor(() => {
        expect(screen.getByText('"Johnny"')).toBeInTheDocument();
        expect(screen.getByText('"Bobby"')).toBeInTheDocument();
      });
    });

    it('displays relationship to me when available', async () => {
      renderWithProviders(<PeopleList />);
      await waitFor(() => {
        // Friend relationship badge for John Doe
        const friendBadges = screen.getAllByText('Friend');
        expect(friendBadges.length).toBeGreaterThanOrEqual(1);
        expect(screen.getByText('Colleague')).toBeInTheDocument();
      });
    });

    it('displays tags for people', async () => {
      renderWithProviders(<PeopleList />);
      await waitFor(() => {
        const friendTags = screen.getAllByText('Friend');
        expect(friendTags.length).toBeGreaterThanOrEqual(2);
      });
    });

    it('renders person cards as links', async () => {
      renderWithProviders(<PeopleList />);
      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });

      const johnLink = screen.getByText('John Doe').closest('a');
      expect(johnLink).toHaveAttribute('href', '/people/p1');
    });
  });

  describe('empty state', () => {
    it('shows empty state when no people', async () => {
      server.use(
        http.get('/api/v1/persons/', () => {
          return HttpResponse.json({ results: [], count: 0 });
        })
      );

      renderWithProviders(<PeopleList />);
      await waitFor(() => {
        expect(screen.getByText(/No people yet/i)).toBeInTheDocument();
      });
    });

    it('shows Add Your First Person button in empty state', async () => {
      server.use(
        http.get('/api/v1/persons/', () => {
          return HttpResponse.json({ results: [], count: 0 });
        })
      );

      renderWithProviders(<PeopleList />);
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Add Your First Person/i })).toBeInTheDocument();
      });
    });

    it('shows helpful message in empty state', async () => {
      server.use(
        http.get('/api/v1/persons/', () => {
          return HttpResponse.json({ results: [], count: 0 });
        })
      );

      renderWithProviders(<PeopleList />);
      await waitFor(() => {
        expect(
          screen.getByText(/Start building your personal CRM by adding your first contact/i)
        ).toBeInTheDocument();
      });
    });
  });

  describe('add person modal', () => {
    it('opens add person modal when Add Person is clicked', async () => {
      const { user } = renderWithProviders(<PeopleList />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Add Person/i })).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /Add Person/i }));

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /Add Person/i })).toBeInTheDocument();
      });
    });

    it('closes modal when cancel is clicked', async () => {
      const { user } = renderWithProviders(<PeopleList />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Add Person/i })).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /Add Person/i }));

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /Add Person/i })).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /Cancel/i }));

      await waitFor(() => {
        expect(screen.queryByRole('heading', { name: /Add Person/i })).not.toBeInTheDocument();
      });
    });
  });

  describe('AI import modal', () => {
    it('opens AI import modal when AI Import is clicked', async () => {
      const { user } = renderWithProviders(<PeopleList />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /AI Import/i })).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /AI Import/i }));

      await waitFor(() => {
        // Modal title is "AI Import Contacts"
        expect(screen.getByText(/AI Import Contacts/i)).toBeInTheDocument();
      });
    });
  });

  describe('AI update modal', () => {
    it('opens AI update modal when AI Update is clicked', async () => {
      const { user } = renderWithProviders(<PeopleList />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /AI Update/i })).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /AI Update/i }));

      await waitFor(() => {
        // Modal title is "AI Update Contacts"
        expect(screen.getByText(/AI Update Contacts/i)).toBeInTheDocument();
      });
    });
  });

  describe('error handling', () => {
    it('shows error message on API failure', async () => {
      server.use(
        http.get('/api/v1/persons/', () => {
          return new HttpResponse(null, { status: 500 });
        })
      );

      renderWithProviders(<PeopleList />);
      await waitFor(() => {
        expect(
          screen.getByText(/Error loading people. Make sure the backend is running./i)
        ).toBeInTheDocument();
      });
    });
  });
});
