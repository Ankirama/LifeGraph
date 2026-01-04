// Core types for LifeGraph

export interface Tag {
  id: string
  name: string
  color: string
  description: string
  person_count?: number
  created_at: string
  updated_at: string
}

export interface Group {
  id: string
  name: string
  description: string
  parent: string | null
  color: string
  full_path: string
  children_count: number
  person_count?: number
  created_at: string
  updated_at: string
}

export interface ContactInfo {
  email?: string
  phone?: string
  address?: string
  label: string
}

export interface Person {
  id: string
  first_name: string
  last_name: string
  full_name: string
  nickname: string
  avatar: string | null
  birthday: string | null
  met_date: string | null
  met_context: string
  emails: ContactInfo[]
  phones: ContactInfo[]
  addresses: ContactInfo[]
  linkedin_url: string
  discord_id: string
  notes: string
  is_active: boolean
  is_owner: boolean
  ai_summary: string
  ai_summary_updated: string | null
  last_contact: string | null
  primary_email: string | null
  primary_phone: string | null
  tags: Tag[]
  groups: Group[]
  created_at: string
  updated_at: string
}

export interface PersonListItem {
  id: string
  first_name: string
  last_name: string
  full_name: string
  nickname: string
  avatar: string | null
  birthday: string | null
  primary_email: string | null
  primary_phone: string | null
  tags: Tag[]
  last_contact: string | null
  relationship_to_me: string | null
  created_at: string
}

export interface RelationshipType {
  id: string
  name: string
  inverse_name: string
  category: 'family' | 'professional' | 'social' | 'custom'
  is_symmetric: boolean
  auto_create_inverse: boolean
  created_at: string
  updated_at: string
}

export interface Relationship {
  id: string
  person_a: string
  person_a_name: string
  person_b: string
  person_b_name: string
  relationship_type: string
  relationship_type_name: string
  relationship_type_inverse_name: string
  started_date: string | null
  notes: string
  strength: number | null
  auto_created: boolean
  created_at: string
  updated_at: string
}

export interface Anecdote {
  id: string
  title: string
  content: string
  date: string | null
  location: string
  persons: PersonListItem[]
  anecdote_type: 'memory' | 'joke' | 'quote' | 'note'
  tags: Tag[]
  created_at: string
  updated_at: string
}

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface LocationCoords {
  lat: number
  lng: number
}

export interface Photo {
  id: string
  file: string
  caption: string
  date_taken: string | null
  location: string
  location_coords: LocationCoords | null
  ai_description: string
  detected_faces: unknown[]
  persons: PersonListItem[]
  anecdote: string | null
  created_at: string
  updated_at: string
}

export interface Employment {
  id: string
  person: string
  person_name: string
  company: string
  title: string
  department: string
  start_date: string | null
  end_date: string | null
  is_current: boolean
  location: string
  description: string
  linkedin_synced: boolean
  linkedin_last_sync: string | null
  created_at: string
  updated_at: string
}

export interface CustomFieldDefinition {
  id: string
  name: string
  field_type: 'text' | 'number' | 'date' | 'select' | 'multiselect'
  options: string[]
  is_required: boolean
  order: number
  created_at: string
  updated_at: string
}

export interface CustomFieldValue {
  id: string
  definition: string
  field_name: string
  field_type: string
  value: unknown
}

// Graph visualization types
export interface GraphNode {
  id: string
  label: string
  first_name: string
  last_name: string
  avatar: string | null
}

export interface GraphEdge {
  id: string
  source: string
  target: string
  type: string
  type_name: string
  inverse_name: string
  category: 'family' | 'professional' | 'social' | 'custom'
  strength: number | null
  is_symmetric: boolean
}

export interface GraphRelationshipType {
  id: string
  name: string
  category: 'family' | 'professional' | 'social' | 'custom'
  color: string
}

export interface RelationshipGraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
  relationship_types: GraphRelationshipType[]
  center_person_id: string | null
}
