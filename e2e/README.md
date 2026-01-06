# LifeGraph E2E Tests

End-to-end tests for LifeGraph Personal CRM using Playwright.

## Setup

### Prerequisites
- Node.js 18+
- Docker and docker-compose (for running the app)
- Playwright browsers

### Installation

```bash
cd e2e
npm install
npx playwright install chromium
```

## Running Tests

### Start the application first

```bash
# From project root
docker-compose up -d
```

### Run all tests

```bash
npm test
```

### Run specific test suites

```bash
# Authentication tests
npm run test:auth

# Navigation tests
npm run test:navigation

# People CRUD tests
npm run test:people

# Relationship tests
npm run test:relationships
```

### Interactive mode

```bash
npm run test:ui
```

### Headed mode (see browser)

```bash
npm run test:headed
```

### Debug mode

```bash
npm run test:debug
```

## Test Structure

```
e2e/
├── playwright.config.ts    # Playwright configuration
├── fixtures/
│   ├── auth.ts            # Authentication helpers
│   └── test-data.ts       # Test data and helpers
├── tests/
│   ├── global.setup.ts    # Authentication setup (runs once)
│   ├── auth.spec.ts       # Authentication tests
│   ├── navigation.spec.ts # Navigation tests
│   ├── people-crud.spec.ts # People CRUD tests
│   └── relationships.spec.ts # Relationship tests
└── .auth/                 # Stored authentication state (gitignored)
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `E2E_BASE_URL` | Base URL for tests | `http://localhost:5173` |
| `E2E_TEST_EMAIL` | Test user email | `test@example.com` |
| `E2E_TEST_PASSWORD` | Test user password | `testpass123` |

### Creating Test User

Before running tests for the first time, create a test user:

```bash
# Via Django admin
docker-compose exec backend python manage.py createsuperuser

# Or via shell
docker-compose exec backend python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email='test@example.com').exists():
    User.objects.create_user(
        username='test',
        email='test@example.com',
        password='testpass123'
    )
"
```

## Test Reports

After running tests, view the HTML report:

```bash
npm run test:report
```

Reports are saved in `playwright-report/`.

## Writing Tests

### Example test

```typescript
import { test, expect } from '@playwright/test';

test.describe('Feature Name', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/page');
    await page.waitForLoadState('networkidle');
  });

  test('should do something', async ({ page }) => {
    await expect(page.getByRole('heading')).toBeVisible();
  });
});
```

### Using fixtures

```typescript
import { test, expect } from '../fixtures/auth';
import { testData, createTestHelper } from '../fixtures/test-data';

test('should create person', async ({ authenticatedPage }) => {
  const helper = createTestHelper(authenticatedPage);
  await helper.ui.navigateTo('/people');
  // ...
});
```

## CI/CD Integration

Add to your CI pipeline:

```yaml
- name: Install Playwright
  run: |
    cd e2e
    npm ci
    npx playwright install --with-deps chromium

- name: Run E2E Tests
  run: |
    cd e2e
    npm test
  env:
    E2E_BASE_URL: http://localhost:5173
```

## Troubleshooting

### Tests timeout on CI
- Increase timeout in `playwright.config.ts`
- Ensure app is fully started before tests

### Authentication fails
- Check `E2E_TEST_EMAIL` and `E2E_TEST_PASSWORD` env vars
- Verify test user exists in database
- Check if app redirects to OAuth provider

### Browser not found
```bash
npx playwright install chromium
```
