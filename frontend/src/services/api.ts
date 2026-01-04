import axios from 'axios'
import type {
  Person,
  PersonListItem,
  PaginatedResponse,
  Tag,
  Group,
  RelationshipType,
  Relationship,
  Anecdote,
  Photo,
  Employment,
  RelationshipGraphData,
} from '@/types'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
})

// Request interceptor for CSRF
api.interceptors.request.use((config) => {
  const csrfToken = document.cookie
    .split('; ')
    .find((row) => row.startsWith('csrftoken='))
    ?.split('=')[1]

  if (csrfToken && config.method !== 'get') {
    config.headers['X-CSRFToken'] = csrfToken
  }

  return config
})

// Persons
export const getPersons = async (params?: {
  search?: string
  tag?: string
  group?: string
  page?: number
}): Promise<PaginatedResponse<PersonListItem>> => {
  const { data } = await api.get('/persons/', { params })
  return data
}

export const getPerson = async (id: string): Promise<Person> => {
  const { data } = await api.get(`/persons/${id}/`)
  return data
}

export const createPerson = async (
  person: Partial<Person>
): Promise<Person> => {
  const { data } = await api.post('/persons/', person)
  return data
}

export const updatePerson = async (
  id: string,
  person: Partial<Person>
): Promise<Person> => {
  const { data } = await api.patch(`/persons/${id}/`, person)
  return data
}

export const deletePerson = async (id: string): Promise<void> => {
  await api.delete(`/persons/${id}/`)
}

export const getPersonRelationships = async (
  id: string
): Promise<Relationship[]> => {
  const { data } = await api.get(`/persons/${id}/relationships/`)
  return data
}

export const getPersonAnecdotes = async (id: string): Promise<Anecdote[]> => {
  const { data } = await api.get(`/persons/${id}/anecdotes/`)
  return data
}

// Tags
export const getTags = async (): Promise<PaginatedResponse<Tag>> => {
  const { data } = await api.get('/tags/')
  return data
}

export const createTag = async (tag: Partial<Tag>): Promise<Tag> => {
  const { data } = await api.post('/tags/', tag)
  return data
}

// Groups
export const getGroups = async (): Promise<PaginatedResponse<Group>> => {
  const { data } = await api.get('/groups/')
  return data
}

export const createGroup = async (group: Partial<Group>): Promise<Group> => {
  const { data } = await api.post('/groups/', group)
  return data
}

// Relationship Types
export const getRelationshipTypes = async (): Promise<
  PaginatedResponse<RelationshipType>
> => {
  const { data } = await api.get('/relationship-types/')
  return data
}

// Relationships
export const getRelationships = async (params?: {
  relationship_type?: string
  page?: number
}): Promise<PaginatedResponse<Relationship>> => {
  const { data } = await api.get('/relationships/', { params })
  return data
}

export const createRelationship = async (
  relationship: Partial<Relationship>
): Promise<Relationship> => {
  const { data } = await api.post('/relationships/', relationship)
  return data
}

export const updateRelationship = async (
  id: string,
  relationship: Partial<Relationship>
): Promise<Relationship> => {
  const { data } = await api.patch(`/relationships/${id}/`, relationship)
  return data
}

export const deleteRelationship = async (id: string): Promise<void> => {
  await api.delete(`/relationships/${id}/`)
}

// Anecdotes
export const getAnecdotes = async (params?: {
  person?: string
  search?: string
  anecdote_type?: string
  page?: number
}): Promise<PaginatedResponse<Anecdote>> => {
  const { data } = await api.get('/anecdotes/', { params })
  return data
}

export const createAnecdote = async (
  anecdote: Partial<Anecdote> & { person_ids: string[]; tag_ids?: string[] }
): Promise<Anecdote> => {
  const { data } = await api.post('/anecdotes/', anecdote)
  return data
}

export const updateAnecdote = async (
  id: string,
  anecdote: Partial<Anecdote>
): Promise<Anecdote> => {
  const { data } = await api.patch(`/anecdotes/${id}/`, anecdote)
  return data
}

export const deleteAnecdote = async (id: string): Promise<void> => {
  await api.delete(`/anecdotes/${id}/`)
}

// Photos
export const getPhotos = async (params?: {
  person?: string
  page?: number
}): Promise<PaginatedResponse<Photo>> => {
  const { data } = await api.get('/photos/', { params })
  return data
}

export const getPhoto = async (id: string): Promise<Photo> => {
  const { data } = await api.get(`/photos/${id}/`)
  return data
}

export const uploadPhoto = async (formData: FormData): Promise<Photo> => {
  const { data } = await api.post('/photos/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return data
}

export const updatePhoto = async (
  id: string,
  photo: Partial<Photo> | FormData
): Promise<Photo> => {
  const config = photo instanceof FormData
    ? { headers: { 'Content-Type': 'multipart/form-data' } }
    : {}
  const { data } = await api.patch(`/photos/${id}/`, photo, config)
  return data
}

export const deletePhoto = async (id: string): Promise<void> => {
  await api.delete(`/photos/${id}/`)
}

export interface GeneratePhotoDescriptionResponse {
  photo_id: string
  ai_description: string
  person_context: string[]
}

export const generatePhotoDescription = async (
  photoId: string
): Promise<GeneratePhotoDescriptionResponse> => {
  const { data } = await api.post(`/photos/${photoId}/generate_description/`)
  return data
}

export const getPersonPhotos = async (personId: string): Promise<Photo[]> => {
  const { data } = await api.get(`/persons/${personId}/photos/`)
  return data
}

// Employments
export const getEmployments = async (params?: {
  person?: string
  is_current?: boolean
  page?: number
}): Promise<PaginatedResponse<Employment>> => {
  const { data } = await api.get('/employments/', { params })
  return data
}

export const getEmployment = async (id: string): Promise<Employment> => {
  const { data } = await api.get(`/employments/${id}/`)
  return data
}

export const createEmployment = async (
  employment: Partial<Employment>
): Promise<Employment> => {
  const { data } = await api.post('/employments/', employment)
  return data
}

export const updateEmployment = async (
  id: string,
  employment: Partial<Employment>
): Promise<Employment> => {
  const { data } = await api.patch(`/employments/${id}/`, employment)
  return data
}

export const deleteEmployment = async (id: string): Promise<void> => {
  await api.delete(`/employments/${id}/`)
}

export const getPersonEmployments = async (personId: string): Promise<Employment[]> => {
  const { data } = await api.get(`/persons/${personId}/employments/`)
  return data
}

// LinkedIn Sync
export interface LinkedInSyncResponse {
  status: string
  person_id: string
  person_name: string
  synced_count: number
  skipped_count: number
  errors: string[]
  profile: {
    name: string
    headline: string
    experiences_count: number
  }
}

export const syncLinkedIn = async (
  personId: string
): Promise<LinkedInSyncResponse> => {
  const { data } = await api.post(`/persons/${personId}/sync_linkedin/`)
  return data
}

// Me (Owner profile)
export const getMe = async (): Promise<Person> => {
  const { data } = await api.get('/me/')
  return data
}

export const createMe = async (person: Partial<Person>): Promise<Person> => {
  const { data } = await api.post('/me/', person)
  return data
}

export const updateMe = async (person: Partial<Person>): Promise<Person> => {
  const { data } = await api.patch('/me/', person)
  return data
}

export const updateMeWithAvatar = async (
  person: Partial<Person>,
  avatarFile?: File
): Promise<Person> => {
  const formData = new FormData()

  // Add all person fields to FormData
  Object.entries(person).forEach(([key, value]) => {
    if (value !== null && value !== undefined && value !== '') {
      formData.append(key, String(value))
    }
  })

  // Add avatar file if provided
  if (avatarFile) {
    formData.append('avatar', avatarFile)
  }

  const { data } = await api.patch('/me/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return data
}

export const createMeWithAvatar = async (
  person: Partial<Person>,
  avatarFile?: File
): Promise<Person> => {
  const formData = new FormData()

  // Add all person fields to FormData
  Object.entries(person).forEach(([key, value]) => {
    if (value !== null && value !== undefined && value !== '') {
      formData.append(key, String(value))
    }
  })

  // Add avatar file if provided
  if (avatarFile) {
    formData.append('avatar', avatarFile)
  }

  const { data } = await api.post('/me/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return data
}

// Search
export const globalSearch = async (
  query: string
): Promise<{ persons: PersonListItem[]; anecdotes: Anecdote[] }> => {
  const { data } = await api.get('/search/', { params: { q: query } })
  return data
}

// Health
export const healthCheck = async (): Promise<{ status: string }> => {
  const { data } = await api.get('/health/')
  return data
}

// Dashboard
export interface DashboardStats {
  total_persons: number
  total_relationships: number
  total_anecdotes: number
  total_photos: number
}

export interface UpcomingBirthday {
  id: string
  full_name: string
  birthday: string
  days_until: number
  turning_age: number
  date: string
}

export interface RecentAnecdote {
  id: string
  title: string
  content: string
  anecdote_type: string
  date: string | null
  persons: string[]
  created_at: string
}

export interface RecentPerson {
  id: string
  full_name: string
  relationship_to_me: string | null
  created_at: string
}

export interface RelationshipDistribution {
  name: string
  count: number
}

export interface DashboardResponse {
  stats: DashboardStats
  upcoming_birthdays: UpcomingBirthday[]
  recent_anecdotes: RecentAnecdote[]
  recent_persons: RecentPerson[]
  relationship_distribution: RelationshipDistribution[]
}

export const getDashboard = async (): Promise<DashboardResponse> => {
  const { data } = await api.get('/dashboard/')
  return data
}

// AI Import
export interface ParsedPerson {
  first_name: string
  last_name: string
  nickname: string
  birthday: string | null
  notes: string
  relationship_to_owner: string
}

export interface ParseContactsResponse {
  persons: ParsedPerson[]
}

export interface BulkImportResponse {
  created_persons: PersonListItem[]
  created_relationships: Relationship[]
  errors: string[]
  summary: {
    persons_created: number
    relationships_created: number
    errors_count: number
  }
}

export const parseContactsWithAI = async (
  text: string
): Promise<ParseContactsResponse> => {
  const { data } = await api.post('/ai/parse-contacts/', { text })
  return data
}

export const bulkImportContacts = async (
  persons: ParsedPerson[]
): Promise<BulkImportResponse> => {
  const { data } = await api.post('/ai/bulk-import/', { persons })
  return data
}

// AI Updates for existing contacts
export interface ParsedAnecdote {
  content: string
  title: string
  anecdote_type: 'memory' | 'quote' | 'joke' | 'note'
  date: string | null
  location: string
}

export interface ParsedUpdate {
  match_type: 'relationship' | 'name'
  match_value: string
  matched_person_id: string | null
  matched_person_name: string | null
  field_updates: {
    birthday?: string
    nickname?: string
    notes_to_append?: string
  }
  anecdotes: ParsedAnecdote[]
}

export interface ParseUpdatesResponse {
  updates: ParsedUpdate[]
}

export interface ApplyUpdatesResponse {
  updated_persons: Array<{
    id: string
    full_name: string
    updates_applied: string[]
  }>
  created_anecdotes: Array<{
    id: string
    title: string
    person_name: string
  }>
  errors: string[]
  summary: {
    persons_updated: number
    anecdotes_created: number
    errors_count: number
  }
}

export const parseUpdatesWithAI = async (
  text: string
): Promise<ParseUpdatesResponse> => {
  const { data } = await api.post('/ai/parse-updates/', { text })
  return data
}

export const applyUpdates = async (
  updates: ParsedUpdate[]
): Promise<ApplyUpdatesResponse> => {
  const { data } = await api.post('/ai/apply-updates/', { updates })
  return data
}

// AI Summary
export interface GenerateSummaryResponse {
  summary: string
  person_id: string
  person_name: string
}

export const generatePersonSummary = async (
  personId: string
): Promise<GenerateSummaryResponse> => {
  const { data } = await api.post(`/persons/${personId}/generate_summary/`)
  return data
}

// AI Chat
export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface ChatResponse {
  answer: string
  question: string
}

export const chatWithAI = async (
  question: string,
  history?: ChatMessage[]
): Promise<ChatResponse> => {
  const { data } = await api.post('/ai/chat/', { question, history })
  return data
}

// AI Tag Suggestions
export interface SuggestedTag {
  name: string
  reason: string
  confidence: number
  is_existing: boolean
}

export interface SuggestTagsResponse {
  suggested_tags: SuggestedTag[]
  person_id: string
  person_name: string
  current_tags: string[]
}

export interface ApplyTagsResponse {
  applied_tags: string[]
  created_tags: string[]
  skipped_tags: string[]
  person_id: string
  person_name: string
  current_tags: string[]
}

export const suggestTags = async (
  personId: string
): Promise<SuggestTagsResponse> => {
  const { data } = await api.post(`/persons/${personId}/suggest_tags/`)
  return data
}

export const applyTags = async (
  personId: string,
  tags: string[],
  createMissing: boolean = false
): Promise<ApplyTagsResponse> => {
  const { data } = await api.post(`/persons/${personId}/apply_tags/`, {
    tags,
    create_missing: createMissing,
  })
  return data
}

// Relationship Graph
export const getRelationshipGraph = async (params?: {
  center_id?: string
  depth?: number
  category?: string
}): Promise<RelationshipGraphData> => {
  const { data } = await api.get('/relationships/graph/', { params })
  return data
}

// AI Relationship Suggestions
export interface RelationshipSuggestion {
  person1_id: string
  person1_name: string
  person2_id: string
  person2_name: string
  suggested_type: string
  confidence: number
  reason: string
  evidence: string[]
}

export interface SuggestRelationshipsResponse {
  suggestions: RelationshipSuggestion[]
  total_contacts: number
  existing_relationships_count: number
  message?: string
}

export interface ApplyRelationshipSuggestionResponse {
  id: string
  person1: string
  person2: string
  relationship_type: string
  message: string
}

export const suggestRelationships = async (): Promise<SuggestRelationshipsResponse> => {
  const { data } = await api.get('/ai/suggest-relationships/')
  return data
}

export const applyRelationshipSuggestion = async (
  person1Id: string,
  person2Id: string,
  relationshipType: string
): Promise<ApplyRelationshipSuggestionResponse> => {
  const { data } = await api.post('/ai/apply-relationship-suggestion/', {
    person1_id: person1Id,
    person2_id: person2Id,
    relationship_type: relationshipType,
  })
  return data
}

export default api
