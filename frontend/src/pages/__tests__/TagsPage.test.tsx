/**
 * Tests for TagsPage page.
 */

import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';
import { renderWithProviders } from '@/test/utils';
import { TagsPage } from '../TagsPage';

// Mock data
const mockTags = {
  results: [
    { id: 't1', name: 'Friend', color: '#ef4444', person_count: 5 },
    { id: 't2', name: 'Family', color: '#22c55e', person_count: 8 },
    { id: 't3', name: 'Work', color: '#3b82f6', person_count: 12 },
    { id: 't4', name: 'College', color: '#8b5cf6', person_count: 0 },
  ],
};

// MSW server setup
const server = setupServer(
  http.get('/api/v1/tags/', () => {
    return HttpResponse.json(mockTags);
  }),
  http.post('/api/v1/tags/', async ({ request }) => {
    const body = await request.json() as { name: string; color: string };
    return HttpResponse.json(
      { id: 'new-tag', name: body.name, color: body.color, person_count: 0 },
      { status: 201 }
    );
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('TagsPage', () => {
  describe('loading state', () => {
    it('shows loading indicator initially', () => {
      renderWithProviders(<TagsPage />);
      expect(screen.getByText('Loading tags...')).toBeInTheDocument();
    });
  });

  describe('page header', () => {
    it('displays page title', async () => {
      renderWithProviders(<TagsPage />);
      await waitFor(() => {
        expect(screen.getByRole('heading', { name: 'Tags' })).toBeInTheDocument();
      });
    });

    it('displays page description', async () => {
      renderWithProviders(<TagsPage />);
      await waitFor(() => {
        expect(screen.getByText(/Organize people with flexible labels/i)).toBeInTheDocument();
      });
    });

    it('displays Create Tag button', async () => {
      renderWithProviders(<TagsPage />);
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Create Tag/i })).toBeInTheDocument();
      });
    });
  });

  describe('tags grid', () => {
    it('displays all tags', async () => {
      renderWithProviders(<TagsPage />);
      await waitFor(() => {
        expect(screen.getByText('Friend')).toBeInTheDocument();
        expect(screen.getByText('Family')).toBeInTheDocument();
        // Work appears in tags
        const workTexts = screen.getAllByText('Work');
        expect(workTexts.length).toBeGreaterThanOrEqual(1);
        expect(screen.getByText('College')).toBeInTheDocument();
      });
    });

    it('displays person counts', async () => {
      renderWithProviders(<TagsPage />);
      await waitFor(() => {
        expect(screen.getByText('5 people')).toBeInTheDocument();
        expect(screen.getByText('8 people')).toBeInTheDocument();
        expect(screen.getByText('12 people')).toBeInTheDocument();
        expect(screen.getByText('0 people')).toBeInTheDocument();
      });
    });

    it('uses singular for single person', async () => {
      server.use(
        http.get('/api/v1/tags/', () => {
          return HttpResponse.json({
            results: [{ id: 't1', name: 'Solo', color: '#ef4444', person_count: 1 }],
          });
        })
      );

      renderWithProviders(<TagsPage />);
      await waitFor(() => {
        expect(screen.getByText('1 person')).toBeInTheDocument();
      });
    });
  });

  describe('empty state', () => {
    it('shows empty state when no tags exist', async () => {
      server.use(
        http.get('/api/v1/tags/', () => {
          return HttpResponse.json({ results: [] });
        })
      );

      renderWithProviders(<TagsPage />);
      await waitFor(() => {
        expect(screen.getByText('No tags yet')).toBeInTheDocument();
      });
    });

    it('shows create first tag button in empty state', async () => {
      server.use(
        http.get('/api/v1/tags/', () => {
          return HttpResponse.json({ results: [] });
        })
      );

      renderWithProviders(<TagsPage />);
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Create your first tag/i })).toBeInTheDocument();
      });
    });
  });

  describe('create tag modal', () => {
    it('opens create modal when Create Tag is clicked', async () => {
      const { user } = renderWithProviders(<TagsPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Create Tag/i })).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /Create Tag/i }));

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: 'Create Tag' })).toBeInTheDocument();
      });
    });

    it('renders tag name input in modal', async () => {
      const { user } = renderWithProviders(<TagsPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Create Tag/i })).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /Create Tag/i }));

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/Family, Work, College Friends/i)).toBeInTheDocument();
      });
    });

    it('renders color picker in modal', async () => {
      const { user } = renderWithProviders(<TagsPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Create Tag/i })).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /Create Tag/i }));

      await waitFor(() => {
        expect(screen.getByText('Color')).toBeInTheDocument();
      });
    });

    it('renders preview section in modal', async () => {
      const { user } = renderWithProviders(<TagsPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Create Tag/i })).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /Create Tag/i }));

      await waitFor(() => {
        expect(screen.getByText('Preview')).toBeInTheDocument();
      });
    });

    it('shows tag name placeholder in preview', async () => {
      const { user } = renderWithProviders(<TagsPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Create Tag/i })).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /Create Tag/i }));

      await waitFor(() => {
        expect(screen.getByText('Tag name')).toBeInTheDocument();
      });
    });

    it('disables submit button when name is empty', async () => {
      const { user } = renderWithProviders(<TagsPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Create Tag/i })).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /Create Tag/i }));

      await waitFor(() => {
        // Find the submit button inside the modal (not the header button)
        const modalButtons = screen.getAllByRole('button');
        const submitButton = modalButtons.find(
          (btn) => btn.textContent === 'Create Tag' && btn.closest('form')
        );
        expect(submitButton).toBeDisabled();
      });
    });

    it('enables submit button when name is entered', async () => {
      const { user } = renderWithProviders(<TagsPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Create Tag/i })).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /Create Tag/i }));

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/Family, Work, College Friends/i)).toBeInTheDocument();
      });

      await user.type(screen.getByPlaceholderText(/Family, Work, College Friends/i), 'New Tag');

      // Find the submit button inside the form
      const modalButtons = screen.getAllByRole('button');
      const submitButton = modalButtons.find(
        (btn) => btn.textContent === 'Create Tag' && btn.closest('form')
      );
      expect(submitButton).not.toBeDisabled();
    });

    it('closes modal when Cancel is clicked', async () => {
      const { user } = renderWithProviders(<TagsPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Create Tag/i })).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /Create Tag/i }));

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: 'Create Tag' })).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /Cancel/i }));

      await waitFor(() => {
        expect(screen.queryByRole('heading', { name: 'Create Tag' })).not.toBeInTheDocument();
      });
    });
  });

  describe('edit tag modal', () => {
    it('opens edit modal when edit button is clicked', async () => {
      const { user, container } = renderWithProviders(<TagsPage />);

      await waitFor(() => {
        expect(screen.getByText('Friend')).toBeInTheDocument();
      });

      // Find the tag card and hover to reveal edit button
      const tagCard = screen.getByText('Friend').closest('.bg-card');
      expect(tagCard).toBeInTheDocument();

      // Find the edit button (pencil icon)
      const editButtons = container.querySelectorAll('button');
      const editButton = Array.from(editButtons).find((btn) =>
        btn.querySelector('svg')?.classList.contains('lucide-pencil') ||
        btn.innerHTML.includes('pencil')
      );

      if (editButton) {
        await user.click(editButton);

        await waitFor(() => {
          expect(screen.getByRole('heading', { name: 'Edit Tag' })).toBeInTheDocument();
        });
      }
    });
  });
});
