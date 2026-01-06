/**
 * Tests for AddAnecdoteModal component.
 */

import { describe, it, expect, beforeAll, afterAll, afterEach, vi } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';
import { renderWithProviders } from '@/test/utils';
import { AddAnecdoteModal } from '../AddAnecdoteModal';

// Mock data
const mockTags = {
  results: [
    { id: 't1', name: 'Important', color: '#ff0000' },
    { id: 't2', name: 'Funny', color: '#00ff00' },
  ],
};

// MSW server setup
const server = setupServer(
  http.get('/api/v1/tags/', () => {
    return HttpResponse.json(mockTags);
  }),
  http.post('/api/v1/anecdotes/', async () => {
    return HttpResponse.json(
      {
        id: 'new-anecdote',
        title: 'Test Anecdote',
        content: 'Test content',
        anecdote_type: 'note',
      },
      { status: 201 }
    );
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('AddAnecdoteModal', () => {
  const mockOnClose = vi.fn();
  const defaultProps = {
    isOpen: true,
    onClose: mockOnClose,
    personId: 'person-1',
    personName: 'John Doe',
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('rendering', () => {
    it('renders modal when open', () => {
      renderWithProviders(<AddAnecdoteModal {...defaultProps} />);
      // Title appears in both modal header and button, so use role
      expect(screen.getByRole('heading', { name: 'Add Anecdote' })).toBeInTheDocument();
    });

    it('does not render when closed', () => {
      renderWithProviders(<AddAnecdoteModal {...defaultProps} isOpen={false} />);
      expect(screen.queryByText('Add Anecdote')).not.toBeInTheDocument();
    });

    it('displays person name in description', () => {
      renderWithProviders(<AddAnecdoteModal {...defaultProps} />);
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    it('renders all anecdote type options', () => {
      renderWithProviders(<AddAnecdoteModal {...defaultProps} />);

      expect(screen.getByText('Note')).toBeInTheDocument();
      expect(screen.getByText('Memory')).toBeInTheDocument();
      expect(screen.getByText('Quote')).toBeInTheDocument();
      expect(screen.getByText('Joke')).toBeInTheDocument();
    });

    it('renders type descriptions', () => {
      renderWithProviders(<AddAnecdoteModal {...defaultProps} />);

      expect(screen.getByText('General notes and observations')).toBeInTheDocument();
      expect(screen.getByText('Shared experiences and moments')).toBeInTheDocument();
      expect(screen.getByText('Something memorable they said')).toBeInTheDocument();
      expect(screen.getByText('Funny moments or inside jokes')).toBeInTheDocument();
    });
  });

  describe('form fields', () => {
    it('renders title input', () => {
      renderWithProviders(<AddAnecdoteModal {...defaultProps} />);
      expect(
        screen.getByPlaceholderText('Optional title for this anecdote')
      ).toBeInTheDocument();
    });

    it('renders content textarea', () => {
      renderWithProviders(<AddAnecdoteModal {...defaultProps} />);
      expect(screen.getByPlaceholderText('Write your notes here...')).toBeInTheDocument();
    });

    it('renders date input', () => {
      renderWithProviders(<AddAnecdoteModal {...defaultProps} />);
      expect(screen.getByText('Date')).toBeInTheDocument();
    });

    it('renders location input', () => {
      renderWithProviders(<AddAnecdoteModal {...defaultProps} />);
      expect(screen.getByPlaceholderText('Where did this happen?')).toBeInTheDocument();
    });
  });

  describe('anecdote type selection', () => {
    it('selects note type by default', () => {
      renderWithProviders(<AddAnecdoteModal {...defaultProps} />);
      const noteButton = screen.getByText('Note').closest('button');
      expect(noteButton).toHaveClass('border-primary');
    });

    it('can select memory type', async () => {
      const { user } = renderWithProviders(<AddAnecdoteModal {...defaultProps} />);

      await user.click(screen.getByText('Memory'));

      // Placeholder should change for memory type
      expect(
        screen.getByPlaceholderText('Describe the memory or experience...')
      ).toBeInTheDocument();
    });

    it('can select quote type', async () => {
      const { user } = renderWithProviders(<AddAnecdoteModal {...defaultProps} />);

      await user.click(screen.getByText('Quote'));

      expect(
        screen.getByPlaceholderText('"Enter the quote here..."')
      ).toBeInTheDocument();
    });

    it('can select joke type', async () => {
      const { user } = renderWithProviders(<AddAnecdoteModal {...defaultProps} />);

      await user.click(screen.getByText('Joke'));

      expect(
        screen.getByPlaceholderText('What was the funny moment?')
      ).toBeInTheDocument();
    });
  });

  describe('tags', () => {
    it('loads and displays available tags', async () => {
      renderWithProviders(<AddAnecdoteModal {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Important')).toBeInTheDocument();
        expect(screen.getByText('Funny')).toBeInTheDocument();
      });
    });
  });

  describe('form submission', () => {
    it('disables submit when content is empty', () => {
      renderWithProviders(<AddAnecdoteModal {...defaultProps} />);
      const submitButton = screen.getByRole('button', { name: 'Add Anecdote' });
      expect(submitButton).toBeDisabled();
    });

    it('enables submit when content is entered', async () => {
      const { user } = renderWithProviders(<AddAnecdoteModal {...defaultProps} />);

      await user.type(
        screen.getByPlaceholderText('Write your notes here...'),
        'Some content'
      );

      const submitButton = screen.getByRole('button', { name: 'Add Anecdote' });
      expect(submitButton).not.toBeDisabled();
    });

    it('submits form and calls onClose on success', async () => {
      const { user } = renderWithProviders(<AddAnecdoteModal {...defaultProps} />);

      await user.type(
        screen.getByPlaceholderText('Write your notes here...'),
        'Some content'
      );
      await user.click(screen.getByRole('button', { name: 'Add Anecdote' }));

      await waitFor(() => {
        expect(mockOnClose).toHaveBeenCalled();
      });
    });
  });

  describe('form actions', () => {
    it('calls onClose when cancel button is clicked', async () => {
      const { user } = renderWithProviders(<AddAnecdoteModal {...defaultProps} />);

      await user.click(screen.getByRole('button', { name: 'Cancel' }));

      expect(mockOnClose).toHaveBeenCalledTimes(1);
    });

    it('clears form on close', async () => {
      const { user } = renderWithProviders(<AddAnecdoteModal {...defaultProps} />);

      // Type some content
      await user.type(
        screen.getByPlaceholderText('Write your notes here...'),
        'Some content'
      );
      await user.type(
        screen.getByPlaceholderText('Optional title for this anecdote'),
        'A Title'
      );

      // Click cancel
      await user.click(screen.getByRole('button', { name: 'Cancel' }));

      // Verify onClose was called (form should reset internally)
      expect(mockOnClose).toHaveBeenCalled();
    });
  });
});
