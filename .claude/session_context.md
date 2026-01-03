# LifeGraph - Session Context

> Last Updated: 2026-01-03
> Session: Sprint 2 Implementation (in progress)

## Project Overview

**Name**: LifeGraph
**Purpose**: Personal CRM for long-term relationship memory (20+ years)
**Type**: Self-hosted web application on Ugreen NAS

## Technical Stack (Implemented)

| Layer | Technology | Status |
|-------|------------|--------|
| Frontend | React + TypeScript + Vite | ✅ Scaffolded |
| UI | Tailwind CSS + shadcn/ui patterns | ✅ Configured |
| Backend | Django 5.0 + DRF | ✅ Scaffolded |
| Database | PostgreSQL 16 | ✅ Configured |
| AI | OpenAI API | ⏳ Configured (not implemented) |
| Auth | OAuth2 via Authentik (allauth) | ✅ Configured |
| Task Queue | Celery + Redis | ✅ Configured |
| File Storage | MinIO | ✅ Configured |
| Deployment | Docker Compose | ✅ Ready |
| Audit Logging | django-auditlog | ✅ Configured |
| Full-Text Search | PostgreSQL FTS | ✅ Implemented |

## Sprint 1 Progress (Complete)

| Task | Description | Status |
|------|-------------|--------|
| SETUP-001 | Django project structure | ✅ Complete |
| SETUP-002 | PostgreSQL configuration | ✅ Complete |
| SETUP-003 | Docker Compose setup | ✅ Complete |
| SETUP-004 | React frontend project | ✅ Complete |
| SETUP-005 | OAuth2 authentication | ✅ Complete |
| MODEL-001 | Person model | ✅ Complete |
| MODEL-003 | RelationshipType model | ✅ Complete |
| MODEL-004 | Relationship model | ✅ Complete |

## Sprint 2 Progress (In Progress)

| Task | Description | Status |
|------|-------------|--------|
| SETUP-007 | MinIO bucket initialization | ✅ Complete |
| SETUP-008 | Audit logging system | ✅ Complete |
| MODEL-007 | Photo model with metadata | ✅ Complete |
| MODEL-008 | Employment/Professional model | ✅ Complete |
| API-008 | Full-text search endpoint | ✅ Complete |
| API-009 | CustomField value management | ⏳ Pending |

## Project Structure

```
personal_crm/
├── backend/
│   ├── apps/
│   │   ├── core/          # Tags, Groups, shared models
│   │   └── people/        # Person, Relationship, Anecdote, Photo, Employment
│   ├── lifegraph/         # Django project settings
│   ├── Dockerfile
│   ├── requirements.txt
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── components/    # Layout, UI components
│   │   ├── pages/         # Dashboard, PeopleList, PersonDetail
│   │   ├── services/      # API client
│   │   └── types/         # TypeScript types (includes Photo, Employment)
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml     # Includes MinIO service
├── scripts/
│   └── init-minio.sh      # MinIO bucket initialization
└── .env.example
```

## Key Features Implemented

- **Person Model**: Full fields including contacts (JSON), social links, AI summary
- **Relationship System**: Bidirectional with auto-inverse via signals
- **Custom Fields**: Definition + Value models for flexible person attributes
- **Anecdotes**: Types (memory, joke, quote, note) with person linking
- **Tags & Groups**: Hierarchical organization with colors
- **Photo Model**: File storage with metadata, location, AI description support
- **Employment Model**: Professional history with LinkedIn sync capability
- **API Endpoints**: Full CRUD for all entities with DRF
- **Full-Text Search**: PostgreSQL-powered search across persons, anecdotes, employments
- **Audit Logging**: Complete change tracking via django-auditlog
- **Frontend Shell**: Dashboard, People list/detail, Layout with sidebar

## API Endpoints

- `/api/persons/` - Person CRUD + relationships, anecdotes, photos, employments, history
- `/api/relationship-types/` - Relationship type management
- `/api/relationships/` - Relationship CRUD
- `/api/anecdotes/` - Anecdote CRUD with person linking
- `/api/photos/` - Photo CRUD with person tagging
- `/api/employments/` - Employment history CRUD
- `/api/custom-fields/` - Custom field definition management
- `/api/search/?q=query` - Global full-text search

## Commands Reference

```bash
# Start development
docker-compose up -d

# Run migrations
docker-compose exec backend python manage.py migrate

# Create superuser
docker-compose exec backend python manage.py createsuperuser

# Seed default data
docker-compose exec backend python manage.py seed_relationship_types

# Frontend development (if running outside Docker)
cd frontend && npm install && npm run dev

# Backend shell
docker-compose exec backend python manage.py shell
```

## Session Learnings

- User prefers feature-rich UI over minimal
- Priority is relationships/profiles, then AI features
- LinkedIn first for social integration, Discord later
- Self-hosted on Ugreen NAS with Docker Compose
