/**
 * Tests for ExportPage page.
 */

import { describe, it, expect, beforeAll, afterAll, afterEach, vi } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';
import { renderWithProviders } from '@/test/utils';
import { ExportPage } from '../ExportPage';

// Mock data - matches getExportPreview API response
const mockPreviewData = {
  counts: {
    persons: 42,
    relationships: 58,
    relationship_types: 10,
    anecdotes: 127,
    photos: 23,
    tags: 15,
    groups: 8,
  },
  total_items: 283,
};

// MSW server setup
const server = setupServer(
  http.get('/api/v1/export/preview/', () => {
    return HttpResponse.json(mockPreviewData);
  }),
  http.get('/api/v1/export/', ({ request }) => {
    const url = new URL(request.url);
    const format = url.searchParams.get('format');

    if (format === 'json') {
      return HttpResponse.json({ persons: [], relationships: [] });
    } else {
      return new HttpResponse('id,first_name,last_name\n1,John,Doe', {
        headers: { 'Content-Type': 'text/csv' },
      });
    }
  })
);

// Mock URL.createObjectURL
const mockCreateObjectURL = vi.fn(() => 'blob:mock-url');
const mockRevokeObjectURL = vi.fn();

beforeAll(() => {
  server.listen();
  global.URL.createObjectURL = mockCreateObjectURL;
  global.URL.revokeObjectURL = mockRevokeObjectURL;
});
afterEach(() => {
  server.resetHandlers();
  vi.clearAllMocks();
});
afterAll(() => server.close());

describe('ExportPage', () => {
  describe('page header', () => {
    it('displays page title', async () => {
      renderWithProviders(<ExportPage />);
      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /Export Data/i })).toBeInTheDocument();
      });
    });

    it('displays page description', async () => {
      renderWithProviders(<ExportPage />);
      await waitFor(() => {
        expect(
          screen.getByText(/Export your data in JSON or CSV format for backup or migration/i)
        ).toBeInTheDocument();
      });
    });
  });

  describe('data summary', () => {
    it('displays data summary section', async () => {
      renderWithProviders(<ExportPage />);
      await waitFor(() => {
        expect(screen.getByText('Data Summary')).toBeInTheDocument();
      });
    });

    it('displays total items count', async () => {
      renderWithProviders(<ExportPage />);
      await waitFor(() => {
        expect(screen.getByText(/Total items:/)).toBeInTheDocument();
        expect(screen.getByText('283')).toBeInTheDocument();
      });
    });

    it('displays people count', async () => {
      renderWithProviders(<ExportPage />);
      await waitFor(() => {
        // People appears both in summary and entity buttons
        const peopleLabels = screen.getAllByText('People');
        expect(peopleLabels.length).toBeGreaterThan(0);
        expect(screen.getByText('42')).toBeInTheDocument();
      });
    });

    it('displays relationships count', async () => {
      renderWithProviders(<ExportPage />);
      await waitFor(() => {
        // Relationships appears both in summary and entity buttons
        const relationshipLabels = screen.getAllByText('Relationships');
        expect(relationshipLabels.length).toBeGreaterThan(0);
        expect(screen.getByText('58')).toBeInTheDocument();
      });
    });

    it('displays anecdotes count', async () => {
      renderWithProviders(<ExportPage />);
      await waitFor(() => {
        // Anecdotes appears both in summary and entity buttons
        const anecdoteLabels = screen.getAllByText('Anecdotes');
        expect(anecdoteLabels.length).toBeGreaterThan(0);
        expect(screen.getByText('127')).toBeInTheDocument();
      });
    });

    it('displays photos count', async () => {
      renderWithProviders(<ExportPage />);
      await waitFor(() => {
        // Photos appears both in summary and entity buttons
        const photoLabels = screen.getAllByText('Photos');
        expect(photoLabels.length).toBeGreaterThan(0);
        expect(screen.getByText('23')).toBeInTheDocument();
      });
    });
  });

  describe('entity selection (button-based)', () => {
    it('displays What to Export section', async () => {
      renderWithProviders(<ExportPage />);
      await waitFor(() => {
        expect(screen.getByText('What to Export')).toBeInTheDocument();
      });
    });

    it('shows All Data button', async () => {
      renderWithProviders(<ExportPage />);
      await waitFor(() => {
        expect(screen.getByText('All Data')).toBeInTheDocument();
        expect(screen.getByText('Complete export')).toBeInTheDocument();
      });
    });

    it('shows People entity button', async () => {
      renderWithProviders(<ExportPage />);
      await waitFor(() => {
        expect(screen.getByText('People')).toBeInTheDocument();
      });
    });

    it('shows Relationships entity button', async () => {
      renderWithProviders(<ExportPage />);
      await waitFor(() => {
        expect(screen.getByText('Relationships')).toBeInTheDocument();
      });
    });

    it('shows Anecdotes entity button', async () => {
      renderWithProviders(<ExportPage />);
      await waitFor(() => {
        expect(screen.getByText('Anecdotes')).toBeInTheDocument();
      });
    });

    it('shows Photos entity button', async () => {
      renderWithProviders(<ExportPage />);
      await waitFor(() => {
        expect(screen.getByText('Photos')).toBeInTheDocument();
      });
    });

    it('shows Tags entity button', async () => {
      renderWithProviders(<ExportPage />);
      await waitFor(() => {
        expect(screen.getByText('Tags')).toBeInTheDocument();
      });
    });

    it('shows Groups entity button', async () => {
      renderWithProviders(<ExportPage />);
      await waitFor(() => {
        expect(screen.getByText('Groups')).toBeInTheDocument();
      });
    });

    it('allows selecting entity buttons', async () => {
      const { user } = renderWithProviders(<ExportPage />);

      await waitFor(() => {
        expect(screen.getByText('People')).toBeInTheDocument();
      });

      // Find People button by text content
      const peopleButton = screen.getByText('People').closest('button');
      expect(peopleButton).toBeInTheDocument();

      if (peopleButton) {
        await user.click(peopleButton);
        // After clicking, the button should be selected (has border-primary class)
        expect(peopleButton).toHaveClass('border-primary');
      }
    });
  });

  describe('format selection', () => {
    it('displays Export Format section', async () => {
      renderWithProviders(<ExportPage />);
      await waitFor(() => {
        expect(screen.getByText('Export Format')).toBeInTheDocument();
      });
    });

    it('shows JSON format option', async () => {
      renderWithProviders(<ExportPage />);
      await waitFor(() => {
        // JSON appears in format selection and possibly in info section
        const jsonTexts = screen.getAllByText('JSON');
        expect(jsonTexts.length).toBeGreaterThan(0);
        expect(screen.getByText('Complete data with all relationships')).toBeInTheDocument();
      });
    });

    it('shows CSV format option', async () => {
      renderWithProviders(<ExportPage />);
      await waitFor(() => {
        // CSV appears in format selection and possibly in info section
        const csvTexts = screen.getAllByText('CSV');
        expect(csvTexts.length).toBeGreaterThan(0);
        expect(
          screen.getByText('Spreadsheet format (People, Relationships, Anecdotes)')
        ).toBeInTheDocument();
      });
    });

    it('allows selecting JSON format', async () => {
      const { user } = renderWithProviders(<ExportPage />);

      await waitFor(() => {
        const jsonTexts = screen.getAllByText('JSON');
        expect(jsonTexts.length).toBeGreaterThan(0);
      });

      // Find the JSON button in format selection (first one should be in export options)
      const jsonTexts = screen.getAllByText('JSON');
      const jsonButton = jsonTexts[0].closest('button');
      expect(jsonButton).toBeInTheDocument();

      if (jsonButton) {
        await user.click(jsonButton);
        // JSON should be selected (it's the default)
        expect(jsonButton).toHaveClass('border-primary');
      }
    });

    it('disables CSV when All Data is selected', async () => {
      renderWithProviders(<ExportPage />);

      await waitFor(() => {
        const csvTexts = screen.getAllByText('CSV');
        expect(csvTexts.length).toBeGreaterThan(0);
      });

      // All Data is selected by default, so CSV should be disabled
      // Find the CSV button in format selection (first one should be in export options)
      const csvTexts = screen.getAllByText('CSV');
      const csvButton = csvTexts[0].closest('button');
      expect(csvButton).toHaveAttribute('disabled');
    });
  });

  describe('export button', () => {
    it('displays export button', async () => {
      renderWithProviders(<ExportPage />);
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Download All Data as JSON/i })).toBeInTheDocument();
      });
    });

    it('button text changes based on selection', async () => {
      const { user } = renderWithProviders(<ExportPage />);

      await waitFor(() => {
        expect(screen.getByText('People')).toBeInTheDocument();
      });

      // Select People entity
      const peopleButton = screen.getByText('People').closest('button');
      if (peopleButton) {
        await user.click(peopleButton);
      }

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Download People as JSON/i })).toBeInTheDocument();
      });
    });
  });

  describe('export info section', () => {
    it('displays About Exports section', async () => {
      renderWithProviders(<ExportPage />);
      await waitFor(() => {
        expect(screen.getByText('About Exports')).toBeInTheDocument();
      });
    });

    it('shows JSON format explanation', async () => {
      renderWithProviders(<ExportPage />);
      await waitFor(() => {
        expect(
          screen.getByText(/exports include all data with complete metadata and relationships/i)
        ).toBeInTheDocument();
      });
    });

    it('shows CSV format explanation', async () => {
      renderWithProviders(<ExportPage />);
      await waitFor(() => {
        expect(
          screen.getByText(/exports are suitable for spreadsheet applications/i)
        ).toBeInTheDocument();
      });
    });
  });

  describe('loading state', () => {
    it('shows loading indicator while fetching preview', () => {
      renderWithProviders(<ExportPage />);
      // Initially shows loading state
      expect(document.querySelector('.animate-spin')).toBeInTheDocument();
    });
  });
});
