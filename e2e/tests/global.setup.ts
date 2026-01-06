import { test as setup, expect } from '@playwright/test';
import path from 'path';

const authFile = path.join(__dirname, '../.auth/user.json');

/**
 * Global setup - authenticate once before all tests
 * This creates a test user and saves the session state
 */
setup('authenticate', async ({ page, request }) => {
  // First, create a test user via Django admin command or use existing
  // For dev environment, we'll login via allauth

  // Navigate to login page
  await page.goto('/accounts/login/');

  // Check if we need to create account first
  const pageContent = await page.content();

  if (pageContent.includes('Sign In') || pageContent.includes('Log In')) {
    // Fill login form - allauth typically uses email
    await page.getByLabel(/email/i).fill(process.env.E2E_TEST_EMAIL || 'test@example.com');
    await page.getByLabel(/password/i).fill(process.env.E2E_TEST_PASSWORD || 'testpass123');

    // Submit
    await page.getByRole('button', { name: /sign in|log in/i }).click();

    // Wait for redirect to dashboard
    await page.waitForURL('/', { timeout: 10000 });
  }

  // Verify we're authenticated - check for layout elements
  await expect(page.getByRole('link', { name: /dashboard|home/i }).or(
    page.getByText(/people|contacts/i)
  )).toBeVisible({ timeout: 5000 });

  // Save authentication state
  await page.context().storageState({ path: authFile });
});

/**
 * Alternative setup using API-based authentication
 * Use this if direct login doesn't work
 */
setup.skip('api-authenticate', async ({ request }) => {
  // Get CSRF token
  const csrfResponse = await request.get('/accounts/login/');
  const csrfCookies = await csrfResponse.headers()['set-cookie'];

  // Login via POST
  const loginResponse = await request.post('/accounts/login/', {
    form: {
      login: process.env.E2E_TEST_EMAIL || 'test@example.com',
      password: process.env.E2E_TEST_PASSWORD || 'testpass123',
    },
  });

  expect(loginResponse.ok()).toBeTruthy();
});
