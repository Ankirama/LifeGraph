/**
 * MSW request handlers for API mocking.
 *
 * Add your mock API handlers here for consistent test fixtures.
 */

import { http, HttpResponse } from 'msw';

const API_BASE = 'http://localhost:8000/api';

// Sample mock data
export const mockPerson = {
  id: '123e4567-e89b-12d3-a456-426614174000',
  first_name: 'John',
  last_name: 'Doe',
  nickname: 'Johnny',
  full_name: 'John Doe',
  birthday: '1990-05-15',
  is_owner: false,
  is_active: true,
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

export const mockDashboard = {
  stats: {
    total_persons: 10,
    total_relationships: 15,
    total_anecdotes: 25,
    total_photos: 5,
  },
  upcoming_birthdays: [],
  recent_anecdotes: [],
  recent_persons: [],
  relationship_distribution: [],
};

// API handlers
export const handlers = [
  // Dashboard
  http.get(`${API_BASE}/dashboard/`, () => {
    return HttpResponse.json(mockDashboard);
  }),

  // Me (Owner)
  http.get(`${API_BASE}/me/`, () => {
    return HttpResponse.json(mockOwner);
  }),

  // Persons list
  http.get(`${API_BASE}/persons/`, () => {
    return HttpResponse.json({
      count: 1,
      next: null,
      previous: null,
      results: [mockPerson],
    });
  }),

  // Person detail
  http.get(`${API_BASE}/persons/:id/`, ({ params }) => {
    const { id } = params;
    return HttpResponse.json({ ...mockPerson, id });
  }),

  // Create person
  http.post(`${API_BASE}/persons/`, async ({ request }) => {
    const body = await request.json() as Record<string, unknown>;
    return HttpResponse.json(
      { ...mockPerson, ...body },
      { status: 201 }
    );
  }),

  // Search
  http.get(`${API_BASE}/search/`, ({ request }) => {
    const url = new URL(request.url);
    const query = url.searchParams.get('q') || '';
    return HttpResponse.json({
      persons: query ? [mockPerson] : [],
      anecdotes: [],
      employments: [],
      query,
    });
  }),
];

// Error handlers for testing error states
export const errorHandlers = [
  http.get(`${API_BASE}/me/`, () => {
    return new HttpResponse(null, { status: 404 });
  }),

  http.get(`${API_BASE}/persons/`, () => {
    return new HttpResponse(null, { status: 500 });
  }),
];
