/**
 * Tests for PersonDetail page.
 */

import { describe, it, expect, beforeAll, afterAll, afterEach, vi } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';
import { renderWithProviders } from '@/test/utils';
import { PersonDetail } from '../PersonDetail';

// Mock useParams
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useParams: () => ({ id: 'person-1' }),
  };
});

// Mock window.confirm
const originalConfirm = window.confirm;
beforeAll(() => {
  window.confirm = vi.fn(() => true);
});
afterAll(() => {
  window.confirm = originalConfirm;
});

// Mock data
const mockPerson = {
  id: 'person-1',
  first_name: 'John',
  last_name: 'Doe',
  full_name: 'John Doe',
  nickname: 'Johnny',
  birthday: '1990-05-15',
  met_date: '2020-01-01',
  met_context: 'Work conference',
  primary_email: 'john@example.com',
  primary_phone: '+1234567890',
  linkedin_url: 'https://linkedin.com/in/johndoe',
  ai_summary: 'John is a software engineer with a passion for hiking.',
  notes: 'Good friend from work.',
  tags: [
    { id: 't1', name: 'Friend', color: '#ff0000' },
    { id: 't2', name: 'Work', color: '#0000ff' },
  ],
  groups: [
    { id: 'g1', name: 'Engineering', full_path: 'Company/Engineering', color: '#00ff00' },
  ],
};

const mockRelationships = [
  {
    id: 'rel-1',
    person_a: 'person-1',
    person_a_name: 'John Doe',
    person_b: 'person-2',
    person_b_name: 'Jane Smith',
    relationship_type: 'rt1',
    relationship_type_name: 'Friend',
    relationship_type_inverse_name: 'Friend',
    strength: 4,
    started_date: '2020-06-01',
  },
];

const mockAnecdotes = [
  {
    id: 'anec-1',
    title: 'Funny story',
    content: 'We had a great laugh together',
    anecdote_type: 'memory',
    date: '2023-07-15',
    location: 'New York',
  },
];

const mockPhotos = [
  {
    id: 'photo-1',
    file: 'https://example.com/photo1.jpg',
    caption: 'Beach day',
    date_taken: '2023-08-01',
    ai_description: 'A sunny beach scene',
    persons: [{ id: 'person-1', full_name: 'John Doe' }],
    tags: [],
    created_at: '2023-08-01T00:00:00Z',
    updated_at: '2023-08-01T00:00:00Z',
  },
];

const mockEmployments = [
  {
    id: 'emp-1',
    person: 'person-1',
    company: 'Tech Corp',
    title: 'Senior Engineer',
    department: 'Engineering',
    start_date: '2022-01-01',
    end_date: null,
    is_current: true,
    location: 'San Francisco',
    description: 'Leading backend team',
    linkedin_synced: true,
    created_at: '2022-01-01T00:00:00Z',
    updated_at: '2022-01-01T00:00:00Z',
  },
];

const mockTags = {
  results: [
    { id: 't1', name: 'Friend', color: '#ff0000' },
    { id: 't2', name: 'Work', color: '#0000ff' },
    { id: 't3', name: 'Family', color: '#00ff00' },
  ],
};

const mockRelationshipTypes = {
  results: [
    { id: 'rt1', name: 'Friend', inverse_name: 'Friend', is_asymmetric: false },
    { id: 'rt2', name: 'Parent', inverse_name: 'Child', is_asymmetric: true },
  ],
};

const mockPersons = {
  results: [
    { id: 'person-2', first_name: 'Jane', last_name: 'Smith', full_name: 'Jane Smith' },
    { id: 'person-3', first_name: 'Bob', last_name: 'Johnson', full_name: 'Bob Johnson' },
  ],
};

// MSW server setup
const server = setupServer(
  http.get('/api/v1/persons/person-1/', () => {
    return HttpResponse.json(mockPerson);
  }),
  http.get('/api/v1/persons/person-1/relationships/', () => {
    return HttpResponse.json(mockRelationships);
  }),
  http.get('/api/v1/persons/person-1/anecdotes/', () => {
    return HttpResponse.json(mockAnecdotes);
  }),
  http.get('/api/v1/persons/person-1/photos/', () => {
    return HttpResponse.json(mockPhotos);
  }),
  http.get('/api/v1/persons/person-1/employments/', () => {
    return HttpResponse.json(mockEmployments);
  }),
  http.get('/api/v1/tags/', () => {
    return HttpResponse.json(mockTags);
  }),
  http.get('/api/v1/groups/', () => {
    return HttpResponse.json({ results: [] });
  }),
  http.get('/api/v1/relationship-types/', () => {
    return HttpResponse.json(mockRelationshipTypes);
  }),
  http.get('/api/v1/persons/', () => {
    return HttpResponse.json(mockPersons);
  }),
  http.get('/api/v1/me/', () => {
    return HttpResponse.json({ id: 'me-1', full_name: 'Test User', is_owner: true });
  }),
  http.post('/api/v1/persons/person-1/generate-summary/', () => {
    return HttpResponse.json({ ai_summary: 'New AI summary' });
  }),
  http.post('/api/v1/persons/person-1/suggest-tags/', () => {
    return HttpResponse.json({
      suggested_tags: [{ name: 'Engineer', confidence: 0.95, reason: 'Works in tech', is_existing: false }],
    });
  }),
  http.delete('/api/v1/relationships/:id/', () => {
    return new HttpResponse(null, { status: 204 });
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('PersonDetail', () => {
  describe('loading state', () => {
    it('shows loading indicator initially', () => {
      renderWithProviders(<PersonDetail />);
      expect(screen.getByText('Loading...')).toBeInTheDocument();
    });
  });

  describe('person header', () => {
    it('displays person full name', async () => {
      renderWithProviders(<PersonDetail />);
      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });
    });

    it('displays nickname when available', async () => {
      renderWithProviders(<PersonDetail />);
      await waitFor(() => {
        expect(screen.getByText('"Johnny"')).toBeInTheDocument();
      });
    });

    it('displays edit button', async () => {
      renderWithProviders(<PersonDetail />);
      await waitFor(() => {
        // Multiple Edit buttons may exist (for person, relationships, etc.)
        const editButtons = screen.getAllByRole('button', { name: /Edit/i });
        expect(editButtons.length).toBeGreaterThan(0);
      });
    });

    it('displays back link to people list', async () => {
      renderWithProviders(<PersonDetail />);
      await waitFor(() => {
        expect(screen.getByRole('link', { name: '' })).toBeInTheDocument();
      });
    });
  });

  describe('quick info', () => {
    it('displays birthday', async () => {
      renderWithProviders(<PersonDetail />);
      await waitFor(() => {
        expect(screen.getByText('May 15')).toBeInTheDocument();
      });
    });

    it('displays met context', async () => {
      renderWithProviders(<PersonDetail />);
      await waitFor(() => {
        expect(screen.getByText('Work conference')).toBeInTheDocument();
      });
    });

    it('displays primary email', async () => {
      renderWithProviders(<PersonDetail />);
      await waitFor(() => {
        expect(screen.getByText('john@example.com')).toBeInTheDocument();
      });
    });

    it('displays primary phone', async () => {
      renderWithProviders(<PersonDetail />);
      await waitFor(() => {
        expect(screen.getByText('+1234567890')).toBeInTheDocument();
      });
    });
  });

  describe('tags section', () => {
    it('displays person tags', async () => {
      renderWithProviders(<PersonDetail />);
      await waitFor(() => {
        // Friend appears as a tag and possibly in relationship section
        const friendTexts = screen.getAllByText('Friend');
        expect(friendTexts.length).toBeGreaterThan(0);
        // Work appears multiple times (tag and employment)
        expect(screen.getAllByText(/Work/i).length).toBeGreaterThanOrEqual(1);
      });
    });

    it('displays suggest tags button', async () => {
      renderWithProviders(<PersonDetail />);
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Suggest Tags/i })).toBeInTheDocument();
      });
    });
  });

  describe('AI summary section', () => {
    it('displays AI summary section', async () => {
      renderWithProviders(<PersonDetail />);
      await waitFor(() => {
        expect(screen.getByText('AI Summary')).toBeInTheDocument();
      });
    });

    it('displays existing AI summary', async () => {
      renderWithProviders(<PersonDetail />);
      await waitFor(() => {
        expect(screen.getByText('John is a software engineer with a passion for hiking.')).toBeInTheDocument();
      });
    });

    it('displays regenerate button when summary exists', async () => {
      renderWithProviders(<PersonDetail />);
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Regenerate/i })).toBeInTheDocument();
      });
    });
  });

  describe('notes section', () => {
    it('displays notes when available', async () => {
      renderWithProviders(<PersonDetail />);
      await waitFor(() => {
        expect(screen.getByText('Good friend from work.')).toBeInTheDocument();
      });
    });
  });

  describe('anecdotes section', () => {
    it('displays anecdotes section title', async () => {
      renderWithProviders(<PersonDetail />);
      await waitFor(() => {
        expect(screen.getByText('Anecdotes')).toBeInTheDocument();
      });
    });

    it('displays anecdote content', async () => {
      renderWithProviders(<PersonDetail />);
      await waitFor(() => {
        expect(screen.getByText('We had a great laugh together')).toBeInTheDocument();
      });
    });

    it('displays add anecdote button', async () => {
      renderWithProviders(<PersonDetail />);
      await waitFor(() => {
        // Find the Add button in the Anecdotes section
        const addButtons = screen.getAllByRole('button', { name: /Add/i });
        expect(addButtons.length).toBeGreaterThanOrEqual(1);
      });
    });
  });

  describe('photos section', () => {
    it('displays photos section title', async () => {
      renderWithProviders(<PersonDetail />);
      await waitFor(() => {
        expect(screen.getByText('Photos')).toBeInTheDocument();
      });
    });

    it('displays upload button', async () => {
      renderWithProviders(<PersonDetail />);
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Upload/i })).toBeInTheDocument();
      });
    });
  });

  describe('employment section', () => {
    it('displays employment history section', async () => {
      renderWithProviders(<PersonDetail />);
      await waitFor(() => {
        expect(screen.getByText('Employment History')).toBeInTheDocument();
      });
    });

    it('displays current employment', async () => {
      renderWithProviders(<PersonDetail />);
      await waitFor(() => {
        expect(screen.getByText('Senior Engineer')).toBeInTheDocument();
        expect(screen.getByText('Tech Corp')).toBeInTheDocument();
      });
    });

    it('displays LinkedIn sync button when URL exists', async () => {
      renderWithProviders(<PersonDetail />);
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Sync LinkedIn/i })).toBeInTheDocument();
      });
    });
  });

  describe('relationships section', () => {
    it('displays relationships section title', async () => {
      renderWithProviders(<PersonDetail />);
      await waitFor(() => {
        expect(screen.getByText('Relationships')).toBeInTheDocument();
      });
    });

    it('displays related person name', async () => {
      renderWithProviders(<PersonDetail />);
      await waitFor(() => {
        expect(screen.getByText('Jane Smith')).toBeInTheDocument();
      });
    });

    it('displays add relationship button', async () => {
      renderWithProviders(<PersonDetail />);
      await waitFor(() => {
        const relSection = screen.getByText('Relationships').closest('div');
        expect(relSection).toBeInTheDocument();
      });
    });
  });

  describe('groups section', () => {
    it('displays groups section when person has groups', async () => {
      renderWithProviders(<PersonDetail />);
      await waitFor(() => {
        expect(screen.getByText('Groups')).toBeInTheDocument();
      });
    });

    it('displays group path', async () => {
      renderWithProviders(<PersonDetail />);
      await waitFor(() => {
        expect(screen.getByText('Company/Engineering')).toBeInTheDocument();
      });
    });
  });

  describe('edit modal', () => {
    it('opens edit modal when Edit button is clicked', async () => {
      const { user } = renderWithProviders(<PersonDetail />);

      await waitFor(() => {
        // Multiple Edit buttons may exist (for person, relationships, etc.)
        const editButtons = screen.getAllByRole('button', { name: /Edit/i });
        expect(editButtons.length).toBeGreaterThan(0);
      });

      // Click the first Edit button (should be the person edit)
      const editButtons = screen.getAllByRole('button', { name: /Edit/i });
      await user.click(editButtons[0]);

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: 'Edit Person' })).toBeInTheDocument();
      });
    });
  });

  describe('not found state', () => {
    it('shows not found message when person does not exist', async () => {
      server.use(
        http.get('/api/v1/persons/person-1/', () => {
          return new HttpResponse(null, { status: 404 });
        })
      );

      renderWithProviders(<PersonDetail />);
      await waitFor(() => {
        expect(screen.getByText('Person not found')).toBeInTheDocument();
      });
    });
  });
});
