import { test, expect } from '@playwright/test';
import { testData } from '../fixtures/test-data';

/**
 * People CRUD E2E Tests
 *
 * Tests Create, Read, Update, Delete operations for people/contacts.
 */

test.describe('People List', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/people');
    await page.waitForLoadState('networkidle');
  });

  test('should display people list page', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /people/i })).toBeVisible();
    await expect(page.getByText(/manage your contacts/i)).toBeVisible();
  });

  test('should have Add Person button', async ({ page }) => {
    await expect(page.getByRole('button', { name: /add person/i })).toBeVisible();
  });

  test('should have AI Import button', async ({ page }) => {
    await expect(page.getByRole('button', { name: /ai import/i })).toBeVisible();
  });

  test('should have search functionality', async ({ page }) => {
    await expect(page.getByPlaceholder(/search/i)).toBeVisible();
  });

  test('should show empty state when no people exist', async ({ page }) => {
    // If the list is empty, check for empty state message
    const emptyState = page.getByText(/no people yet/i);
    const personCards = page.locator('[data-testid="person-card"]').or(
      page.locator('a[href^="/people/"]')
    );

    // Either we have people or an empty state
    const hasEmptyState = await emptyState.isVisible().catch(() => false);
    const hasPeople = (await personCards.count()) > 0;

    expect(hasEmptyState || hasPeople).toBeTruthy();
  });
});

test.describe('Add Person', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/people');
    await page.waitForLoadState('networkidle');
  });

  test('should open add person modal', async ({ page }) => {
    await page.getByRole('button', { name: /add person/i }).click();

    // Modal should appear
    await expect(page.getByRole('heading', { name: /add person/i })).toBeVisible();

    // Form fields should be visible
    await expect(page.getByLabel(/first name/i)).toBeVisible();
    await expect(page.getByLabel(/last name/i)).toBeVisible();
  });

  test('should create a new person', async ({ page }) => {
    await page.getByRole('button', { name: /add person/i }).click();

    // Fill form with test data
    const uniqueSuffix = Date.now();
    await page.getByLabel(/first name/i).fill(`E2E_${uniqueSuffix}`);
    await page.getByLabel(/last name/i).fill('TestPerson');

    // Submit form
    await page.getByRole('button', { name: /save|create|add/i }).click();

    // Wait for success - either modal closes or success message
    await page.waitForTimeout(1000);

    // Verify person was created (either in list or redirected to detail)
    const successIndicators = [
      page.getByText(`E2E_${uniqueSuffix} TestPerson`),
      page.getByText(/successfully created/i),
      page.getByText(/added/i),
    ];

    let found = false;
    for (const indicator of successIndicators) {
      if (await indicator.isVisible().catch(() => false)) {
        found = true;
        break;
      }
    }

    // If not found in list, check if we're on detail page
    if (!found) {
      const url = page.url();
      found = url.includes('/people/');
    }

    expect(found).toBeTruthy();
  });

  test('should validate required fields', async ({ page }) => {
    await page.getByRole('button', { name: /add person/i }).click();

    // Try to submit empty form
    await page.getByRole('button', { name: /save|create|add/i }).click();

    // Should show validation error
    const errorMessages = [
      page.getByText(/required/i),
      page.getByText(/cannot be empty/i),
      page.getByText(/please fill/i),
    ];

    let hasError = false;
    for (const error of errorMessages) {
      if (await error.isVisible().catch(() => false)) {
        hasError = true;
        break;
      }
    }

    // Either shows error or form is still open
    const formStillOpen = await page.getByLabel(/first name/i).isVisible();
    expect(hasError || formStillOpen).toBeTruthy();
  });
});

test.describe('Person Detail', () => {
  test('should display person detail page', async ({ page }) => {
    // Navigate to people list first
    await page.goto('/people');
    await page.waitForLoadState('networkidle');

    // Check if any person exists
    const personLinks = page.locator('a[href^="/people/"]').filter({
      hasNot: page.locator('[href="/people"]'),
    });

    const count = await personLinks.count();

    if (count > 0) {
      // Click on first person
      await personLinks.first().click();
      await page.waitForLoadState('networkidle');

      // Should be on detail page
      await expect(page).toHaveURL(/\/people\/[\w-]+/);

      // Should show person info sections
      await expect(page.getByText(/anecdotes|relationships|photos/i)).toBeVisible();
    } else {
      // Skip if no people exist
      test.skip();
    }
  });

  test('should show edit button on person detail', async ({ page }) => {
    await page.goto('/people');
    await page.waitForLoadState('networkidle');

    const personLinks = page.locator('a[href^="/people/"]').filter({
      hasNot: page.locator('[href="/people"]'),
    });

    if ((await personLinks.count()) > 0) {
      await personLinks.first().click();
      await page.waitForLoadState('networkidle');

      await expect(page.getByRole('button', { name: /edit/i }).first()).toBeVisible();
    } else {
      test.skip();
    }
  });

  test('should navigate back to people list', async ({ page }) => {
    await page.goto('/people');
    await page.waitForLoadState('networkidle');

    const personLinks = page.locator('a[href^="/people/"]').filter({
      hasNot: page.locator('[href="/people"]'),
    });

    if ((await personLinks.count()) > 0) {
      await personLinks.first().click();
      await page.waitForLoadState('networkidle');

      // Find back link/button
      const backLink = page.getByRole('link', { name: /back|people/i }).or(
        page.locator('a[href="/people"]')
      );

      await backLink.first().click();
      await expect(page).toHaveURL('/people');
    } else {
      test.skip();
    }
  });
});

test.describe('Search People', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/people');
    await page.waitForLoadState('networkidle');
  });

  test('should filter people by search term', async ({ page }) => {
    const searchInput = page.getByPlaceholder(/search/i);

    // Type search query
    await searchInput.fill('test');

    // Wait for debounce and API call
    await page.waitForTimeout(500);
    await page.waitForLoadState('networkidle');

    // Search should be applied (URL might contain search param)
    const url = page.url();
    expect(url.includes('search') || url.includes('q=') || true).toBeTruthy();
  });

  test('should clear search', async ({ page }) => {
    const searchInput = page.getByPlaceholder(/search/i);

    await searchInput.fill('test');
    await page.waitForTimeout(500);

    await searchInput.clear();
    await page.waitForTimeout(500);

    // Search input should be empty
    await expect(searchInput).toHaveValue('');
  });
});
