/**
 * Tests for PersonForm component.
 */

import { describe, it, expect, beforeAll, afterAll, afterEach, vi } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';
import { renderWithProviders } from '@/test/utils';
import { PersonForm } from '../PersonForm';

// Mock data
const mockTags = {
  results: [
    { id: 't1', name: 'Friend', color: '#ff0000' },
    { id: 't2', name: 'Family', color: '#00ff00' },
  ],
};

const mockGroups = {
  results: [
    { id: 'g1', name: 'Work' },
    { id: 'g2', name: 'College' },
  ],
};

const mockPerson = {
  id: '1',
  first_name: 'John',
  last_name: 'Doe',
  full_name: 'John Doe',
  nickname: 'Johnny',
  birthday: '1990-01-15',
  met_date: '2020-03-01',
  met_context: 'Work conference',
  emails: [{ email: 'john@example.com', label: 'personal' }],
  phones: [{ phone: '+1234567890', label: 'mobile' }],
  addresses: [],
  linkedin_url: 'https://linkedin.com/in/johndoe',
  discord_id: 'john#1234',
  notes: 'Great friend',
  tags: [{ id: 't1', name: 'Friend', color: '#ff0000' }],
  groups: [{ id: 'g1', name: 'Work' }],
};

// MSW server setup
const server = setupServer(
  http.get('/api/v1/tags/', () => {
    return HttpResponse.json(mockTags);
  }),
  http.get('/api/v1/groups/', () => {
    return HttpResponse.json(mockGroups);
  }),
  http.post('/api/v1/persons/', async () => {
    return HttpResponse.json({ ...mockPerson, id: 'new-id' }, { status: 201 });
  }),
  http.patch('/api/v1/persons/:id/', async () => {
    return HttpResponse.json(mockPerson);
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('PersonForm', () => {
  const mockOnSuccess = vi.fn();
  const mockOnCancel = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('create mode', () => {
    it('renders empty form for new person', () => {
      renderWithProviders(
        <PersonForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />
      );

      expect(screen.getByPlaceholderText('First name')).toHaveValue('');
      expect(screen.getByPlaceholderText('Last name')).toHaveValue('');
    });

    it('renders all form sections', () => {
      renderWithProviders(
        <PersonForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />
      );

      expect(screen.getByText('Basic Information')).toBeInTheDocument();
      expect(screen.getByText('Contact Information')).toBeInTheDocument();
      expect(screen.getByText('Social Links')).toBeInTheDocument();
      expect(screen.getByText('Organization')).toBeInTheDocument();
    });

    it('renders first name as required field', () => {
      renderWithProviders(
        <PersonForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />
      );

      const firstNameInput = screen.getByPlaceholderText('First name');
      expect(firstNameInput).toHaveAttribute('required');
    });

    it('shows Create Person button for new person', () => {
      renderWithProviders(
        <PersonForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />
      );

      expect(screen.getByRole('button', { name: 'Create Person' })).toBeInTheDocument();
    });

    it('disables submit when first name is empty', () => {
      renderWithProviders(
        <PersonForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />
      );

      const submitButton = screen.getByRole('button', { name: 'Create Person' });
      expect(submitButton).toBeDisabled();
    });

    it('enables submit when first name is entered', async () => {
      const { user } = renderWithProviders(
        <PersonForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />
      );

      const firstNameInput = screen.getByPlaceholderText('First name');
      await user.type(firstNameInput, 'Jane');

      const submitButton = screen.getByRole('button', { name: 'Create Person' });
      expect(submitButton).not.toBeDisabled();
    });
  });

  describe('edit mode', () => {
    it('populates form with existing person data', () => {
      renderWithProviders(
        <PersonForm
          person={mockPerson as any}
          onSuccess={mockOnSuccess}
          onCancel={mockOnCancel}
        />
      );

      expect(screen.getByPlaceholderText('First name')).toHaveValue('John');
      expect(screen.getByPlaceholderText('Last name')).toHaveValue('Doe');
      expect(screen.getByPlaceholderText('Optional nickname')).toHaveValue('Johnny');
    });

    it('shows Save Changes button for existing person', () => {
      renderWithProviders(
        <PersonForm
          person={mockPerson as any}
          onSuccess={mockOnSuccess}
          onCancel={mockOnCancel}
        />
      );

      expect(screen.getByRole('button', { name: 'Save Changes' })).toBeInTheDocument();
    });

    it('populates social links from existing person', () => {
      renderWithProviders(
        <PersonForm
          person={mockPerson as any}
          onSuccess={mockOnSuccess}
          onCancel={mockOnCancel}
        />
      );

      expect(screen.getByPlaceholderText('https://linkedin.com/in/...')).toHaveValue(
        'https://linkedin.com/in/johndoe'
      );
      expect(screen.getByPlaceholderText('username#1234')).toHaveValue('john#1234');
    });
  });

  describe('contact fields', () => {
    it('can add new email field', async () => {
      const { user } = renderWithProviders(
        <PersonForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />
      );

      // Find and click the Add button for emails
      const addButtons = screen.getAllByText('Add');
      await user.click(addButtons[0]); // First Add is for emails

      // Should have multiple email inputs now
      const emailInputs = screen.getAllByPlaceholderText('email@example.com');
      expect(emailInputs.length).toBeGreaterThan(1);
    });

    it('can add new phone field', async () => {
      const { user } = renderWithProviders(
        <PersonForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />
      );

      // Find and click the Add button for phones (second Add button)
      const addButtons = screen.getAllByText('Add');
      await user.click(addButtons[1]); // Second Add is for phones

      const phoneInputs = screen.getAllByPlaceholderText('+1 234 567 8900');
      expect(phoneInputs.length).toBe(1);
    });
  });

  describe('tags and groups', () => {
    it('loads and displays available tags', async () => {
      renderWithProviders(
        <PersonForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />
      );

      await waitFor(() => {
        expect(screen.getByText('Friend')).toBeInTheDocument();
        expect(screen.getByText('Family')).toBeInTheDocument();
      });
    });

    it('loads and displays available groups', async () => {
      renderWithProviders(
        <PersonForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />
      );

      await waitFor(() => {
        // Groups section shows group names as labels - Work also appears in email label select
        // Look for College which is unique to groups
        expect(screen.getByText('College')).toBeInTheDocument();
        // Work appears in groups section (and email select), just check it's present
        const workElements = screen.getAllByText('Work');
        expect(workElements.length).toBeGreaterThanOrEqual(1);
      });
    });
  });

  describe('form actions', () => {
    it('calls onCancel when cancel button is clicked', async () => {
      const { user } = renderWithProviders(
        <PersonForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />
      );

      await user.click(screen.getByRole('button', { name: 'Cancel' }));

      expect(mockOnCancel).toHaveBeenCalledTimes(1);
    });

    it('submits form and calls onSuccess', async () => {
      const { user } = renderWithProviders(
        <PersonForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />
      );

      await user.type(screen.getByPlaceholderText('First name'), 'Jane');
      await user.click(screen.getByRole('button', { name: 'Create Person' }));

      await waitFor(() => {
        expect(mockOnSuccess).toHaveBeenCalled();
      });
    });
  });

  describe('form inputs', () => {
    it('updates first name on input', async () => {
      const { user } = renderWithProviders(
        <PersonForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />
      );

      const input = screen.getByPlaceholderText('First name');
      await user.type(input, 'Jane');

      expect(input).toHaveValue('Jane');
    });

    it('updates last name on input', async () => {
      const { user } = renderWithProviders(
        <PersonForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />
      );

      const input = screen.getByPlaceholderText('Last name');
      await user.type(input, 'Smith');

      expect(input).toHaveValue('Smith');
    });

    it('updates nickname on input', async () => {
      const { user } = renderWithProviders(
        <PersonForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />
      );

      const input = screen.getByPlaceholderText('Optional nickname');
      await user.type(input, 'JJ');

      expect(input).toHaveValue('JJ');
    });

    it('updates met context on input', async () => {
      const { user } = renderWithProviders(
        <PersonForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />
      );

      const input = screen.getByPlaceholderText('e.g., College roommate, Work conference 2023');
      await user.type(input, 'Met at conference');

      expect(input).toHaveValue('Met at conference');
    });

    it('updates notes on input', async () => {
      const { user } = renderWithProviders(
        <PersonForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />
      );

      const input = screen.getByPlaceholderText('General notes about this person...');
      await user.type(input, 'Some notes');

      expect(input).toHaveValue('Some notes');
    });
  });
});
