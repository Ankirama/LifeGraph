/**
 * MSW request handlers for API mocking.
 *
 * Comprehensive handlers for all API endpoints.
 */

import { http, HttpResponse } from 'msw';

// MSW matches relative URLs when using jsdom - no need for host
const API_BASE = '/api/v1';

// ============================================================================
// Mock Data
// ============================================================================

export const mockPerson = {
  id: '123e4567-e89b-12d3-a456-426614174000',
  first_name: 'John',
  last_name: 'Doe',
  nickname: 'Johnny',
  full_name: 'John Doe',
  birthday: '1990-05-15',
  met_date: '2020-01-01',
  met_context: 'Met at conference',
  emails: [{ email: 'john@example.com', label: 'work' }],
  phones: [{ phone: '+1234567890', label: 'mobile' }],
  addresses: [],
  linkedin_url: '',
  discord_id: '',
  notes: 'Great person',
  is_owner: false,
  is_active: true,
  ai_summary: '',
  ai_summary_updated: null,
  last_contact: null,
  primary_email: 'john@example.com',
  primary_phone: '+1234567890',
  tags: [],
  groups: [],
  custom_fields: [],
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

export const mockOwner = {
  ...mockPerson,
  id: '123e4567-e89b-12d3-a456-426614174001',
  first_name: 'Me',
  last_name: 'Owner',
  full_name: 'Me Owner',
  is_owner: true,
};

export const mockTag = {
  id: '223e4567-e89b-12d3-a456-426614174000',
  name: 'Friend',
  color: '#ff0000',
  description: 'Friends',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

export const mockGroup = {
  id: '323e4567-e89b-12d3-a456-426614174000',
  name: 'Work',
  description: 'Work contacts',
  color: '#00ff00',
  parent: null,
  parent_id: null,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

export const mockRelationshipType = {
  id: '423e4567-e89b-12d3-a456-426614174000',
  name: 'Friend',
  inverse_name: 'Friend',
  category: 'social',
  is_symmetric: true,
  auto_create_inverse: true,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

export const mockRelationship = {
  id: '523e4567-e89b-12d3-a456-426614174000',
  person_a: mockPerson.id,
  person_a_name: mockPerson.full_name,
  person_b: mockOwner.id,
  person_b_name: mockOwner.full_name,
  relationship_type: mockRelationshipType.id,
  relationship_type_name: 'Friend',
  relationship_type_inverse_name: 'Friend',
  started_date: '2020-01-01',
  notes: '',
  strength: 5,
  auto_created: false,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

export const mockAnecdote = {
  id: '623e4567-e89b-12d3-a456-426614174000',
  title: 'Funny Story',
  content: 'Once upon a time...',
  date: '2023-07-20',
  location: 'New York',
  anecdote_type: 'memory',
  persons: [{ ...mockPerson, tags: [] }],
  tags: [],
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

export const mockPhoto = {
  id: '723e4567-e89b-12d3-a456-426614174000',
  file: '/media/photos/2024/01/photo.jpg',
  caption: 'Birthday party',
  date_taken: '2024-01-15T12:00:00Z',
  location: 'Home',
  location_coords: null,
  ai_description: '',
  detected_faces: [],
  persons: [],
  anecdote: null,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

export const mockEmployment = {
  id: '823e4567-e89b-12d3-a456-426614174000',
  person: mockPerson.id,
  person_name: mockPerson.full_name,
  company: 'Acme Corp',
  title: 'Software Engineer',
  department: 'Engineering',
  start_date: '2020-01-01',
  end_date: null,
  is_current: true,
  location: 'San Francisco',
  description: 'Building cool stuff',
  linkedin_synced: false,
  linkedin_last_sync: null,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

export const mockDashboard = {
  stats: {
    total_persons: 10,
    total_relationships: 15,
    total_anecdotes: 25,
    total_photos: 5,
  },
  upcoming_birthdays: [
    {
      id: mockPerson.id,
      full_name: 'John Doe',
      birthday: '1990-05-15',
      days_until: 10,
      turning_age: 35,
      date: '2025-05-15',
    },
  ],
  recent_anecdotes: [],
  recent_persons: [],
  relationship_distribution: [{ name: 'Friend', count: 5 }],
};

export const mockGraphData = {
  nodes: [
    { id: mockPerson.id, label: 'John Doe', first_name: 'John', last_name: 'Doe', avatar: null },
    { id: mockOwner.id, label: 'Me Owner', first_name: 'Me', last_name: 'Owner', avatar: null },
  ],
  edges: [
    {
      id: mockRelationship.id,
      source: mockPerson.id,
      target: mockOwner.id,
      type: mockRelationshipType.id,
      type_name: 'Friend',
      inverse_name: 'Friend',
      category: 'social',
      strength: 5,
      is_symmetric: true,
    },
  ],
  relationship_types: [{ id: mockRelationshipType.id, name: 'Friend', category: 'social' }],
  center_person_id: null,
};

// ============================================================================
// Paginated Response Helper
// ============================================================================

function paginatedResponse<T>(results: T[], count?: number) {
  return {
    count: count ?? results.length,
    next: null,
    previous: null,
    results,
  };
}

// ============================================================================
// API Handlers
// ============================================================================

export const handlers = [
  // -------------------- Dashboard --------------------
  http.get(`${API_BASE}/dashboard/`, () => {
    return HttpResponse.json(mockDashboard);
  }),

  // -------------------- Health --------------------
  http.get(`${API_BASE}/health/`, () => {
    return HttpResponse.json({ status: 'healthy' });
  }),

  // -------------------- Me (Owner) --------------------
  http.get(`${API_BASE}/me/`, () => {
    return HttpResponse.json(mockOwner);
  }),

  http.post(`${API_BASE}/me/`, async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json({ ...mockOwner, ...body }, { status: 201 });
  }),

  http.patch(`${API_BASE}/me/`, async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json({ ...mockOwner, ...body });
  }),

  // -------------------- Persons --------------------
  http.get(`${API_BASE}/persons/`, ({ request }) => {
    const url = new URL(request.url);
    const search = url.searchParams.get('search');
    const results = search ? [mockPerson] : [mockPerson];
    return HttpResponse.json(paginatedResponse(results));
  }),

  http.get(`${API_BASE}/persons/:id/`, ({ params }) => {
    const { id } = params;
    return HttpResponse.json({ ...mockPerson, id });
  }),

  http.post(`${API_BASE}/persons/`, async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json(
      { ...mockPerson, id: crypto.randomUUID(), ...body },
      { status: 201 }
    );
  }),

  http.patch(`${API_BASE}/persons/:id/`, async ({ request, params }) => {
    const { id } = params;
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json({ ...mockPerson, id, ...body });
  }),

  http.delete(`${API_BASE}/persons/:id/`, () => {
    return new HttpResponse(null, { status: 204 });
  }),

  http.get(`${API_BASE}/persons/:id/relationships/`, () => {
    return HttpResponse.json([mockRelationship]);
  }),

  http.get(`${API_BASE}/persons/:id/anecdotes/`, () => {
    return HttpResponse.json([mockAnecdote]);
  }),

  http.get(`${API_BASE}/persons/:id/photos/`, () => {
    return HttpResponse.json([mockPhoto]);
  }),

  http.get(`${API_BASE}/persons/:id/employments/`, () => {
    return HttpResponse.json([mockEmployment]);
  }),

  http.post(`${API_BASE}/persons/:id/generate_summary/`, ({ params }) => {
    const { id } = params;
    return HttpResponse.json({
      summary: 'AI generated summary',
      person_id: id,
      person_name: mockPerson.full_name,
    });
  }),

  http.post(`${API_BASE}/persons/:id/suggest_tags/`, ({ params }) => {
    const { id } = params;
    return HttpResponse.json({
      suggested_tags: [{ name: 'Friend', reason: 'Close relationship', confidence: 0.9, is_existing: true }],
      person_id: id,
      person_name: mockPerson.full_name,
      current_tags: [],
    });
  }),

  http.post(`${API_BASE}/persons/:id/apply_tags/`, async ({ request, params }) => {
    const { id } = params;
    const body = (await request.json()) as { tags: string[]; create_missing?: boolean };
    return HttpResponse.json({
      applied_tags: body.tags,
      created_tags: [],
      skipped_tags: [],
      person_id: id,
      person_name: mockPerson.full_name,
      current_tags: body.tags,
    });
  }),

  http.post(`${API_BASE}/persons/:id/sync_linkedin/`, ({ params }) => {
    const { id } = params;
    return HttpResponse.json({
      status: 'success',
      person_id: id,
      person_name: mockPerson.full_name,
      synced_count: 2,
      skipped_count: 0,
      errors: [],
      profile: { name: 'John Doe', headline: 'Software Engineer', experiences_count: 2 },
    });
  }),

  // -------------------- Tags --------------------
  http.get(`${API_BASE}/tags/`, () => {
    return HttpResponse.json(paginatedResponse([mockTag]));
  }),

  http.post(`${API_BASE}/tags/`, async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json({ ...mockTag, id: crypto.randomUUID(), ...body }, { status: 201 });
  }),

  // -------------------- Groups --------------------
  http.get(`${API_BASE}/groups/`, () => {
    return HttpResponse.json(paginatedResponse([mockGroup]));
  }),

  http.post(`${API_BASE}/groups/`, async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json({ ...mockGroup, id: crypto.randomUUID(), ...body }, { status: 201 });
  }),

  // -------------------- Relationship Types --------------------
  http.get(`${API_BASE}/relationship-types/`, () => {
    return HttpResponse.json(paginatedResponse([mockRelationshipType]));
  }),

  // -------------------- Relationships --------------------
  http.get(`${API_BASE}/relationships/`, () => {
    return HttpResponse.json(paginatedResponse([mockRelationship]));
  }),

  http.post(`${API_BASE}/relationships/`, async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json(
      { ...mockRelationship, id: crypto.randomUUID(), ...body },
      { status: 201 }
    );
  }),

  http.patch(`${API_BASE}/relationships/:id/`, async ({ request, params }) => {
    const { id } = params;
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json({ ...mockRelationship, id, ...body });
  }),

  http.delete(`${API_BASE}/relationships/:id/`, () => {
    return new HttpResponse(null, { status: 204 });
  }),

  http.get(`${API_BASE}/relationships/graph/`, () => {
    return HttpResponse.json(mockGraphData);
  }),

  // -------------------- Anecdotes --------------------
  http.get(`${API_BASE}/anecdotes/`, () => {
    return HttpResponse.json(paginatedResponse([mockAnecdote]));
  }),

  http.post(`${API_BASE}/anecdotes/`, async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json(
      { ...mockAnecdote, id: crypto.randomUUID(), ...body },
      { status: 201 }
    );
  }),

  http.patch(`${API_BASE}/anecdotes/:id/`, async ({ request, params }) => {
    const { id } = params;
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json({ ...mockAnecdote, id, ...body });
  }),

  http.delete(`${API_BASE}/anecdotes/:id/`, () => {
    return new HttpResponse(null, { status: 204 });
  }),

  // -------------------- Photos --------------------
  http.get(`${API_BASE}/photos/`, () => {
    return HttpResponse.json(paginatedResponse([mockPhoto]));
  }),

  http.get(`${API_BASE}/photos/:id/`, ({ params }) => {
    const { id } = params;
    return HttpResponse.json({ ...mockPhoto, id });
  }),

  http.post(`${API_BASE}/photos/`, async () => {
    return HttpResponse.json({ ...mockPhoto, id: crypto.randomUUID() }, { status: 201 });
  }),

  http.patch(`${API_BASE}/photos/:id/`, async ({ params }) => {
    const { id } = params;
    return HttpResponse.json({ ...mockPhoto, id });
  }),

  http.delete(`${API_BASE}/photos/:id/`, () => {
    return new HttpResponse(null, { status: 204 });
  }),

  http.post(`${API_BASE}/photos/:id/generate_description/`, ({ params }) => {
    const { id } = params;
    return HttpResponse.json({
      photo_id: id,
      ai_description: 'AI generated description of the photo',
      person_context: ['John Doe appears in the photo'],
    });
  }),

  // -------------------- Employments --------------------
  http.get(`${API_BASE}/employments/`, () => {
    return HttpResponse.json(paginatedResponse([mockEmployment]));
  }),

  http.get(`${API_BASE}/employments/:id/`, ({ params }) => {
    const { id } = params;
    return HttpResponse.json({ ...mockEmployment, id });
  }),

  http.post(`${API_BASE}/employments/`, async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json(
      { ...mockEmployment, id: crypto.randomUUID(), ...body },
      { status: 201 }
    );
  }),

  http.patch(`${API_BASE}/employments/:id/`, async ({ request, params }) => {
    const { id } = params;
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json({ ...mockEmployment, id, ...body });
  }),

  http.delete(`${API_BASE}/employments/:id/`, () => {
    return new HttpResponse(null, { status: 204 });
  }),

  // -------------------- Search --------------------
  http.get(`${API_BASE}/search/`, ({ request }) => {
    const url = new URL(request.url);
    const query = url.searchParams.get('q') || '';
    return HttpResponse.json({
      persons: query ? [mockPerson] : [],
      anecdotes: query ? [mockAnecdote] : [],
      query,
    });
  }),

  // -------------------- AI Endpoints --------------------
  http.post(`${API_BASE}/ai/parse-contacts/`, async ({ request }) => {
    const body = (await request.json()) as { text: string };
    return HttpResponse.json({
      persons: [
        {
          first_name: 'Jane',
          last_name: 'Smith',
          nickname: '',
          birthday: null,
          notes: 'Colleague',
          relationship_to_owner: 'colleague',
        },
      ],
    });
  }),

  http.post(`${API_BASE}/ai/bulk-import/`, async ({ request }) => {
    const body = (await request.json()) as { persons: unknown[] };
    return HttpResponse.json({
      created_persons: [{ ...mockPerson, first_name: 'Jane', last_name: 'Smith' }],
      created_relationships: [],
      errors: [],
      summary: {
        persons_created: body.persons.length,
        relationships_created: 0,
        errors_count: 0,
      },
    });
  }),

  http.post(`${API_BASE}/ai/parse-updates/`, async () => {
    return HttpResponse.json({
      updates: [
        {
          match_type: 'name',
          match_value: 'John Doe',
          matched_person_id: mockPerson.id,
          matched_person_name: mockPerson.full_name,
          field_updates: { notes_to_append: 'Additional info' },
          anecdotes: [],
        },
      ],
    });
  }),

  http.post(`${API_BASE}/ai/apply-updates/`, async () => {
    return HttpResponse.json({
      updated_persons: [
        { id: mockPerson.id, full_name: mockPerson.full_name, updates_applied: ['notes'] },
      ],
      created_anecdotes: [],
      errors: [],
      summary: { persons_updated: 1, anecdotes_created: 0, errors_count: 0 },
    });
  }),

  http.post(`${API_BASE}/ai/chat/`, async ({ request }) => {
    const body = (await request.json()) as { question: string };
    return HttpResponse.json({
      answer: 'Based on your contacts, here is my response...',
      question: body.question,
    });
  }),

  http.get(`${API_BASE}/ai/suggest-relationships/`, () => {
    return HttpResponse.json({
      suggestions: [
        {
          person1_id: mockPerson.id,
          person1_name: mockPerson.full_name,
          person2_id: mockOwner.id,
          person2_name: mockOwner.full_name,
          suggested_type: 'colleague',
          confidence: 0.85,
          reason: 'Work at same company',
          evidence: ['Same company in employment'],
        },
      ],
      total_contacts: 10,
      existing_relationships_count: 5,
    });
  }),

  http.post(`${API_BASE}/ai/apply-relationship-suggestion/`, async ({ request }) => {
    const body = (await request.json()) as {
      person1_id: string;
      person2_id: string;
      relationship_type: string;
    };
    return HttpResponse.json({
      id: crypto.randomUUID(),
      person1: body.person1_id,
      person2: body.person2_id,
      relationship_type: body.relationship_type,
      message: 'Relationship created successfully',
    });
  }),

  http.post(`${API_BASE}/ai/smart-search/`, async ({ request }) => {
    const body = (await request.json()) as { query: string };
    return HttpResponse.json({
      query: body.query,
      interpreted_as: body.query,
      search_type: 'mixed',
      persons: [
        {
          id: mockPerson.id,
          full_name: mockPerson.full_name,
          relationship_to_me: 'friend',
          current_job: 'Software Engineer at Acme Corp',
          tags: ['Friend'],
          avatar_url: null,
        },
      ],
      anecdotes: [],
      employments: [],
      counts: { persons: 1, anecdotes: 0, employments: 0 },
    });
  }),

  // -------------------- Export --------------------
  http.get(`${API_BASE}/export/preview/`, ({ request }) => {
    const url = new URL(request.url);
    const entity = url.searchParams.get('entity');

    if (entity) {
      return HttpResponse.json({
        entity_type: entity,
        count: 10,
        available_formats: ['json', 'csv'],
      });
    }

    return HttpResponse.json({
      export_type: 'full',
      counts: {
        persons: 10,
        relationships: 15,
        relationship_types: 38,
        anecdotes: 25,
        photos: 5,
        tags: 8,
        groups: 3,
      },
      total_items: 104,
      available_formats: {
        json: { full_export: true, entity_types: ['persons', 'relationships', 'anecdotes'] },
        csv: { full_export: false, entity_types: ['persons', 'relationships', 'anecdotes'] },
      },
    });
  }),

  http.get(`${API_BASE}/export/`, ({ request }) => {
    const url = new URL(request.url);
    const format = url.searchParams.get('export_format') || 'json';
    const entity = url.searchParams.get('entity');

    const filename = entity
      ? `lifegraph_${entity}.${format}`
      : `lifegraph_export.${format}`;

    const content = format === 'json' ? '{"data": []}' : 'id,name\n1,test';

    return new HttpResponse(content, {
      headers: {
        'Content-Type': format === 'json' ? 'application/json' : 'text/csv',
        'Content-Disposition': `attachment; filename="${filename}"`,
      },
    });
  }),
];

// ============================================================================
// Error Handlers for Testing Error States
// ============================================================================

export const errorHandlers = {
  notFound: http.get(`${API_BASE}/persons/:id/`, () => {
    return HttpResponse.json({ detail: 'Not found.' }, { status: 404 });
  }),

  serverError: http.get(`${API_BASE}/persons/`, () => {
    return HttpResponse.json({ detail: 'Internal server error' }, { status: 500 });
  }),

  validationError: http.post(`${API_BASE}/persons/`, () => {
    return HttpResponse.json(
      { first_name: ['This field is required.'] },
      { status: 400 }
    );
  }),

  unauthorized: http.get(`${API_BASE}/me/`, () => {
    return HttpResponse.json({ detail: 'Authentication required' }, { status: 401 });
  }),
};
