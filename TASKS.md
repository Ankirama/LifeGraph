# LifeGraph - Kanban Tasks

## Epic: Project Setup
> Foundation and infrastructure for the entire project

### Backlog

- [ ] **[SETUP-001]** Initialize Django project with proper structure
  - Create Django project named `lifegraph`
  - Configure settings for dev/prod environments
  - Set up environment variables handling
  - **Labels:** `backend`, `setup`, `priority-critical`

- [ ] **[SETUP-002]** Configure PostgreSQL database connection
  - Add psycopg2 dependency
  - Configure DATABASE_URL parsing
  - Create initial migration structure
  - **Labels:** `backend`, `database`, `priority-critical`

- [ ] **[SETUP-003]** Set up Docker Compose development environment
  - Create Dockerfile for Django backend
  - Create docker-compose.yml with postgres, redis, backend
  - Add volume mounts for development
  - Create .env.example template
  - **Labels:** `devops`, `setup`, `priority-critical`

- [ ] **[SETUP-004]** Initialize React frontend project
  - Create React app with Vite
  - Configure TypeScript
  - Set up folder structure (components, pages, hooks, services)
  - Add Dockerfile for frontend
  - **Labels:** `frontend`, `setup`, `priority-critical`

- [ ] **[SETUP-005]** Configure OAuth2 authentication with Authentik
  - Install django-allauth or social-auth-app-django
  - Configure OAuth2 provider settings
  - Create login/logout flow
  - Add session management
  - **Labels:** `backend`, `security`, `priority-critical`

- [ ] **[SETUP-006]** Set up Celery for background tasks
  - Configure Celery with Redis broker
  - Create celery.py configuration
  - Add celery-beat for scheduled tasks
  - Create worker Dockerfile/service
  - **Labels:** `backend`, `infrastructure`, `priority-high`

- [ ] **[SETUP-007]** Configure MinIO for file storage
  - Add MinIO service to docker-compose
  - Configure django-storages with S3 backend
  - Create bucket initialization script
  - **Labels:** `devops`, `infrastructure`, `priority-high`

- [ ] **[SETUP-008]** Set up audit logging system
  - Install django-auditlog or django-simple-history
  - Configure login/logout event logging
  - Add middleware for request logging
  - **Labels:** `backend`, `security`, `priority-high`

---

## Epic: Core Data Models
> Database models and business logic for people and relationships

### Backlog

- [ ] **[MODEL-001]** Create Person model with core fields
  - Basic fields: name, nickname, birthday, avatar
  - Contact fields: emails, phones (JSON or related)
  - Social fields: linkedin_url, discord_id
  - Meta fields: created_at, updated_at, last_contact
  - **Labels:** `backend`, `database`, `priority-critical`

- [ ] **[MODEL-002]** Create CustomField system for Person
  - CustomFieldDefinition model (name, type, options)
  - CustomFieldValue model (person, definition, value)
  - Support types: text, number, date, select, multi-select
  - **Labels:** `backend`, `database`, `priority-high`

- [ ] **[MODEL-003]** Create RelationshipType model
  - Fields: name, inverse_name, category, is_symmetric
  - Auto-create flag for inverse relationships
  - Seed default types (spouse, parent, friend, colleague, etc.)
  - **Labels:** `backend`, `database`, `priority-critical`

- [ ] **[MODEL-004]** Create Relationship model with bidirectional support
  - Link two persons with relationship type
  - Auto-create inverse for symmetric relationships
  - Handle asymmetric relationships (parent/child)
  - Add started_date, notes, strength fields
  - **Labels:** `backend`, `database`, `priority-critical`

- [ ] **[MODEL-005]** Create Group and Tag models
  - Group model for categorizing people
  - Tag model for flexible labeling
  - Many-to-many relationships with Person
  - **Labels:** `backend`, `database`, `priority-high`

- [ ] **[MODEL-006]** Create Anecdote/Memory model
  - Link to Person (and optionally multiple persons)
  - Fields: title, content, date, location
  - Support for rich text content
  - **Labels:** `backend`, `database`, `priority-critical`

- [ ] **[MODEL-007]** Create Photo model with metadata
  - File storage reference (MinIO)
  - Fields: caption, date_taken, location
  - Link to persons (many-to-many)
  - AI metadata fields: description, detected_faces
  - **Labels:** `backend`, `database`, `priority-high`

- [ ] **[MODEL-008]** Create Employment/Professional model
  - Link to Person
  - Fields: company, title, start_date, end_date, is_current
  - LinkedIn sync metadata
  - **Labels:** `backend`, `database`, `priority-high`

---

## Epic: Backend API
> REST API endpoints for all operations

### Backlog

- [ ] **[API-001]** Set up Django REST Framework
  - Install and configure DRF
  - Set up authentication classes
  - Configure pagination, filtering
  - Set up OpenAPI/Swagger documentation
  - **Labels:** `backend`, `api`, `priority-critical`

- [ ] **[API-002]** Create Person CRUD endpoints
  - GET /api/v1/persons/ (list with search/filter)
  - POST /api/v1/persons/ (create)
  - GET /api/v1/persons/{id}/ (detail)
  - PUT/PATCH /api/v1/persons/{id}/ (update)
  - DELETE /api/v1/persons/{id}/ (soft delete)
  - **Labels:** `backend`, `api`, `priority-critical`

- [ ] **[API-003]** Create Relationship endpoints
  - GET /api/v1/relationships/ (list)
  - POST /api/v1/relationships/ (create with auto-inverse)
  - GET /api/v1/persons/{id}/relationships/ (person's relationships)
  - DELETE /api/v1/relationships/{id}/ (delete pair)
  - **Labels:** `backend`, `api`, `priority-critical`

- [ ] **[API-004]** Create RelationshipType management endpoints
  - GET /api/v1/relationship-types/ (list)
  - POST /api/v1/relationship-types/ (create custom)
  - **Labels:** `backend`, `api`, `priority-high`

- [ ] **[API-005]** Create Anecdote CRUD endpoints
  - Full CRUD for anecdotes
  - Filter by person, date range, search content
  - **Labels:** `backend`, `api`, `priority-critical`

- [ ] **[API-006]** Create Group and Tag endpoints
  - CRUD for groups and tags
  - Bulk assign/remove from persons
  - **Labels:** `backend`, `api`, `priority-high`

- [ ] **[API-007]** Create Photo upload and management endpoints
  - POST /api/v1/photos/ (upload with metadata)
  - Link photos to persons
  - GET with filtering by person, date, location
  - **Labels:** `backend`, `api`, `priority-high`

- [ ] **[API-008]** Create search endpoint
  - GET /api/v1/search/?q=query
  - Search across persons, anecdotes, tags
  - Return grouped results
  - **Labels:** `backend`, `api`, `priority-high`

- [ ] **[API-009]** Create CustomField management endpoints
  - CRUD for field definitions
  - Values managed through Person endpoints
  - **Labels:** `backend`, `api`, `priority-medium`

---

## Epic: Frontend Core
> React application foundation and core components

### Backlog

- [ ] **[FE-001]** Set up React project structure
  - Configure routing (React Router)
  - Set up API client (axios/fetch wrapper)
  - Configure React Query for data fetching
  - Set up global state if needed (Zustand)
  - **Labels:** `frontend`, `setup`, `priority-critical`

- [ ] **[FE-002]** Implement OAuth2 login flow
  - Redirect to Authentik
  - Handle callback and token storage
  - Protected route wrapper
  - Logout functionality
  - **Labels:** `frontend`, `auth`, `priority-critical`

- [ ] **[FE-003]** Set up UI component library
  - Install shadcn/ui or Mantine
  - Configure theming (dark/light mode)
  - Create base layout components
  - **Labels:** `frontend`, `ui`, `priority-critical`

- [ ] **[FE-004]** Create main layout with navigation
  - Sidebar with navigation
  - Header with search and user menu
  - Responsive layout
  - **Labels:** `frontend`, `ui`, `priority-critical`

- [ ] **[FE-005]** Create Dashboard page
  - Quick stats (total people, recent contacts)
  - Recent anecdotes
  - Upcoming birthdays
  - Quick add shortcuts
  - **Labels:** `frontend`, `feature`, `priority-high`

- [ ] **[FE-006]** Create People list page
  - Grid/list view toggle
  - Search and filter sidebar
  - Sort options (name, last contact, created)
  - Pagination
  - **Labels:** `frontend`, `feature`, `priority-critical`

- [ ] **[FE-007]** Create Person detail page
  - Profile header with avatar, name, key info
  - Tabs: Overview, Relationships, Anecdotes, Photos, Timeline
  - Edit mode toggle
  - **Labels:** `frontend`, `feature`, `priority-critical`

- [ ] **[FE-008]** Create Person form (create/edit)
  - All core fields with validation
  - Custom fields support
  - Avatar upload
  - Contact info management (add/remove emails, phones)
  - **Labels:** `frontend`, `feature`, `priority-critical`

- [ ] **[FE-009]** Create Relationship management UI
  - Add relationship modal
  - Relationship type selector
  - Visual relationship display on person page
  - **Labels:** `frontend`, `feature`, `priority-critical`

- [ ] **[FE-010]** Create Anecdote components
  - Anecdote card display
  - Create/edit modal or page
  - Rich text editor for content
  - Date and person linking
  - **Labels:** `frontend`, `feature`, `priority-critical`

- [ ] **[FE-011]** Create Groups and Tags management
  - Group list and CRUD
  - Tag management with colors
  - Assign to persons UI
  - **Labels:** `frontend`, `feature`, `priority-high`

- [ ] **[FE-012]** Create global search interface
  - Search bar in header
  - Results dropdown with categories
  - Full search results page
  - **Labels:** `frontend`, `feature`, `priority-high`

- [ ] **[FE-013]** Create Photo gallery components
  - Photo upload with drag-drop
  - Gallery view on person page
  - Photo detail modal with metadata
  - Person tagging in photos
  - **Labels:** `frontend`, `feature`, `priority-high`

---

## Epic: AI Integration
> OpenAI-powered features for summaries and chat

### Backlog

- [ ] **[AI-001]** Set up OpenAI client in backend
  - Configure API key securely
  - Create base service class
  - Add rate limiting and error handling
  - **Labels:** `backend`, `ai`, `priority-critical`

- [ ] **[AI-002]** Implement Person summary generation
  - Create prompt template for person summaries
  - Aggregate all person data (profile, anecdotes, relationships)
  - Generate and store summary
  - Add refresh/regenerate capability
  - **Labels:** `backend`, `ai`, `priority-critical`

- [ ] **[AI-003]** Create AI summary API endpoint
  - POST /api/v1/persons/{id}/generate-summary/
  - GET /api/v1/persons/{id}/summary/
  - **Labels:** `backend`, `api`, `priority-high`

- [ ] **[AI-004]** Implement auto-tagging service
  - Analyze person data and anecdotes
  - Suggest relevant tags
  - Batch processing for existing data
  - **Labels:** `backend`, `ai`, `priority-medium`

- [ ] **[AI-005]** Create conversational interface backend
  - Chat endpoint with context
  - System prompt with person database context
  - Query understanding and response generation
  - **Labels:** `backend`, `ai`, `priority-high`

- [ ] **[AI-006]** Create chat UI component
  - Chat panel/modal
  - Message history
  - Streaming responses
  - Quick question suggestions
  - **Labels:** `frontend`, `ai`, `priority-high`

- [ ] **[AI-007]** Implement photo AI description
  - Send photos to OpenAI Vision
  - Generate and store descriptions
  - Face detection/recognition hints
  - **Labels:** `backend`, `ai`, `priority-medium`

---

## Epic: LinkedIn Integration
> Automated job information sync

### Backlog

- [ ] **[LINKEDIN-001]** Research and choose LinkedIn scraping approach
  - Evaluate linkedin-api library
  - Assess cookie-based authentication
  - Document legal/ToS considerations
  - **Labels:** `research`, `integration`, `priority-high`

- [ ] **[LINKEDIN-002]** Implement LinkedIn profile fetcher
  - Create LinkedIn service class
  - Fetch profile data from URL
  - Parse job history, current position
  - Handle authentication and rate limits
  - **Labels:** `backend`, `integration`, `priority-high`

- [ ] **[LINKEDIN-003]** Create LinkedIn sync Celery task
  - Scheduled task (daily/weekly configurable)
  - Iterate through persons with LinkedIn URLs
  - Update employment records
  - Handle errors and retries
  - **Labels:** `backend`, `tasks`, `priority-high`

- [ ] **[LINKEDIN-004]** Create LinkedIn sync management UI
  - Status display per person
  - Manual sync trigger
  - Last sync timestamp
  - Error display
  - **Labels:** `frontend`, `integration`, `priority-medium`

- [ ] **[LINKEDIN-005]** Add LinkedIn URL field with validation
  - URL format validation
  - Profile preview on add
  - Duplicate detection
  - **Labels:** `backend`, `frontend`, `priority-medium`

---

## Epic: Security & Production
> Security hardening and production readiness

### Backlog

- [ ] **[SEC-001]** Implement data encryption at rest
  - Configure PostgreSQL encryption
  - Encrypt sensitive fields (API keys, tokens)
  - Secure MinIO bucket encryption
  - **Labels:** `security`, `devops`, `priority-high`

- [ ] **[SEC-002]** Add CSRF and security headers
  - Configure Django security middleware
  - Add CSP headers
  - CORS configuration
  - **Labels:** `security`, `backend`, `priority-high`

- [ ] **[SEC-003]** Create backup system
  - PostgreSQL daily backup script
  - MinIO backup script
  - Retention policy (30 days)
  - Backup verification
  - **Labels:** `devops`, `priority-high`

- [ ] **[SEC-004]** Add rate limiting
  - API endpoint rate limiting
  - Login attempt limiting
  - AI endpoint rate limiting
  - **Labels:** `security`, `backend`, `priority-medium`

- [ ] **[SEC-005]** Create production docker-compose
  - Production-ready configuration
  - Resource limits
  - Health checks
  - Logging configuration
  - **Labels:** `devops`, `priority-high`

- [ ] **[SEC-006]** Documentation for deployment
  - Reverse proxy configuration (Traefik/Nginx)
  - Authentik setup guide
  - Environment variables documentation
  - **Labels:** `documentation`, `priority-high`

---

## Epic: Phase 2+ (Future)
> Features planned for later phases

### Icebox

- [ ] **[FUTURE-001]** Discord message import
  - GDPR export parser
  - Message summarization with AI
  - Conversation linking to persons
  - **Labels:** `integration`, `phase-4`

- [ ] **[FUTURE-002]** Relationship graph visualization
  - Force-directed graph display
  - Interactive exploration
  - Filtering by relationship type
  - **Labels:** `frontend`, `phase-4`

- [ ] **[FUTURE-003]** Contact reminder system
  - "Haven't contacted in X days" detection
  - Notification/reminder display
  - Configurable thresholds per person
  - **Labels:** `feature`, `phase-4`

- [ ] **[FUTURE-004]** Timeline visualization
  - Chronological view of all interactions
  - Filter by person, type, date range
  - Visual timeline component
  - **Labels:** `frontend`, `phase-3`

- [ ] **[FUTURE-005]** Calendar integration
  - Google Calendar / CalDAV sync
  - Auto-create anecdotes from meetings
  - Attendee detection
  - **Labels:** `integration`, `phase-4`

- [ ] **[FUTURE-006]** Mobile responsive optimization
  - Mobile-first CSS updates
  - Touch-friendly interactions
  - PWA capabilities
  - **Labels:** `frontend`, `phase-3`

- [ ] **[FUTURE-007]** Import/Export functionality
  - JSON full export
  - CSV export for persons
  - Import from Monica HQ format
  - **Labels:** `feature`, `phase-2`

---

## Summary

| Epic | Tasks | Priority |
|------|-------|----------|
| Project Setup | 8 | Critical |
| Core Data Models | 8 | Critical |
| Backend API | 9 | Critical |
| Frontend Core | 13 | Critical |
| AI Integration | 7 | High |
| LinkedIn Integration | 5 | High |
| Security & Production | 6 | High |
| Phase 2+ (Future) | 7 | Low |

**Total Tasks: 63**

### Suggested Sprint Organization

**Sprint 1 (Foundation):**
- SETUP-001 to SETUP-005
- MODEL-001, MODEL-003, MODEL-004

**Sprint 2 (Core Backend):**
- SETUP-006 to SETUP-008
- MODEL-002, MODEL-005, MODEL-006
- API-001 to API-005

**Sprint 3 (Core Frontend):**
- FE-001 to FE-010
- API-006 to API-009

**Sprint 4 (Features + AI):**
- FE-011 to FE-013
- AI-001 to AI-003
- MODEL-007, MODEL-008

**Sprint 5 (Intelligence):**
- AI-004 to AI-007
- LINKEDIN-001 to LINKEDIN-005

**Sprint 6 (Production):**
- SEC-001 to SEC-006
- Final testing and deployment
