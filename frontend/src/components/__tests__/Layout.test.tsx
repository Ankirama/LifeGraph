/**
 * Tests for Layout component.
 */

import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';
import { renderWithProviders } from '@/test/utils';
import { Layout } from '../Layout';

// Mock owner data
const mockOwner = {
  id: '123',
  first_name: 'Test',
  last_name: 'User',
  full_name: 'Test User',
  is_owner: true,
};

// MSW server setup
const server = setupServer(
  http.get('/api/v1/me/', () => {
    return HttpResponse.json(mockOwner);
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('Layout', () => {
  describe('sidebar navigation', () => {
    it('renders the sidebar with app name', async () => {
      renderWithProviders(<Layout />);
      expect(screen.getByText('LifeGraph')).toBeInTheDocument();
    });

    it('renders all navigation items', async () => {
      renderWithProviders(<Layout />);

      expect(screen.getByText('Dashboard')).toBeInTheDocument();
      expect(screen.getByText('People')).toBeInTheDocument();
      expect(screen.getByText('Relationships')).toBeInTheDocument();
      expect(screen.getByText('Graph')).toBeInTheDocument();
      expect(screen.getByText('Anecdotes')).toBeInTheDocument();
      expect(screen.getByText('Photos')).toBeInTheDocument();
      expect(screen.getByText('Groups')).toBeInTheDocument();
      expect(screen.getByText('Tags')).toBeInTheDocument();
      expect(screen.getByText('Export')).toBeInTheDocument();
      expect(screen.getByText('My Profile')).toBeInTheDocument();
      expect(screen.getByText('Settings')).toBeInTheDocument();
    });

    it('renders AI Chat navigation item', async () => {
      renderWithProviders(<Layout />);
      expect(screen.getByText('AI Chat')).toBeInTheDocument();
    });

    it('renders Smart Search navigation item', async () => {
      renderWithProviders(<Layout />);
      expect(screen.getByText('Smart Search')).toBeInTheDocument();
    });

    it('navigation links have correct hrefs', async () => {
      renderWithProviders(<Layout />);

      expect(screen.getByText('Dashboard').closest('a')).toHaveAttribute('href', '/');
      expect(screen.getByText('People').closest('a')).toHaveAttribute('href', '/people');
      expect(screen.getByText('Relationships').closest('a')).toHaveAttribute('href', '/relationships');
      expect(screen.getByText('Graph').closest('a')).toHaveAttribute('href', '/graph');
      expect(screen.getByText('Anecdotes').closest('a')).toHaveAttribute('href', '/anecdotes');
      expect(screen.getByText('Photos').closest('a')).toHaveAttribute('href', '/photos');
    });
  });

  describe('header', () => {
    it('renders the header', async () => {
      renderWithProviders(<Layout />);
      // GlobalSearch should be in the header
      expect(screen.getByRole('banner')).toBeInTheDocument();
    });

    it('displays user avatar with first initial', async () => {
      renderWithProviders(<Layout />);

      await waitFor(() => {
        expect(screen.getByText('T')).toBeInTheDocument(); // 'T' for 'Test'
      });
    });

    it('displays user name when loaded', async () => {
      renderWithProviders(<Layout />);

      await waitFor(() => {
        expect(screen.getByText('Test User')).toBeInTheDocument();
      });
    });

    it('shows fallback avatar when user not loaded', async () => {
      server.use(
        http.get('/api/v1/me/', () => {
          return HttpResponse.json(null, { status: 404 });
        })
      );

      renderWithProviders(<Layout />);

      // Should show 'U' for unknown/unauthorized
      await waitFor(() => {
        expect(screen.getByText('U')).toBeInTheDocument();
      });
    });
  });

  describe('active navigation state', () => {
    it('highlights active navigation item for root path', async () => {
      renderWithProviders(<Layout />, { initialEntries: ['/'] });

      const dashboardLink = screen.getByText('Dashboard').closest('a');
      expect(dashboardLink).toHaveClass('bg-primary');
    });

    it('highlights active navigation item for people page', async () => {
      renderWithProviders(<Layout />, { initialEntries: ['/people'] });

      const peopleLink = screen.getByText('People').closest('a');
      expect(peopleLink).toHaveClass('bg-primary');
    });

    it('does not highlight inactive navigation items', async () => {
      renderWithProviders(<Layout />, { initialEntries: ['/'] });

      const peopleLink = screen.getByText('People').closest('a');
      expect(peopleLink).not.toHaveClass('bg-primary');
    });
  });

  describe('main content area', () => {
    it('renders the main content area', async () => {
      renderWithProviders(<Layout />);
      expect(screen.getByRole('main')).toBeInTheDocument();
    });

    it('main content has proper overflow handling', async () => {
      renderWithProviders(<Layout />);
      const main = screen.getByRole('main');
      expect(main).toHaveClass('overflow-auto');
    });
  });
});
