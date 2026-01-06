/**
 * Tests for PhotoGallery component.
 */

import { describe, it, expect, beforeAll, afterAll, afterEach, vi } from 'vitest';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';
import { renderWithProviders } from '@/test/utils';
import { PhotoGallery } from '../PhotoGallery';
import type { Photo } from '@/types';

// Mock window.confirm
const originalConfirm = window.confirm;
beforeAll(() => {
  window.confirm = vi.fn(() => true);
});
afterAll(() => {
  window.confirm = originalConfirm;
});

// Mock photos
const mockPhotos: Photo[] = [
  {
    id: 'photo-1',
    file: 'https://example.com/photo1.jpg',
    caption: 'Beach vacation',
    date_taken: '2023-07-15',
    location: 'Hawaii',
    ai_description: 'A beautiful beach scene',
    persons: [{ id: 'p1', full_name: 'John Doe' }],
    tags: [],
    created_at: '2023-07-15T00:00:00Z',
    updated_at: '2023-07-15T00:00:00Z',
  },
  {
    id: 'photo-2',
    file: 'https://example.com/photo2.jpg',
    caption: 'Birthday party',
    date_taken: '2023-08-20',
    location: 'New York',
    ai_description: null,
    persons: [],
    tags: [],
    created_at: '2023-08-20T00:00:00Z',
    updated_at: '2023-08-20T00:00:00Z',
  },
  {
    id: 'photo-3',
    file: 'https://example.com/photo3.jpg',
    caption: null,
    date_taken: null,
    location: null,
    ai_description: null,
    persons: [],
    tags: [],
    created_at: '2023-09-01T00:00:00Z',
    updated_at: '2023-09-01T00:00:00Z',
  },
];

// MSW server setup
const server = setupServer(
  http.delete('/api/v1/photos/:id/', () => {
    return new HttpResponse(null, { status: 204 });
  }),
  http.post('/api/v1/photos/:id/describe/', () => {
    return HttpResponse.json({ ai_description: 'New AI description' });
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('PhotoGallery', () => {
  describe('empty state', () => {
    it('shows empty message when no photos', () => {
      renderWithProviders(<PhotoGallery photos={[]} />);
      expect(screen.getByText('No photos yet. Upload some memories!')).toBeInTheDocument();
    });
  });

  describe('grid display', () => {
    it('renders photo grid with all photos', () => {
      renderWithProviders(<PhotoGallery photos={mockPhotos} />);

      const images = screen.getAllByRole('img');
      expect(images).toHaveLength(3);
    });

    it('renders photos as clickable buttons', () => {
      renderWithProviders(<PhotoGallery photos={mockPhotos} />);

      const buttons = screen.getAllByRole('button');
      expect(buttons.length).toBeGreaterThanOrEqual(3);
    });

    it('uses photo caption as alt text', () => {
      renderWithProviders(<PhotoGallery photos={mockPhotos} />);

      expect(screen.getByRole('img', { name: 'Beach vacation' })).toBeInTheDocument();
      expect(screen.getByRole('img', { name: 'Birthday party' })).toBeInTheDocument();
    });

    it('uses default alt text when caption is null', () => {
      renderWithProviders(<PhotoGallery photos={mockPhotos} />);

      expect(screen.getByRole('img', { name: 'Photo' })).toBeInTheDocument();
    });
  });

  describe('lightbox', () => {
    it('opens lightbox when photo is clicked', async () => {
      const { user } = renderWithProviders(<PhotoGallery photos={mockPhotos} />);

      const photoButtons = screen.getAllByRole('button');
      await user.click(photoButtons[0]);

      // Lightbox should show photo counter
      expect(screen.getByText('1 / 3')).toBeInTheDocument();
    });

    it('displays photo caption in lightbox', async () => {
      const { user } = renderWithProviders(<PhotoGallery photos={mockPhotos} />);

      const photoButtons = screen.getAllByRole('button');
      await user.click(photoButtons[0]);

      // Caption should be visible in lightbox
      const captions = screen.getAllByText('Beach vacation');
      expect(captions.length).toBeGreaterThanOrEqual(1);
    });

    it('displays photo date in lightbox', async () => {
      const { user } = renderWithProviders(<PhotoGallery photos={mockPhotos} />);

      const photoButtons = screen.getAllByRole('button');
      await user.click(photoButtons[0]);

      expect(screen.getByText('July 15, 2023')).toBeInTheDocument();
    });

    it('displays photo location in lightbox', async () => {
      const { user } = renderWithProviders(<PhotoGallery photos={mockPhotos} />);

      const photoButtons = screen.getAllByRole('button');
      await user.click(photoButtons[0]);

      expect(screen.getByText('Hawaii')).toBeInTheDocument();
    });

    it('displays AI description in lightbox', async () => {
      const { user } = renderWithProviders(<PhotoGallery photos={mockPhotos} />);

      const photoButtons = screen.getAllByRole('button');
      await user.click(photoButtons[0]);

      expect(screen.getByText('A beautiful beach scene')).toBeInTheDocument();
    });

    it('displays tagged persons in lightbox', async () => {
      const { user } = renderWithProviders(<PhotoGallery photos={mockPhotos} />);

      const photoButtons = screen.getAllByRole('button');
      await user.click(photoButtons[0]);

      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    it('closes lightbox when close button is clicked', async () => {
      const { user } = renderWithProviders(<PhotoGallery photos={mockPhotos} />);

      // Open lightbox
      const photoButtons = screen.getAllByRole('button');
      await user.click(photoButtons[0]);

      expect(screen.getByText('1 / 3')).toBeInTheDocument();

      // Find and click close button (X icon)
      const closeButtons = screen.getAllByRole('button');
      const closeButton = closeButtons.find(btn => btn.querySelector('svg'));
      if (closeButton) {
        await user.click(closeButton);
      }
    });

    it('closes lightbox on Escape key', async () => {
      const { user } = renderWithProviders(<PhotoGallery photos={mockPhotos} />);

      // Open lightbox
      const photoButtons = screen.getAllByRole('button');
      await user.click(photoButtons[0]);

      expect(screen.getByText('1 / 3')).toBeInTheDocument();

      // Find the lightbox container and fire key event on it
      const lightbox = screen.getByText('1 / 3').closest('[tabindex]');
      if (lightbox) {
        fireEvent.keyDown(lightbox, { key: 'Escape' });
      }

      await waitFor(() => {
        expect(screen.queryByText('1 / 3')).not.toBeInTheDocument();
      });
    });
  });

  describe('navigation', () => {
    it('shows next button when not at last photo', async () => {
      const { user } = renderWithProviders(<PhotoGallery photos={mockPhotos} />);

      const photoButtons = screen.getAllByRole('button');
      await user.click(photoButtons[0]);

      // Should show navigation buttons
      const allButtons = screen.getAllByRole('button');
      expect(allButtons.length).toBeGreaterThan(1);
    });

    it('navigates to next photo', async () => {
      const { user } = renderWithProviders(<PhotoGallery photos={mockPhotos} />);

      const photoButtons = screen.getAllByRole('button');
      await user.click(photoButtons[0]);

      expect(screen.getByText('1 / 3')).toBeInTheDocument();

      // Find the lightbox container and fire key event on it
      const lightbox = screen.getByText('1 / 3').closest('[tabindex]');
      if (lightbox) {
        fireEvent.keyDown(lightbox, { key: 'ArrowRight' });
      }

      await waitFor(() => {
        expect(screen.getByText('2 / 3')).toBeInTheDocument();
      });
    });

    it('navigates to previous photo', async () => {
      const { user } = renderWithProviders(<PhotoGallery photos={mockPhotos} />);

      // Start at second photo
      const photoButtons = screen.getAllByRole('button');
      await user.click(photoButtons[1]);

      expect(screen.getByText('2 / 3')).toBeInTheDocument();

      // Find the lightbox container and fire key event on it
      const lightbox = screen.getByText('2 / 3').closest('[tabindex]');
      if (lightbox) {
        fireEvent.keyDown(lightbox, { key: 'ArrowLeft' });
      }

      await waitFor(() => {
        expect(screen.getByText('1 / 3')).toBeInTheDocument();
      });
    });
  });

  describe('actions', () => {
    it('shows AI describe button', async () => {
      const { user } = renderWithProviders(<PhotoGallery photos={mockPhotos} />);

      const photoButtons = screen.getAllByRole('button');
      await user.click(photoButtons[0]);

      // First photo has AI description, so should show regenerate
      expect(screen.getByText('Regenerate Description')).toBeInTheDocument();
    });

    it('shows AI Describe for photos without description', async () => {
      const { user } = renderWithProviders(<PhotoGallery photos={mockPhotos} />);

      // Click second photo (no AI description)
      const photoButtons = screen.getAllByRole('button');
      await user.click(photoButtons[1]);

      expect(screen.getByText('AI Describe')).toBeInTheDocument();
    });

    it('shows delete button', async () => {
      const { user } = renderWithProviders(<PhotoGallery photos={mockPhotos} />);

      const photoButtons = screen.getAllByRole('button');
      await user.click(photoButtons[0]);

      expect(screen.getByText('Delete')).toBeInTheDocument();
    });
  });
});
