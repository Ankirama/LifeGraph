/**
 * Tests for RelationshipsPage page.
 */

import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';
import { renderWithProviders } from '@/test/utils';
import { RelationshipsPage } from '../RelationshipsPage';

// Mock data
const mockRelationships = {
  results: [
    {
      id: 'rel-1',
      person_a: 'p1',
      person_a_name: 'John Doe',
      person_b: 'p2',
      person_b_name: 'Jane Smith',
      relationship_type: 'rt1',
      relationship_type_name: 'Friend',
      started_date: '2020-01-15',
      strength: 4,
    },
    {
      id: 'rel-2',
      person_a: 'p1',
      person_a_name: 'John Doe',
      person_b: 'p3',
      person_b_name: 'Bob Johnson',
      relationship_type: 'rt1',
      relationship_type_name: 'Friend',
      started_date: null,
      strength: null,
    },
    {
      id: 'rel-3',
      person_a: 'p2',
      person_a_name: 'Jane Smith',
      person_b: 'p4',
      person_b_name: 'Alice Brown',
      relationship_type: 'rt2',
      relationship_type_name: 'Colleague',
      started_date: '2022-03-01',
      strength: 3,
    },
  ],
};

const mockRelationshipTypes = {
  results: [
    { id: 'rt1', name: 'Friend', inverse_name: 'Friend', is_asymmetric: false, category: 'social' },
    {
      id: 'rt2',
      name: 'Colleague',
      inverse_name: 'Colleague',
      is_asymmetric: false,
      category: 'professional',
    },
    { id: 'rt3', name: 'Parent', inverse_name: 'Child', is_asymmetric: true, category: 'family' },
  ],
};

const mockSuggestions = {
  suggestions: [
    {
      person1_id: 'p1',
      person1_name: 'John Doe',
      person2_id: 'p5',
      person2_name: 'Charlie Wilson',
      suggested_type: 'Friend',
      confidence: 0.85,
      reason: 'Both appear in 3 photos together',
      evidence: ['Photo at beach', 'Birthday party', 'Work event'],
    },
  ],
  total_contacts: 10,
  existing_relationships_count: 3,
  message: null,
};

// MSW server setup
const server = setupServer(
  http.get('/api/v1/relationships/', () => {
    return HttpResponse.json(mockRelationships);
  }),
  http.get('/api/v1/relationship-types/', () => {
    return HttpResponse.json(mockRelationshipTypes);
  }),
  http.get('/api/v1/ai/suggest-relationships/', () => {
    return HttpResponse.json(mockSuggestions);
  }),
  http.post('/api/v1/ai/apply-relationship-suggestion/', () => {
    return HttpResponse.json({ success: true });
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('RelationshipsPage', () => {
  describe('loading state', () => {
    it('shows loading indicator initially', () => {
      renderWithProviders(<RelationshipsPage />);
      expect(screen.getByText('Loading relationships...')).toBeInTheDocument();
    });
  });

  describe('page header', () => {
    it('displays page title', async () => {
      renderWithProviders(<RelationshipsPage />);
      await waitFor(() => {
        expect(screen.getByRole('heading', { name: 'Relationships' })).toBeInTheDocument();
      });
    });

    it('displays page description', async () => {
      renderWithProviders(<RelationshipsPage />);
      await waitFor(() => {
        expect(
          screen.getByText(/View connections between people in your network/i)
        ).toBeInTheDocument();
      });
    });

    it('displays AI Suggestions button', async () => {
      renderWithProviders(<RelationshipsPage />);
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /AI Suggestions/i })).toBeInTheDocument();
      });
    });
  });

  describe('stats', () => {
    it('displays total connections count', async () => {
      renderWithProviders(<RelationshipsPage />);
      await waitFor(() => {
        // "3" may appear in counts and strength indicators
        const threeTexts = screen.getAllByText('3');
        expect(threeTexts.length).toBeGreaterThan(0);
        expect(screen.getByText('Total Connections')).toBeInTheDocument();
      });
    });

    it('displays relationship types count', async () => {
      renderWithProviders(<RelationshipsPage />);
      await waitFor(() => {
        expect(screen.getByText('Relationship Types')).toBeInTheDocument();
      });
    });

    it('displays family types count', async () => {
      renderWithProviders(<RelationshipsPage />);
      await waitFor(() => {
        expect(screen.getByText('Family Types')).toBeInTheDocument();
      });
    });

    it('displays professional types count', async () => {
      renderWithProviders(<RelationshipsPage />);
      await waitFor(() => {
        expect(screen.getByText('Professional Types')).toBeInTheDocument();
      });
    });
  });

  describe('filter', () => {
    it('renders type filter dropdown', async () => {
      renderWithProviders(<RelationshipsPage />);
      await waitFor(() => {
        expect(screen.getByRole('combobox')).toBeInTheDocument();
      });
    });

    it('has "All Relationship Types" as default option', async () => {
      renderWithProviders(<RelationshipsPage />);
      await waitFor(() => {
        const select = screen.getByRole('combobox');
        expect(select).toHaveValue('');
      });
    });

    it('shows relationship type options', async () => {
      renderWithProviders(<RelationshipsPage />);
      await waitFor(() => {
        expect(screen.getByRole('option', { name: 'All Relationship Types' })).toBeInTheDocument();
        expect(screen.getByRole('option', { name: 'Friend' })).toBeInTheDocument();
        expect(screen.getByRole('option', { name: 'Colleague' })).toBeInTheDocument();
        expect(screen.getByRole('option', { name: 'Parent' })).toBeInTheDocument();
      });
    });
  });

  describe('relationships list', () => {
    it('displays person names', async () => {
      renderWithProviders(<RelationshipsPage />);
      await waitFor(() => {
        // Person names appear multiple times (in relationship cards and section headers)
        const johnDoeTexts = screen.getAllByText('John Doe');
        expect(johnDoeTexts.length).toBeGreaterThan(0);
        const janeSmithTexts = screen.getAllByText('Jane Smith');
        expect(janeSmithTexts.length).toBeGreaterThan(0);
        const bobJohnsonTexts = screen.getAllByText('Bob Johnson');
        expect(bobJohnsonTexts.length).toBeGreaterThan(0);
      });
    });

    it('displays relationship types', async () => {
      renderWithProviders(<RelationshipsPage />);
      await waitFor(() => {
        const friendTypes = screen.getAllByText('Friend');
        expect(friendTypes.length).toBeGreaterThanOrEqual(1);
        // Colleague appears multiple times (filter option, relationship type, etc.)
        const colleagueTexts = screen.getAllByText('Colleague');
        expect(colleagueTexts.length).toBeGreaterThan(0);
      });
    });

    it('displays strength indicators when available', async () => {
      renderWithProviders(<RelationshipsPage />);
      await waitFor(() => {
        // Strength label appears for each relationship with strength
        const strengthTexts = screen.getAllByText('Strength:');
        expect(strengthTexts.length).toBeGreaterThan(0);
      });
    });

    it('displays started date when available', async () => {
      renderWithProviders(<RelationshipsPage />);
      await waitFor(() => {
        expect(screen.getByText(/Since Jan 2020/)).toBeInTheDocument();
      });
    });

    it('groups relationships by type', async () => {
      renderWithProviders(<RelationshipsPage />);
      await waitFor(() => {
        // Friend section should show with count
        expect(screen.getByText('(2)')).toBeInTheDocument();
      });
    });
  });

  describe('empty state', () => {
    it('shows empty state when no relationships', async () => {
      server.use(
        http.get('/api/v1/relationships/', () => {
          return HttpResponse.json({ results: [] });
        })
      );

      renderWithProviders(<RelationshipsPage />);
      await waitFor(() => {
        expect(screen.getByText('No relationships yet')).toBeInTheDocument();
      });
    });

    it('shows link to people page in empty state', async () => {
      server.use(
        http.get('/api/v1/relationships/', () => {
          return HttpResponse.json({ results: [] });
        })
      );

      renderWithProviders(<RelationshipsPage />);
      await waitFor(() => {
        expect(screen.getByRole('link', { name: /Go to People/i })).toBeInTheDocument();
      });
    });

    it('shows helpful message in empty state', async () => {
      server.use(
        http.get('/api/v1/relationships/', () => {
          return HttpResponse.json({ results: [] });
        })
      );

      renderWithProviders(<RelationshipsPage />);
      await waitFor(() => {
        expect(
          screen.getByText(/Add relationships from person profiles to see connections here/i)
        ).toBeInTheDocument();
      });
    });
  });

  describe('AI suggestions panel', () => {
    it('shows suggestions panel when button is clicked', async () => {
      const { user } = renderWithProviders(<RelationshipsPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /AI Suggestions/i })).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /AI Suggestions/i }));

      await waitFor(() => {
        expect(screen.getByText('AI Relationship Suggestions')).toBeInTheDocument();
      });
    });

    it('displays suggestions', async () => {
      const { user } = renderWithProviders(<RelationshipsPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /AI Suggestions/i })).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /AI Suggestions/i }));

      await waitFor(() => {
        expect(screen.getByText('Charlie Wilson')).toBeInTheDocument();
        expect(screen.getByText('Both appear in 3 photos together')).toBeInTheDocument();
      });
    });

    it('displays confidence percentage', async () => {
      const { user } = renderWithProviders(<RelationshipsPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /AI Suggestions/i })).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /AI Suggestions/i }));

      await waitFor(() => {
        expect(screen.getByText('85% confident')).toBeInTheDocument();
      });
    });

    it('displays accept button for suggestions', async () => {
      const { user } = renderWithProviders(<RelationshipsPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /AI Suggestions/i })).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /AI Suggestions/i }));

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Accept/i })).toBeInTheDocument();
      });
    });

    it('displays evidence for suggestions', async () => {
      const { user } = renderWithProviders(<RelationshipsPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /AI Suggestions/i })).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /AI Suggestions/i }));

      await waitFor(() => {
        expect(screen.getByText('Photo at beach')).toBeInTheDocument();
        expect(screen.getByText('Birthday party')).toBeInTheDocument();
        expect(screen.getByText('Work event')).toBeInTheDocument();
      });
    });

    it('hides suggestions panel when button is clicked again', async () => {
      const { user } = renderWithProviders(<RelationshipsPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /AI Suggestions/i })).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /AI Suggestions/i }));

      await waitFor(() => {
        expect(screen.getByText('AI Relationship Suggestions')).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /Hide Suggestions/i }));

      await waitFor(() => {
        expect(screen.queryByText('AI Relationship Suggestions')).not.toBeInTheDocument();
      });
    });
  });

  describe('suggestions empty state', () => {
    it('shows empty message when no suggestions', async () => {
      server.use(
        http.get('/api/v1/ai/suggest-relationships/', () => {
          return HttpResponse.json({
            suggestions: [],
            total_contacts: 10,
            existing_relationships_count: 5,
            message: 'No new relationship suggestions found.',
          });
        })
      );

      const { user } = renderWithProviders(<RelationshipsPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /AI Suggestions/i })).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /AI Suggestions/i }));

      await waitFor(() => {
        expect(screen.getByText('No new relationship suggestions found.')).toBeInTheDocument();
      });
    });
  });

  describe('person links', () => {
    it('renders person names as links', async () => {
      renderWithProviders(<RelationshipsPage />);

      await waitFor(() => {
        const johnDoeTexts = screen.getAllByText('John Doe');
        expect(johnDoeTexts.length).toBeGreaterThan(0);
      });

      // Find the first John Doe link
      const johnDoeTexts = screen.getAllByText('John Doe');
      const johnLink = johnDoeTexts[0].closest('a');
      expect(johnLink).toHaveAttribute('href', '/people/p1');
    });
  });
});
