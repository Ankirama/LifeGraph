/**
 * Tests for AddRelationshipModal component.
 */

import { describe, it, expect, beforeAll, afterAll, afterEach, vi } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';
import { renderWithProviders } from '@/test/utils';
import { AddRelationshipModal } from '../AddRelationshipModal';

// Mock data
const mockPersons = {
  results: [
    { id: 'p1', first_name: 'Jane', last_name: 'Smith', full_name: 'Jane Smith', nickname: 'Janie' },
    { id: 'p2', first_name: 'Bob', last_name: 'Johnson', full_name: 'Bob Johnson', nickname: null },
    { id: 'p3', first_name: 'Alice', last_name: 'Brown', full_name: 'Alice Brown', nickname: null },
  ],
};

const mockMe = {
  id: 'me-1',
  first_name: 'Test',
  last_name: 'User',
  full_name: 'Test User',
  is_owner: true,
};

const mockRelationshipTypes = {
  results: [
    { id: 'rt1', name: 'Friend', inverse_name: 'Friend', is_asymmetric: false },
    { id: 'rt2', name: 'Parent', inverse_name: 'Child', is_asymmetric: true },
    { id: 'rt3', name: 'Colleague', inverse_name: 'Colleague', is_asymmetric: false },
  ],
};

// MSW server setup
const server = setupServer(
  http.get('/api/v1/persons/', () => {
    return HttpResponse.json(mockPersons);
  }),
  http.get('/api/v1/me/', () => {
    return HttpResponse.json(mockMe);
  }),
  http.get('/api/v1/relationship-types/', () => {
    return HttpResponse.json(mockRelationshipTypes);
  }),
  http.post('/api/v1/relationships/', async () => {
    return HttpResponse.json(
      {
        id: 'new-relationship',
        person_a: 'current-person',
        person_b: 'p1',
        relationship_type: 'rt1',
      },
      { status: 201 }
    );
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('AddRelationshipModal', () => {
  const mockOnClose = vi.fn();
  const defaultProps = {
    isOpen: true,
    onClose: mockOnClose,
    personId: 'current-person',
    personName: 'John Doe',
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('rendering', () => {
    it('renders modal when open', () => {
      renderWithProviders(<AddRelationshipModal {...defaultProps} />);
      // Title appears in both modal header and button, so use role
      expect(screen.getByRole('heading', { name: 'Add Relationship' })).toBeInTheDocument();
    });

    it('does not render when closed', () => {
      renderWithProviders(<AddRelationshipModal {...defaultProps} isOpen={false} />);
      expect(screen.queryByText('Add Relationship')).not.toBeInTheDocument();
    });

    it('displays person name in description', () => {
      renderWithProviders(<AddRelationshipModal {...defaultProps} />);
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });
  });

  describe('person search', () => {
    it('renders search input', () => {
      renderWithProviders(<AddRelationshipModal {...defaultProps} />);
      expect(screen.getByPlaceholderText('Search by name...')).toBeInTheDocument();
    });

    it('loads and displays available persons', async () => {
      renderWithProviders(<AddRelationshipModal {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Jane Smith')).toBeInTheDocument();
        expect(screen.getByText('Bob Johnson')).toBeInTheDocument();
        expect(screen.getByText('Alice Brown')).toBeInTheDocument();
      });
    });

    it('shows Me option when me exists', async () => {
      renderWithProviders(<AddRelationshipModal {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Test User')).toBeInTheDocument();
        expect(screen.getByText('(Me)')).toBeInTheDocument();
      });
    });

    it('shows nickname when available', async () => {
      renderWithProviders(<AddRelationshipModal {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('"Janie"')).toBeInTheDocument();
      });
    });

    it('can select a person', async () => {
      const { user } = renderWithProviders(<AddRelationshipModal {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Jane Smith')).toBeInTheDocument();
      });

      await user.click(screen.getByText('Jane Smith'));

      // Person should be selected (bg-accent class)
      const personButton = screen.getByText('Jane Smith').closest('button');
      expect(personButton).toHaveClass('bg-accent');
    });
  });

  describe('relationship type', () => {
    it('renders relationship type select', () => {
      renderWithProviders(<AddRelationshipModal {...defaultProps} />);
      expect(screen.getByText('Relationship Type')).toBeInTheDocument();
    });

    it('loads and displays relationship types', async () => {
      renderWithProviders(<AddRelationshipModal {...defaultProps} />);

      await waitFor(() => {
        const select = screen.getByRole('combobox');
        expect(select).toBeInTheDocument();
      });
    });

    it('shows inverse name for asymmetric types', async () => {
      const { user } = renderWithProviders(<AddRelationshipModal {...defaultProps} />);

      await waitFor(() => {
        const select = screen.getByRole('combobox');
        expect(select).toBeInTheDocument();
      });

      const select = screen.getByRole('combobox');
      await user.click(select);

      // Should show "Parent / Child" option
      await waitFor(() => {
        expect(screen.getByText('Parent / Child')).toBeInTheDocument();
      });
    });
  });

  describe('additional fields', () => {
    it('renders strength input', () => {
      renderWithProviders(<AddRelationshipModal {...defaultProps} />);
      expect(screen.getByText('Relationship Strength (1-5)')).toBeInTheDocument();
    });

    it('renders started date input', () => {
      renderWithProviders(<AddRelationshipModal {...defaultProps} />);
      expect(screen.getByText('Started Date')).toBeInTheDocument();
    });

    it('renders notes textarea', () => {
      renderWithProviders(<AddRelationshipModal {...defaultProps} />);
      expect(screen.getByPlaceholderText('How do they know each other?')).toBeInTheDocument();
    });
  });

  describe('form submission', () => {
    it('disables submit when no person selected', () => {
      renderWithProviders(<AddRelationshipModal {...defaultProps} />);
      const submitButton = screen.getByRole('button', { name: 'Add Relationship' });
      expect(submitButton).toBeDisabled();
    });

    it('disables submit when no relationship type selected', async () => {
      const { user } = renderWithProviders(<AddRelationshipModal {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Jane Smith')).toBeInTheDocument();
      });

      await user.click(screen.getByText('Jane Smith'));

      const submitButton = screen.getByRole('button', { name: 'Add Relationship' });
      expect(submitButton).toBeDisabled();
    });

    it('enables submit when person and type are selected', async () => {
      const { user } = renderWithProviders(<AddRelationshipModal {...defaultProps} />);

      // Wait for data to load
      await waitFor(() => {
        expect(screen.getByText('Jane Smith')).toBeInTheDocument();
      });

      // Select person
      await user.click(screen.getByText('Jane Smith'));

      // Select relationship type
      const select = screen.getByRole('combobox');
      await user.selectOptions(select, 'rt1');

      const submitButton = screen.getByRole('button', { name: 'Add Relationship' });
      expect(submitButton).not.toBeDisabled();
    });

    it('submits form and calls onClose on success', async () => {
      const { user } = renderWithProviders(<AddRelationshipModal {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Jane Smith')).toBeInTheDocument();
      });

      await user.click(screen.getByText('Jane Smith'));

      const select = screen.getByRole('combobox');
      await user.selectOptions(select, 'rt1');

      await user.click(screen.getByRole('button', { name: 'Add Relationship' }));

      await waitFor(() => {
        expect(mockOnClose).toHaveBeenCalled();
      });
    });
  });

  describe('form actions', () => {
    it('calls onClose when cancel button is clicked', async () => {
      const { user } = renderWithProviders(<AddRelationshipModal {...defaultProps} />);

      await user.click(screen.getByRole('button', { name: 'Cancel' }));

      expect(mockOnClose).toHaveBeenCalledTimes(1);
    });
  });

  describe('strength input', () => {
    it('accepts number input for strength', async () => {
      const { user } = renderWithProviders(<AddRelationshipModal {...defaultProps} />);

      const strengthInput = screen.getByPlaceholderText('Optional (1 = weak, 5 = strong)');
      await user.type(strengthInput, '4');

      expect(strengthInput).toHaveValue(4);
    });

    it('has min and max constraints', () => {
      renderWithProviders(<AddRelationshipModal {...defaultProps} />);

      const strengthInput = screen.getByPlaceholderText('Optional (1 = weak, 5 = strong)');
      expect(strengthInput).toHaveAttribute('min', '1');
      expect(strengthInput).toHaveAttribute('max', '5');
    });
  });

  describe('notes input', () => {
    it('accepts text input for notes', async () => {
      const { user } = renderWithProviders(<AddRelationshipModal {...defaultProps} />);

      const notesInput = screen.getByPlaceholderText('How do they know each other?');
      await user.type(notesInput, 'Met at work');

      expect(notesInput).toHaveValue('Met at work');
    });
  });
});
