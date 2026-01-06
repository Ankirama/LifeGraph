/**
 * Tests for GroupsPage page.
 */

import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';
import { renderWithProviders } from '@/test/utils';
import { GroupsPage } from '../GroupsPage';

// Mock data
const mockGroups = {
  results: [
    {
      id: 'g1',
      name: 'Work',
      description: 'Work contacts',
      color: '#3b82f6',
      parent: null,
      full_path: 'Work',
      children_count: 2,
    },
    {
      id: 'g2',
      name: 'Engineering',
      description: 'Engineering team',
      color: '#22c55e',
      parent: 'g1',
      full_path: 'Work / Engineering',
      children_count: 0,
    },
    {
      id: 'g3',
      name: 'Sales',
      description: '',
      color: '#ef4444',
      parent: 'g1',
      full_path: 'Work / Sales',
      children_count: 0,
    },
    {
      id: 'g4',
      name: 'Family',
      description: 'Family members',
      color: '#8b5cf6',
      parent: null,
      full_path: 'Family',
      children_count: 0,
    },
  ],
};

// MSW server setup
const server = setupServer(
  http.get('/api/v1/groups/', () => {
    return HttpResponse.json(mockGroups);
  }),
  http.post('/api/v1/groups/', async ({ request }) => {
    const body = (await request.json()) as { name: string; color: string };
    return HttpResponse.json(
      { id: 'new-group', name: body.name, color: body.color, children_count: 0 },
      { status: 201 }
    );
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('GroupsPage', () => {
  describe('loading state', () => {
    it('shows loading indicator initially', () => {
      renderWithProviders(<GroupsPage />);
      expect(screen.getByText('Loading groups...')).toBeInTheDocument();
    });
  });

  describe('page header', () => {
    it('displays page title', async () => {
      renderWithProviders(<GroupsPage />);
      await waitFor(() => {
        expect(screen.getByRole('heading', { name: 'Groups' })).toBeInTheDocument();
      });
    });

    it('displays page description', async () => {
      renderWithProviders(<GroupsPage />);
      await waitFor(() => {
        expect(
          screen.getByText(/Organize people into hierarchical categories/i)
        ).toBeInTheDocument();
      });
    });

    it('displays Create Group button', async () => {
      renderWithProviders(<GroupsPage />);
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Create Group/i })).toBeInTheDocument();
      });
    });
  });

  describe('groups tree', () => {
    it('displays root groups', async () => {
      renderWithProviders(<GroupsPage />);
      await waitFor(() => {
        expect(screen.getByText('Work')).toBeInTheDocument();
        expect(screen.getByText('Family')).toBeInTheDocument();
      });
    });

    it('displays child groups under parents', async () => {
      renderWithProviders(<GroupsPage />);
      await waitFor(() => {
        expect(screen.getByText('Engineering')).toBeInTheDocument();
        expect(screen.getByText('Sales')).toBeInTheDocument();
      });
    });

    it('displays group descriptions', async () => {
      renderWithProviders(<GroupsPage />);
      await waitFor(() => {
        expect(screen.getByText('Work contacts')).toBeInTheDocument();
        expect(screen.getByText('Engineering team')).toBeInTheDocument();
      });
    });

    it('displays subgroup counts', async () => {
      renderWithProviders(<GroupsPage />);
      await waitFor(() => {
        expect(screen.getByText('(2 subgroups)')).toBeInTheDocument();
      });
    });
  });

  describe('empty state', () => {
    it('shows empty state when no groups exist', async () => {
      server.use(
        http.get('/api/v1/groups/', () => {
          return HttpResponse.json({ results: [] });
        })
      );

      renderWithProviders(<GroupsPage />);
      await waitFor(() => {
        expect(screen.getByText('No groups yet')).toBeInTheDocument();
      });
    });

    it('shows create first group button in empty state', async () => {
      server.use(
        http.get('/api/v1/groups/', () => {
          return HttpResponse.json({ results: [] });
        })
      );

      renderWithProviders(<GroupsPage />);
      await waitFor(() => {
        expect(
          screen.getByRole('button', { name: /Create your first group/i })
        ).toBeInTheDocument();
      });
    });
  });

  describe('create group modal', () => {
    it('opens create modal when Create Group is clicked', async () => {
      const { user } = renderWithProviders(<GroupsPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Create Group/i })).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /Create Group/i }));

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: 'Create Group' })).toBeInTheDocument();
      });
    });

    it('renders group name input in modal', async () => {
      const { user } = renderWithProviders(<GroupsPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Create Group/i })).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /Create Group/i }));

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/Work, Family, School/i)).toBeInTheDocument();
      });
    });

    it('renders description textarea in modal', async () => {
      const { user } = renderWithProviders(<GroupsPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Create Group/i })).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /Create Group/i }));

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/Optional description/i)).toBeInTheDocument();
      });
    });

    it('renders color picker in modal', async () => {
      const { user } = renderWithProviders(<GroupsPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Create Group/i })).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /Create Group/i }));

      await waitFor(() => {
        expect(screen.getByText('Color')).toBeInTheDocument();
      });
    });

    it('renders parent group selector when groups exist', async () => {
      const { user } = renderWithProviders(<GroupsPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Create Group/i })).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /Create Group/i }));

      await waitFor(() => {
        expect(screen.getByText('Parent Group (optional)')).toBeInTheDocument();
        expect(screen.getByText('No parent (top-level group)')).toBeInTheDocument();
      });
    });

    it('disables submit button when name is empty', async () => {
      const { user } = renderWithProviders(<GroupsPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Create Group/i })).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /Create Group/i }));

      await waitFor(() => {
        // Find the submit button inside the form
        const modalButtons = screen.getAllByRole('button');
        const submitButton = modalButtons.find(
          (btn) => btn.textContent === 'Create Group' && btn.closest('form')
        );
        expect(submitButton).toBeDisabled();
      });
    });

    it('enables submit button when name is entered', async () => {
      const { user } = renderWithProviders(<GroupsPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Create Group/i })).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /Create Group/i }));

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/Work, Family, School/i)).toBeInTheDocument();
      });

      await user.type(screen.getByPlaceholderText(/Work, Family, School/i), 'New Group');

      const modalButtons = screen.getAllByRole('button');
      const submitButton = modalButtons.find(
        (btn) => btn.textContent === 'Create Group' && btn.closest('form')
      );
      expect(submitButton).not.toBeDisabled();
    });

    it('closes modal when Cancel is clicked', async () => {
      const { user } = renderWithProviders(<GroupsPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Create Group/i })).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /Create Group/i }));

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: 'Create Group' })).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /Cancel/i }));

      await waitFor(() => {
        expect(screen.queryByRole('heading', { name: 'Create Group' })).not.toBeInTheDocument();
      });
    });
  });

  describe('group actions', () => {
    it('displays expand/collapse button for parent groups', async () => {
      const { container } = renderWithProviders(<GroupsPage />);

      await waitFor(() => {
        expect(screen.getByText('Work')).toBeInTheDocument();
      });

      // The Work group should have an expand/collapse button
      const chevronButtons = container.querySelectorAll('svg.lucide-chevron-right');
      expect(chevronButtons.length).toBeGreaterThan(0);
    });
  });

  describe('hierarchical display', () => {
    it('shows subgroups under their parent groups', async () => {
      renderWithProviders(<GroupsPage />);

      await waitFor(() => {
        // All groups should be visible since they're expanded by default
        expect(screen.getByText('Work')).toBeInTheDocument();
        expect(screen.getByText('Engineering')).toBeInTheDocument();
        expect(screen.getByText('Sales')).toBeInTheDocument();
        expect(screen.getByText('Family')).toBeInTheDocument();
      });
    });
  });
});
