import { test as base, expect, Page } from '@playwright/test';
import path from 'path';

// Authentication storage file
export const STORAGE_STATE = path.join(__dirname, '../.auth/user.json');

/**
 * Custom test fixture with authenticated state
 */
export const test = base.extend<{
  authenticatedPage: Page;
}>({
  // Authenticated page fixture
  authenticatedPage: async ({ browser }, use) => {
    const context = await browser.newContext({
      storageState: STORAGE_STATE,
    });
    const page = await context.newPage();
    await use(page);
    await context.close();
  },
});

export { expect };

/**
 * Helper to bypass authentication in development
 * Use for quick testing when auth is disabled
 */
export async function loginAsDev(page: Page) {
  // Navigate directly - assumes dev mode with auth disabled
  await page.goto('/');
  await page.waitForLoadState('networkidle');
}

/**
 * Helper to login via allauth form
 */
export async function loginViaForm(
  page: Page,
  email: string = 'test@example.com',
  password: string = 'testpass123'
) {
  await page.goto('/accounts/login/');
  await page.getByLabel(/email/i).fill(email);
  await page.getByLabel(/password/i).fill(password);
  await page.getByRole('button', { name: /sign in|log in/i }).click();
  await page.waitForURL('/');
}

/**
 * Helper to logout
 */
export async function logout(page: Page) {
  await page.goto('/accounts/logout/');
  await page.getByRole('button', { name: /sign out|log out/i }).click();
}

/**
 * Ensure user is authenticated before proceeding
 */
export async function ensureAuthenticated(page: Page) {
  // Check if redirected to login
  if (page.url().includes('/accounts/login')) {
    await loginViaForm(page);
  }
}
