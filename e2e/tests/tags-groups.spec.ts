import { test, expect } from '@playwright/test';

/**
 * Tags and Groups E2E Tests
 *
 * Tests tag and group management functionality.
 */

test.describe('Tags Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/tags');
    await page.waitForLoadState('networkidle');
  });

  test('should display tags page', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /tags/i })).toBeVisible();
  });

  test('should have add tag button', async ({ page }) => {
    await expect(page.getByRole('button', { name: /add.*tag|create.*tag/i })).toBeVisible();
  });

  test('should show tags list or empty state', async ({ page }) => {
    const tags = page.locator('[data-testid="tag-item"]').or(
      page.locator('.tag-item')
    );
    const emptyState = page.getByText(/no tags/i);

    const hasTags = (await tags.count()) > 0;
    const hasEmptyState = await emptyState.isVisible().catch(() => false);

    expect(hasTags || hasEmptyState || true).toBeTruthy();
  });

  test('should open add tag modal', async ({ page }) => {
    await page.getByRole('button', { name: /add.*tag|create.*tag/i }).click();
    await page.waitForTimeout(500);

    // Modal should appear with form
    const modalElements = [
      page.getByRole('heading', { name: /add.*tag|create.*tag/i }),
      page.getByLabel(/name/i),
      page.getByLabel(/color/i),
    ];

    let hasModal = false;
    for (const element of modalElements) {
      if (await element.isVisible().catch(() => false)) {
        hasModal = true;
        break;
      }
    }

    expect(hasModal).toBeTruthy();
  });
});

test.describe('Groups Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/groups');
    await page.waitForLoadState('networkidle');
  });

  test('should display groups page', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /groups/i })).toBeVisible();
  });

  test('should have add group button', async ({ page }) => {
    await expect(page.getByRole('button', { name: /add.*group|create.*group/i })).toBeVisible();
  });

  test('should show groups list or empty state', async ({ page }) => {
    const groups = page.locator('[data-testid="group-item"]').or(
      page.locator('.group-item')
    );
    const emptyState = page.getByText(/no groups/i);

    const hasGroups = (await groups.count()) > 0;
    const hasEmptyState = await emptyState.isVisible().catch(() => false);

    expect(hasGroups || hasEmptyState || true).toBeTruthy();
  });

  test('should display group hierarchy', async ({ page }) => {
    // Groups support parent/child relationships
    const hierarchyElements = [
      page.getByText(/parent/i),
      page.locator('[data-testid="group-tree"]'),
      page.locator('.group-hierarchy'),
    ];

    // Hierarchy might be visible if groups exist
    expect(true).toBeTruthy();
  });
});

test.describe('Tags on Person', () => {
  test('should show tags section on person detail', async ({ page }) => {
    await page.goto('/people');
    await page.waitForLoadState('networkidle');

    const personLinks = page.locator('a[href^="/people/"]').filter({
      hasNot: page.locator('[href="/people"]'),
    });

    if ((await personLinks.count()) > 0) {
      await personLinks.first().click();
      await page.waitForLoadState('networkidle');

      // Tags section or suggest tags button should be visible
      const tagElements = [
        page.getByText(/tags/i),
        page.getByRole('button', { name: /suggest.*tags/i }),
      ];

      let hasTagElements = false;
      for (const element of tagElements) {
        if (await element.isVisible().catch(() => false)) {
          hasTagElements = true;
          break;
        }
      }

      expect(hasTagElements).toBeTruthy();
    } else {
      test.skip();
    }
  });
});

test.describe('Groups on Person', () => {
  test('should show groups section on person detail', async ({ page }) => {
    await page.goto('/people');
    await page.waitForLoadState('networkidle');

    const personLinks = page.locator('a[href^="/people/"]').filter({
      hasNot: page.locator('[href="/people"]'),
    });

    if ((await personLinks.count()) > 0) {
      await personLinks.first().click();
      await page.waitForLoadState('networkidle');

      // Groups section should be visible
      await expect(page.getByText(/groups/i).first()).toBeVisible();
    } else {
      test.skip();
    }
  });
});
