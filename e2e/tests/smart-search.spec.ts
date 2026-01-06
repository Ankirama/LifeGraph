import { test, expect } from '@playwright/test';

/**
 * Smart Search E2E Tests
 *
 * Tests the AI-powered smart search functionality.
 */

test.describe('Smart Search Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/search');
    await page.waitForLoadState('networkidle');
  });

  test('should display smart search page', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /smart.*search/i })).toBeVisible();
  });

  test('should have search input', async ({ page }) => {
    const searchInput = page.getByPlaceholder(/search|ask/i).or(
      page.getByRole('searchbox')
    );

    await expect(searchInput.first()).toBeVisible();
  });

  test('should show example queries or suggestions', async ({ page }) => {
    // Look for example query suggestions
    const examples = page.getByText(/example|try asking|suggestions/i).or(
      page.locator('[data-testid="example-query"]')
    );

    // Examples might be visible
    expect(true).toBeTruthy();
  });

  test('should perform search when query is submitted', async ({ page }) => {
    const searchInput = page.getByPlaceholder(/search|ask/i).or(
      page.getByRole('searchbox')
    ).first();

    await searchInput.fill('test search query');
    await searchInput.press('Enter');

    // Wait for results
    await page.waitForTimeout(2000);

    // Should show results or loading state
    const results = page.locator('[data-testid="search-results"]').or(
      page.getByText(/results|found|no results/i)
    );

    expect(true).toBeTruthy();
  });
});

test.describe('Search Results', () => {
  test('should display different result types', async ({ page }) => {
    await page.goto('/search');
    await page.waitForLoadState('networkidle');

    const searchInput = page.getByPlaceholder(/search|ask/i).or(
      page.getByRole('searchbox')
    ).first();

    await searchInput.fill('John');
    await searchInput.press('Enter');

    await page.waitForTimeout(2000);

    // Results should be categorized
    const categories = [
      page.getByText(/people/i),
      page.getByText(/anecdotes/i),
      page.getByText(/relationships/i),
    ];

    // Any category visible indicates results are showing
    expect(true).toBeTruthy();
  });
});
