# LifeGraph - Product Requirements Document

> Personal CRM for long-term relationship memory

## Executive Summary

**Project Name:** LifeGraph
**Version:** 1.0
**Last Updated:** 2025-01-03
**Status:** Planning Complete

### Vision Statement

LifeGraph is a self-hosted personal CRM designed to help you never forget anyone or anything about the people in your life. Unlike traditional CRMs focused on sales, LifeGraph emphasizes personal relationships, memories, and long-term knowledge retention - designed to be your relationship memory for 20+ years.

### Problem Statement

- Traditional contact apps only store basic information (name, phone, email)
- Memory of personal details (jokes, stories, family members) fades over time
- No centralized place to capture relationship context and history
- Existing solutions (like MonicaHQ) lack AI capabilities and active development

### Solution

A feature-rich, self-hosted web application that:
- Stores comprehensive information about people in your life
- Captures anecdotes, memories, and personal details
- Maps relationships between people
- Uses AI to summarize and make information accessible
- Syncs with professional networks (LinkedIn) for up-to-date info
- Provides a conversational interface to query your relationship data

---

## Technical Specifications

### Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| Frontend | React + TypeScript | Modern, component-based, strong typing |
| UI Library | shadcn/ui or Mantine | Feature-rich, accessible, customizable |
| State | React Query + Zustand | Server state + client state management |
| Backend | Django + DRF | Batteries-included, mature ecosystem |
| Database | PostgreSQL 16 | Robust, JSON support, full-text search |
| Task Queue | Celery + Redis | Async tasks, scheduling |
| File Storage | MinIO | S3-compatible, self-hosted |
| AI | OpenAI API | GPT-4 for summaries, chat, vision |
| Auth | OAuth2 (Authentik) | SSO with existing infrastructure |
| Deployment | Docker Compose | Self-hosted on NAS |

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      SYSTEM ARCHITECTURE                        │
└─────────────────────────────────────────────────────────────────┘

                    ┌─────────────────┐
                    │   Authentik     │
                    │   (OAuth2/SSO)  │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Reverse Proxy  │
                    │  (Traefik)      │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│    React      │   │   Django      │   │   Celery      │
│   Frontend    │   │   Backend     │   │   Workers     │
│   (Nginx)     │   │   (Gunicorn)  │   │   (Beat)      │
└───────┬───────┘   └───────┬───────┘   └───────┬───────┘
        │                   │                   │
        │           ┌───────┴───────┐           │
        │           │               │           │
        │           ▼               ▼           │
        │   ┌─────────────┐ ┌─────────────┐     │
        │   │ PostgreSQL  │ │   Redis     │◀────┘
        │   │             │ │             │
        │   └─────────────┘ └─────────────┘
        │
        │           ┌─────────────┐
        └──────────▶│   MinIO     │
                    │             │
                    └─────────────┘

External:
┌─────────────┐   ┌─────────────┐
│  OpenAI     │   │  LinkedIn   │
│  API        │   │  (Scraping) │
└─────────────┘   └─────────────┘
```

### Security Model

```
Layer 1: Network
├── TLS termination at reverse proxy
├── Rate limiting (nginx/traefik)
└── Optional IP allowlisting

Layer 2: Authentication
├── OAuth2 via Authentik (OIDC)
├── Session-based authentication
├── CSRF protection enabled
└── Secure cookie configuration

Layer 3: Data Protection
├── PostgreSQL with encryption at rest
├── Encrypted sensitive fields (fernet)
├── MinIO server-side encryption
└── Environment-based secrets

Layer 4: Audit
├── All logins logged
├── Data modifications tracked
├── API access logged with IP
└── 90-day log retention
```

---

## Data Model

### Core Entities

#### Person
```python
class Person(models.Model):
    # Identity
    id = UUIDField(primary_key=True)
    name = CharField(max_length=255)
    nickname = CharField(max_length=100, blank=True)
    avatar = ImageField(upload_to='avatars/', blank=True)

    # Dates
    birthday = DateField(null=True, blank=True)
    met_date = DateField(null=True, blank=True)
    met_context = TextField(blank=True)  # "Tech conference 2020"

    # Contact (JSON fields for flexibility)
    emails = JSONField(default=list)  # [{"email": "...", "label": "work"}]
    phones = JSONField(default=list)
    addresses = JSONField(default=list)

    # Social
    linkedin_url = URLField(blank=True)
    discord_id = CharField(max_length=50, blank=True)

    # Metadata
    notes = TextField(blank=True)  # General notes
    is_active = BooleanField(default=True)  # Soft delete

    # AI
    ai_summary = TextField(blank=True)
    ai_summary_updated = DateTimeField(null=True)

    # Timestamps
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    last_contact = DateTimeField(null=True)

    # Relations
    groups = ManyToManyField('Group', related_name='persons')
    tags = ManyToManyField('Tag', related_name='persons')
```

#### Relationship
```python
class RelationshipType(models.Model):
    id = UUIDField(primary_key=True)
    name = CharField(max_length=100)  # "spouse"
    inverse_name = CharField(max_length=100, blank=True)  # "spouse" (same for symmetric)
    category = CharField(choices=CATEGORY_CHOICES)  # family/professional/social/custom
    is_symmetric = BooleanField(default=False)
    auto_create_inverse = BooleanField(default=True)

class Relationship(models.Model):
    id = UUIDField(primary_key=True)
    person_a = ForeignKey(Person, related_name='relationships_as_a')
    person_b = ForeignKey(Person, related_name='relationships_as_b')
    relationship_type = ForeignKey(RelationshipType)

    # Metadata
    started_date = DateField(null=True, blank=True)
    notes = TextField(blank=True)
    strength = IntegerField(null=True)  # 1-5 scale

    # System
    auto_created = BooleanField(default=False)  # True if inverse
    created_at = DateTimeField(auto_now_add=True)
```

#### Anecdote
```python
class Anecdote(models.Model):
    id = UUIDField(primary_key=True)
    title = CharField(max_length=255, blank=True)
    content = TextField()  # Rich text / Markdown
    date = DateField(null=True, blank=True)
    location = CharField(max_length=255, blank=True)

    # Relations
    persons = ManyToManyField(Person, related_name='anecdotes')

    # Categorization
    anecdote_type = CharField(choices=TYPE_CHOICES)  # memory/joke/quote/note
    tags = ManyToManyField('Tag', related_name='anecdotes')

    # Timestamps
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
```

#### Photo
```python
class Photo(models.Model):
    id = UUIDField(primary_key=True)
    file = FileField(upload_to='photos/')
    caption = CharField(max_length=500, blank=True)

    # Metadata
    date_taken = DateTimeField(null=True)
    location = CharField(max_length=255, blank=True)
    location_coords = JSONField(null=True)  # {lat, lng}

    # AI
    ai_description = TextField(blank=True)
    detected_faces = JSONField(default=list)

    # Relations
    persons = ManyToManyField(Person, related_name='photos')
    anecdote = ForeignKey(Anecdote, null=True, related_name='photos')

    # Timestamps
    created_at = DateTimeField(auto_now_add=True)
```

#### Custom Fields
```python
class CustomFieldDefinition(models.Model):
    id = UUIDField(primary_key=True)
    name = CharField(max_length=100)
    field_type = CharField(choices=FIELD_TYPES)  # text/number/date/select/multiselect
    options = JSONField(default=list)  # For select types
    is_required = BooleanField(default=False)
    order = IntegerField(default=0)

class CustomFieldValue(models.Model):
    person = ForeignKey(Person, related_name='custom_field_values')
    definition = ForeignKey(CustomFieldDefinition)
    value = JSONField()  # Flexible storage
```

### Default Relationship Types

| Name | Inverse | Category | Symmetric |
|------|---------|----------|-----------|
| spouse | spouse | family | Yes |
| partner | partner | family | Yes |
| parent | child | family | No |
| sibling | sibling | family | Yes |
| grandparent | grandchild | family | No |
| uncle/aunt | nephew/niece | family | No |
| cousin | cousin | family | Yes |
| in-law | in-law | family | Yes |
| friend | friend | social | Yes |
| close friend | close friend | social | Yes |
| acquaintance | acquaintance | social | Yes |
| neighbor | neighbor | social | Yes |
| colleague | colleague | professional | Yes |
| manager | report | professional | No |
| mentor | mentee | professional | No |
| client | provider | professional | No |

---

## Feature Specifications

### Phase 1: MVP (Core Value)

#### F1.1 Person Management
- **Create Person:** Form with all core fields, avatar upload
- **Edit Person:** Inline editing, field-by-field updates
- **Delete Person:** Soft delete with confirmation
- **View Person:** Detail page with all information
- **List Persons:** Grid/list view, search, filter, sort

#### F1.2 Relationship Management
- **Add Relationship:** Select person, type, optional metadata
- **Auto-Inverse:** System creates inverse for symmetric types
- **View Relationships:** Visual display on person page
- **Remove Relationship:** Deletes both sides

#### F1.3 Anecdotes System
- **Create Anecdote:** Title, rich content, date, link to persons
- **Types:** Memory, joke, quote, note
- **View on Person:** Chronological list on person page
- **Search:** Full-text search across anecdotes

#### F1.4 Groups and Tags
- **Groups:** Hierarchical organization (Family, Work > Company A)
- **Tags:** Flat labels with colors
- **Assignment:** Easy add/remove from person page
- **Filtering:** Filter person list by group/tag

#### F1.5 Search
- **Global Search:** Search bar in header
- **Scope:** Persons (name, notes), anecdotes (content)
- **Results:** Grouped by type, quick navigation

#### F1.6 Authentication
- **OAuth2 Login:** Redirect to Authentik
- **Session Management:** Secure, configurable timeout
- **Audit:** All logins logged

### Phase 2: Intelligence

#### F2.1 AI Summaries
- **Generate Summary:** Button on person page
- **Auto-Refresh:** Option to regenerate periodically
- **Summary Content:** "Who is X?" natural language summary
- **Data Sources:** Profile, relationships, anecdotes

#### F2.2 Conversational Interface
- **Chat Panel:** Slide-out or modal
- **Queries:** "What does X work on?", "When did I meet Y?"
- **Context:** AI has access to full database
- **Suggestions:** Pre-defined quick questions

#### F2.3 Auto-Tagging
- **Suggestion:** AI suggests tags based on content
- **Batch Processing:** Analyze existing persons
- **Review Flow:** Accept/reject suggestions

#### F2.4 LinkedIn Sync
- **Connect:** Add LinkedIn URL to person
- **Sync:** Scheduled task fetches profile
- **Data:** Current job, company, title
- **Status:** Last sync time, error display

### Phase 3: Rich Media

#### F3.1 Photo Management
- **Upload:** Drag-drop, multiple files
- **Metadata:** Caption, date, location
- **Person Linking:** Tag persons in photos
- **Gallery:** Grid view on person page

#### F3.2 AI Photo Features
- **Description:** Auto-generate from image
- **Face Hints:** Detect faces for tagging assistance
- **Bulk Processing:** Process uploaded photos

#### F3.3 Location Tagging
- **Photos:** Extract or manual location
- **Anecdotes:** Add location to memories
- **Map View:** (Future) See photos on map

### Phase 4: Advanced

#### F4.1 Discord Import
- **Method:** GDPR export import
- **Processing:** AI summarizes conversations
- **Linking:** Match to persons
- **Privacy:** Process then delete raw messages

#### F4.2 Contact Reminders
- **Detection:** Track last_contact field
- **Alerts:** "Haven't contacted X in Y days"
- **Configuration:** Per-person thresholds

#### F4.3 Relationship Graph
- **Visualization:** Force-directed graph
- **Interaction:** Click to navigate
- **Filtering:** By relationship type, group

---

## API Specification

### Base URL
```
/api/v1/
```

### Authentication
All endpoints require OAuth2 Bearer token.

### Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /persons/ | List persons |
| POST | /persons/ | Create person |
| GET | /persons/{id}/ | Get person detail |
| PATCH | /persons/{id}/ | Update person |
| DELETE | /persons/{id}/ | Delete person |
| GET | /persons/{id}/relationships/ | Person's relationships |
| POST | /persons/{id}/generate-summary/ | Generate AI summary |
| GET | /relationships/ | List all relationships |
| POST | /relationships/ | Create relationship |
| DELETE | /relationships/{id}/ | Delete relationship |
| GET | /relationship-types/ | List relationship types |
| POST | /relationship-types/ | Create custom type |
| GET | /anecdotes/ | List anecdotes |
| POST | /anecdotes/ | Create anecdote |
| GET | /anecdotes/{id}/ | Get anecdote detail |
| PATCH | /anecdotes/{id}/ | Update anecdote |
| DELETE | /anecdotes/{id}/ | Delete anecdote |
| GET | /groups/ | List groups |
| POST | /groups/ | Create group |
| GET | /tags/ | List tags |
| POST | /tags/ | Create tag |
| POST | /photos/ | Upload photo |
| GET | /photos/ | List photos |
| GET | /search/ | Global search |
| POST | /ai/chat/ | Conversational query |

---

## UI/UX Specifications

### Design Principles
- **Feature-Rich:** Dense information display, multiple panels
- **Desktop-First:** Optimized for large screens
- **Dark Mode:** Support for dark theme
- **Keyboard Navigation:** Power user shortcuts

### Key Screens

#### Dashboard
```
┌─────────────────────────────────────────────────────────────────┐
│  🔍 Search...                                    [User] [⚙️]    │
├───────────────┬─────────────────────────────────────────────────┤
│               │                                                 │
│  📊 Dashboard │   ┌─────────────┐  ┌─────────────┐             │
│  👥 People    │   │ 127 People  │  │ 12 Upcoming │             │
│  🔗 Relations │   │             │  │ Birthdays   │             │
│  📝 Anecdotes │   └─────────────┘  └─────────────┘             │
│  📸 Photos    │                                                 │
│  🏷️ Tags      │   Recent Anecdotes                             │
│  ⚙️ Settings  │   ├── Funny story with Alice (2 days ago)      │
│               │   ├── Meeting notes with Bob (1 week ago)      │
│               │   └── Birthday party memory (2 weeks ago)      │
│               │                                                 │
└───────────────┴─────────────────────────────────────────────────┘
```

#### Person Detail
```
┌─────────────────────────────────────────────────────────────────┐
│  ← Back                                          [Edit] [...]  │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────┐                                                       │
│  │Avatar│  Alice Smith                                          │
│  │      │  🎂 March 15 • 📍 San Francisco                       │
│  └──────┘  🏢 Engineer at TechCorp                              │
│                                                                 │
│  [Overview] [Relationships] [Anecdotes] [Photos] [Timeline]    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  🤖 AI Summary                                   [Regenerate]  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Alice is a close friend you met at a tech conference    │   │
│  │ in 2020. She works as a senior engineer at TechCorp...  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  📝 Quick Facts                                                 │
│  • Favorite food: Sushi                                        │
│  • Kids: Emma (5), Jake (3)                                    │
│  • Inside joke: "Remember the airport incident"                │
│                                                                 │
│  🔗 Relationships                                              │
│  ├── 💑 Bob Smith (spouse)                                     │
│  ├── 👶 Emma Smith (child)                                     │
│  └── 👥 Carol Jones (colleague)                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Deployment Specifications

### Docker Compose (Production)
```yaml
version: '3.8'

services:
  frontend:
    image: lifegraph-frontend:latest
    build: ./frontend
    restart: unless-stopped
    depends_on:
      - backend
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.lifegraph.rule=Host(`lifegraph.yourdomain.com`)"

  backend:
    image: lifegraph-backend:latest
    build: ./backend
    restart: unless-stopped
    environment:
      - DATABASE_URL=postgresql://lifegraph:${DB_PASSWORD}@db/lifegraph
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - OAUTH2_CLIENT_ID=${OAUTH2_CLIENT_ID}
      - OAUTH2_CLIENT_SECRET=${OAUTH2_CLIENT_SECRET}
      - MINIO_ENDPOINT=minio:9000
      - MINIO_ACCESS_KEY=${MINIO_ACCESS_KEY}
      - MINIO_SECRET_KEY=${MINIO_SECRET_KEY}
    depends_on:
      - db
      - redis
      - minio

  worker:
    image: lifegraph-backend:latest
    command: celery -A lifegraph worker -l INFO
    restart: unless-stopped
    environment:
      # Same as backend
    depends_on:
      - db
      - redis

  scheduler:
    image: lifegraph-backend:latest
    command: celery -A lifegraph beat -l INFO
    restart: unless-stopped
    depends_on:
      - db
      - redis

  db:
    image: postgres:16-alpine
    restart: unless-stopped
    environment:
      - POSTGRES_DB=lifegraph
      - POSTGRES_USER=lifegraph
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U lifegraph"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    volumes:
      - redis_data:/data

  minio:
    image: minio/minio
    restart: unless-stopped
    command: server /data --console-address ":9001"
    environment:
      - MINIO_ROOT_USER=${MINIO_ACCESS_KEY}
      - MINIO_ROOT_PASSWORD=${MINIO_SECRET_KEY}
    volumes:
      - minio_data:/data

volumes:
  postgres_data:
  redis_data:
  minio_data:
```

### Resource Requirements

| Service | CPU | Memory | Storage |
|---------|-----|--------|---------|
| Frontend | 0.1 | 128MB | - |
| Backend | 0.5 | 512MB | - |
| Worker | 0.3 | 256MB | - |
| PostgreSQL | 0.5 | 512MB | 10GB+ |
| Redis | 0.1 | 128MB | 1GB |
| MinIO | 0.2 | 256MB | 50GB+ |
| **Total** | **1.7** | **~1.8GB** | **61GB+** |

### Backup Strategy

```bash
#!/bin/bash
# /scripts/backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=/backups

# PostgreSQL
docker exec lifegraph-db pg_dump -U lifegraph lifegraph | \
  gzip > $BACKUP_DIR/db_$DATE.sql.gz

# MinIO (using mc client)
docker run --rm -v $BACKUP_DIR:/backup \
  minio/mc mirror minio/lifegraph /backup/files_$DATE

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -mtime +30 -delete
```

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Person creation time | < 2 min | UX testing |
| Search response time | < 500ms | API monitoring |
| AI summary generation | < 10s | API monitoring |
| LinkedIn sync success | > 95% | Task monitoring |
| Data retention | 20+ years | Architecture design |
| Uptime | 99.5% | Monitoring |

---

## Appendix

### A. Technology Alternatives Considered

| Choice | Alternative | Reason for Choice |
|--------|-------------|-------------------|
| Django | FastAPI | Django's admin, ORM, ecosystem for large project |
| PostgreSQL | SQLite | Need for concurrent access, full-text search |
| MinIO | Local FS | S3 API compatibility, easier backup |
| Celery | Django-Q | Mature, well-documented, Redis integration |

### B. Future Considerations

- **Mobile App:** React Native or PWA
- **Multi-User:** Shared family instance
- **Email Integration:** Parse emails for context
- **Voice Notes:** Record and transcribe memories
- **Facial Recognition:** Auto-tag in photos

### C. References

- [MonicaHQ](https://github.com/monicahq/monica) - Inspiration
- [Django Documentation](https://docs.djangoproject.com/)
- [OpenAI API](https://platform.openai.com/docs/)
