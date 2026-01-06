import { test, expect } from '@playwright/test';

/**
 * Navigation E2E Tests
 *
 * Tests the main navigation flows across the application.
 * Note: These tests assume authentication is handled by setup or dev mode.
 */

test.describe('Navigation', () => {
  test.beforeEach(async ({ page }) => {
    // Start from the homepage
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('should display main navigation links', async ({ page }) => {
    // Check for main navigation elements
    await expect(page.getByRole('link', { name: /dashboard|home/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /people/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /relationships/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /anecdotes/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /photos/i })).toBeVisible();
  });

  test('should navigate to People page from dashboard', async ({ page }) => {
    // Click on People link
    await page.getByRole('link', { name: /people/i }).click();

    // Verify we're on the People page
    await expect(page).toHaveURL(/\/people/);
    await expect(page.getByRole('heading', { name: /people/i })).toBeVisible();
  });

  test('should navigate through all main pages', async ({ page }) => {
    // Navigate through each main section
    const routes = [
      { link: /people/i, url: '/people', heading: /people/i },
      { link: /relationships/i, url: '/relationships', heading: /relationships/i },
      { link: /anecdotes/i, url: '/anecdotes', heading: /anecdotes/i },
      { link: /photos/i, url: '/photos', heading: /photos/i },
      { link: /tags/i, url: '/tags', heading: /tags/i },
      { link: /groups/i, url: '/groups', heading: /groups/i },
    ];

    for (const route of routes) {
      await page.getByRole('link', { name: route.link }).click();
      await expect(page).toHaveURL(new RegExp(route.url));
      await expect(page.getByRole('heading', { name: route.heading })).toBeVisible();

      // Navigate back to dashboard
      await page.getByRole('link', { name: /dashboard|home/i }).first().click();
      await expect(page).toHaveURL('/');
    }
  });
});

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('should display dashboard statistics', async ({ page }) => {
    // Check for stats cards
    await expect(page.getByText(/people/i)).toBeVisible();
    await expect(page.getByText(/relationships/i)).toBeVisible();
    await expect(page.getByText(/anecdotes/i)).toBeVisible();
    await expect(page.getByText(/photos/i)).toBeVisible();
  });

  test('should display upcoming birthdays section', async ({ page }) => {
    await expect(page.getByText(/upcoming birthdays/i)).toBeVisible();
  });

  test('should display recent anecdotes section', async ({ page }) => {
    await expect(page.getByText(/recent anecdotes/i)).toBeVisible();
  });
});

test.describe('Search', () => {
  test('should have global search accessible', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Check for search input in header or navigation
    const searchInput = page.getByPlaceholder(/search/i).or(
      page.getByRole('searchbox')
    );

    // Search should be visible or accessible
    await expect(searchInput.first()).toBeVisible();
  });

  test('should navigate to smart search page', async ({ page }) => {
    await page.goto('/search');
    await page.waitForLoadState('networkidle');

    await expect(page.getByRole('heading', { name: /smart search/i })).toBeVisible();
  });
});
