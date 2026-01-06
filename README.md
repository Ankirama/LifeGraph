# LifeGraph

A personal CRM for managing relationships, memories, and life connections. Built with Django, React, and AI-powered features.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![React](https://img.shields.io/badge/react-18-blue.svg)
![TypeScript](https://img.shields.io/badge/typescript-5.3-blue.svg)

## Overview

LifeGraph helps you maintain meaningful connections by organizing information about the people in your life. Track relationships, record memories, and visualize your social network with an interactive graph.

## Features

### People Management
- Create and manage contact profiles with rich metadata
- AI-powered import from text descriptions (LinkedIn profiles, bios, etc.)
- AI-powered profile updates and enrichment
- Custom fields for flexible data storage
- Birthday tracking with dashboard reminders

### Relationships
- Track relationships between people with customizable types
- Interactive graph visualization powered by D3.js
- AI-suggested relationship connections
- Bidirectional relationship support

### Photos & Media
- Photo gallery with person tagging
- S3-compatible object storage (MinIO)
- Photo metadata and descriptions

### Anecdotes & Memories
- Record memories, notes, and stories
- Associate anecdotes with multiple people
- Filter by type (memory, note, story)

### Smart Search
- Natural language search powered by AI
- Search across people, relationships, and anecdotes
- Intelligent result categorization

### Organization
- Tags for flexible categorization
- Hierarchical groups with parent/child support
- Employment history tracking

### Data Management
- Export data in JSON or CSV format
- Full audit logging with django-auditlog
- Field-level encryption for sensitive data

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Backend** | Django 5.0, Django REST Framework, Celery |
| **Frontend** | React 18, TypeScript, TailwindCSS, React Query |
| **Database** | PostgreSQL with field-level encryption |
| **Storage** | MinIO (S3-compatible), Redis |
| **AI** | OpenAI GPT-4 integration |
| **Infrastructure** | Docker, Docker Compose, Nginx |

## Quick Start

### Prerequisites

- Docker and Docker Compose
- OpenAI API key (for AI features)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Ankirama/LifeGraph.git
   cd LifeGraph
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Generate encryption key**
   ```bash
   docker-compose run --rm backend python manage.py generate_encryption_key
   # Add the generated key to your .env file
   ```

4. **Start the services**
   ```bash
   docker-compose up -d
   ```

5. **Run database migrations**
   ```bash
   docker-compose exec backend python manage.py migrate
   ```

6. **Seed relationship types**
   ```bash
   docker-compose exec backend python manage.py seed_relationship_types
   ```

7. **Create a superuser**
   ```bash
   docker-compose exec backend python manage.py createsuperuser
   ```

8. **Access the application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000/api/
   - Admin: http://localhost:8000/admin/

## Development

### Backend Development

```bash
# Install dependencies
cd backend
pip install -r requirements-dev.txt

# Run tests
pytest

# Run with coverage
pytest --cov=apps --cov-report=html
```

### Frontend Development

```bash
# Install dependencies
cd frontend
npm install

# Start development server
npm run dev

# Run tests
npm test

# Run tests with coverage
npm run test:coverage
```

### E2E Testing

```bash
# Run E2E tests with Docker
docker-compose --profile testing run --rm e2e npm test

# Run specific test file
docker-compose --profile testing run --rm e2e npm test -- auth.spec.ts
```

## Project Structure

```
lifegraph/
├── backend/                 # Django backend
│   ├── apps/
│   │   ├── core/           # Core app (users, encryption)
│   │   └── people/         # People, relationships, anecdotes
│   ├── lifegraph/          # Django settings
│   └── tests/              # Backend tests
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # Reusable components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API services
│   │   └── types/          # TypeScript types
│   └── tests/              # Frontend tests
├── e2e/                    # Playwright E2E tests
├── nginx/                  # Nginx configuration
├── scripts/                # Utility scripts
└── docker-compose.yml      # Docker orchestration
```

## API Documentation

The API is built with Django REST Framework and includes:

- `/api/persons/` - People CRUD operations
- `/api/relationships/` - Relationship management
- `/api/anecdotes/` - Anecdotes and memories
- `/api/photos/` - Photo management
- `/api/tags/` - Tag management
- `/api/groups/` - Group management
- `/api/search/` - Full-text search
- `/api/smart-search/` - AI-powered search
- `/api/export/` - Data export
- `/api/ai/` - AI features (import, update, suggestions)

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key | (required) |
| `DEBUG` | Debug mode | `False` |
| `DATABASE_URL` | PostgreSQL connection URL | (required) |
| `REDIS_URL` | Redis connection URL | (required) |
| `OPENAI_API_KEY` | OpenAI API key for AI features | (optional) |
| `FIELD_ENCRYPTION_KEY` | Encryption key for sensitive fields | (required) |
| `MINIO_ROOT_USER` | MinIO access key | (required) |
| `MINIO_ROOT_PASSWORD` | MinIO secret key | (required) |

See `.env.example` for a complete list of configuration options.

## Testing

### Test Coverage

| Layer | Tests | Coverage |
|-------|-------|----------|
| Backend | 650+ | ~85% |
| Frontend | 514 | ~75% |
| E2E | 89 | Critical flows |

### Running Tests

```bash
# Backend tests
docker-compose exec backend pytest

# Frontend tests
docker-compose exec frontend npm test

# E2E tests
docker-compose --profile testing run --rm e2e npm test
```

## Deployment

For production deployment, see [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

The production setup includes:
- Nginx reverse proxy with SSL
- Gunicorn WSGI server
- Celery workers for background tasks
- PostgreSQL with connection pooling
- MinIO for object storage
- Redis for caching and task queue
- Automated backups

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Django](https://www.djangoproject.com/) - Backend framework
- [React](https://react.dev/) - Frontend library
- [TailwindCSS](https://tailwindcss.com/) - CSS framework
- [D3.js](https://d3js.org/) - Graph visualization
- [OpenAI](https://openai.com/) - AI capabilities
