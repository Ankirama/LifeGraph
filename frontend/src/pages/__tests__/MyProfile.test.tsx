/**
 * Tests for MyProfile page.
 */

import { describe, it, expect, beforeAll, afterAll, afterEach, vi } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';
import { renderWithProviders } from '@/test/utils';
import { MyProfile } from '../MyProfile';

// Mock data
const mockMe = {
  id: 'me-1',
  first_name: 'Test',
  last_name: 'User',
  full_name: 'Test User',
  nickname: 'Testy',
  birthday: '1990-01-15',
  linkedin_url: 'https://linkedin.com/in/testuser',
  discord_id: 'testuser#1234',
  notes: 'This is my profile in the CRM.',
  avatar: null,
  is_owner: true,
};

// MSW server setup
const server = setupServer(
  http.get('/api/v1/me/', () => {
    return HttpResponse.json(mockMe);
  }),
  http.patch('/api/v1/me/', async ({ request }) => {
    const body = await request.json() as Record<string, unknown>;
    return HttpResponse.json({ ...mockMe, ...body });
  }),
  http.post('/api/v1/me/', async ({ request }) => {
    const body = await request.json() as Record<string, unknown>;
    return HttpResponse.json({ ...mockMe, ...body }, { status: 201 });
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('MyProfile', () => {
  describe('loading state', () => {
    it('shows loading indicator initially', () => {
      renderWithProviders(<MyProfile />);
      expect(screen.getByText('Loading...')).toBeInTheDocument();
    });
  });

  describe('view mode', () => {
    it('displays full name', async () => {
      renderWithProviders(<MyProfile />);
      await waitFor(() => {
        expect(screen.getByText('Test User')).toBeInTheDocument();
      });
    });

    it('displays nickname when available', async () => {
      renderWithProviders(<MyProfile />);
      await waitFor(() => {
        expect(screen.getByText('"Testy"')).toBeInTheDocument();
      });
    });

    it('displays birthday', async () => {
      renderWithProviders(<MyProfile />);
      await waitFor(() => {
        expect(screen.getByText(/January 15, 1990/)).toBeInTheDocument();
      });
    });

    it('displays LinkedIn link', async () => {
      renderWithProviders(<MyProfile />);
      await waitFor(() => {
        expect(screen.getByText('LinkedIn Profile')).toBeInTheDocument();
      });

      const link = screen.getByText('LinkedIn Profile').closest('a');
      expect(link).toHaveAttribute('href', 'https://linkedin.com/in/testuser');
    });

    it('displays Discord ID', async () => {
      renderWithProviders(<MyProfile />);
      await waitFor(() => {
        expect(screen.getByText(/testuser#1234/)).toBeInTheDocument();
      });
    });

    it('displays notes', async () => {
      renderWithProviders(<MyProfile />);
      await waitFor(() => {
        expect(screen.getByText('This is my profile in the CRM.')).toBeInTheDocument();
      });
    });

    it('displays Edit Profile button', async () => {
      renderWithProviders(<MyProfile />);
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Edit Profile/i })).toBeInTheDocument();
      });
    });
  });

  describe('edit mode', () => {
    it('opens edit mode when Edit Profile is clicked', async () => {
      const { user } = renderWithProviders(<MyProfile />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Edit Profile/i })).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /Edit Profile/i }));

      await waitFor(() => {
        expect(screen.getByText('Edit Your Profile')).toBeInTheDocument();
      });
    });

    it('pre-fills form with existing data', async () => {
      const { user } = renderWithProviders(<MyProfile />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Edit Profile/i })).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /Edit Profile/i }));

      await waitFor(() => {
        expect(screen.getByDisplayValue('Test')).toBeInTheDocument();
        expect(screen.getByDisplayValue('User')).toBeInTheDocument();
        expect(screen.getByDisplayValue('Testy')).toBeInTheDocument();
      });
    });

    it('shows Cancel button in edit mode', async () => {
      const { user } = renderWithProviders(<MyProfile />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Edit Profile/i })).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /Edit Profile/i }));

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Cancel/i })).toBeInTheDocument();
      });
    });

    it('shows Save Changes button in edit mode', async () => {
      const { user } = renderWithProviders(<MyProfile />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Edit Profile/i })).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /Edit Profile/i }));

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Save Changes/i })).toBeInTheDocument();
      });
    });

    it('returns to view mode when Cancel is clicked', async () => {
      const { user } = renderWithProviders(<MyProfile />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Edit Profile/i })).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /Edit Profile/i }));

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Cancel/i })).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /Cancel/i }));

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Edit Profile/i })).toBeInTheDocument();
      });
    });
  });

  describe('setup mode', () => {
    it('shows setup mode when no profile exists', async () => {
      server.use(
        http.get('/api/v1/me/', () => {
          return new HttpResponse(null, { status: 404 });
        })
      );

      renderWithProviders(<MyProfile />);
      await waitFor(() => {
        expect(screen.getByText('Set Up Your Profile')).toBeInTheDocument();
      });
    });

    it('shows Create Profile button in setup mode', async () => {
      server.use(
        http.get('/api/v1/me/', () => {
          return new HttpResponse(null, { status: 404 });
        })
      );

      renderWithProviders(<MyProfile />);
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Create Profile/i })).toBeInTheDocument();
      });
    });

    it('requires first name in setup mode', async () => {
      server.use(
        http.get('/api/v1/me/', () => {
          return new HttpResponse(null, { status: 404 });
        })
      );

      renderWithProviders(<MyProfile />);
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Create Profile/i })).toBeDisabled();
      });
    });
  });

  describe('form fields', () => {
    it('renders first name input', async () => {
      const { user } = renderWithProviders(<MyProfile />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Edit Profile/i })).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /Edit Profile/i }));

      await waitFor(() => {
        expect(screen.getByPlaceholderText('Your first name')).toBeInTheDocument();
      });
    });

    it('renders last name input', async () => {
      const { user } = renderWithProviders(<MyProfile />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Edit Profile/i })).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /Edit Profile/i }));

      await waitFor(() => {
        expect(screen.getByPlaceholderText('Your last name')).toBeInTheDocument();
      });
    });

    it('renders nickname input', async () => {
      const { user } = renderWithProviders(<MyProfile />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Edit Profile/i })).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /Edit Profile/i }));

      await waitFor(() => {
        expect(screen.getByPlaceholderText('Optional nickname')).toBeInTheDocument();
      });
    });

    it('renders birthday input', async () => {
      const { user } = renderWithProviders(<MyProfile />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Edit Profile/i })).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /Edit Profile/i }));

      await waitFor(() => {
        expect(screen.getByText('Birthday')).toBeInTheDocument();
      });
    });
  });

  describe('avatar', () => {
    it('displays initial when no avatar', async () => {
      renderWithProviders(<MyProfile />);
      await waitFor(() => {
        expect(screen.getByText('T')).toBeInTheDocument();
      });
    });

    it('displays avatar image when available', async () => {
      server.use(
        http.get('/api/v1/me/', () => {
          return HttpResponse.json({ ...mockMe, avatar: 'https://example.com/avatar.jpg' });
        })
      );

      renderWithProviders(<MyProfile />);
      await waitFor(() => {
        const avatar = screen.getByRole('img', { name: 'Test User' });
        expect(avatar).toHaveAttribute('src', 'https://example.com/avatar.jpg');
      });
    });
  });
});
