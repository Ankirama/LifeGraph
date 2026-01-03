# LifeGraph - Session Context

> Last Updated: 2026-01-03
> Session: Sprint 1 Implementation

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

## Sprint 1 Progress

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

## Project Structure Created

```
personal_crm/
├── backend/
│   ├── apps/
│   │   ├── core/          # Tags, Groups, shared models
│   │   └── people/        # Person, Relationship, Anecdote
│   ├── lifegraph/         # Django project settings
│   ├── Dockerfile
│   ├── requirements.txt
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── components/    # Layout, UI components
│   │   ├── pages/         # Dashboard, PeopleList, PersonDetail
│   │   ├── services/      # API client
│   │   └── types/         # TypeScript types
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
└── .env.example
```

## Key Features Implemented

- **Person Model**: Full fields including contacts (JSON), social links, AI summary
- **Relationship System**: Bidirectional with auto-inverse via signals
- **Custom Fields**: Definition + Value models for flexible person attributes
- **Anecdotes**: Types (memory, joke, quote, note) with person linking
- **Tags & Groups**: Hierarchical organization with colors
- **API Endpoints**: Full CRUD for all entities with DRF
- **Frontend Shell**: Dashboard, People list/detail, Layout with sidebar

## Next Steps

1. Run `docker-compose up -d` to start the development environment
2. Run migrations: `docker-compose exec backend python manage.py migrate`
3. Seed relationship types: `docker-compose exec backend python manage.py seed_relationship_types`
4. Access frontend at http://localhost:5173
5. Access API docs at http://localhost:8000/api/docs/

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
