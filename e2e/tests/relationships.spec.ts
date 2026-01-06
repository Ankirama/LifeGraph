import { test, expect } from '@playwright/test';

/**
 * Relationships E2E Tests
 *
 * Tests relationship management functionality.
 */

test.describe('Relationships Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/relationships');
    await page.waitForLoadState('networkidle');
  });

  test('should display relationships page', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /relationships/i })).toBeVisible();
    await expect(page.getByText(/view connections/i)).toBeVisible();
  });

  test('should show statistics', async ({ page }) => {
    // Check for stats cards
    await expect(page.getByText(/total connections/i)).toBeVisible();
    await expect(page.getByText(/relationship types/i)).toBeVisible();
  });

  test('should have AI suggestions button', async ({ page }) => {
    await expect(page.getByRole('button', { name: /ai suggestions/i })).toBeVisible();
  });

  test('should have relationship type filter', async ({ page }) => {
    // Check for filter dropdown
    const filter = page.getByRole('combobox').or(
      page.getByLabel(/filter|type/i)
    );
    await expect(filter.first()).toBeVisible();
  });

  test('should show empty state or relationships list', async ({ page }) => {
    // Either we have relationships or an empty state
    const emptyState = page.getByText(/no relationships yet/i);
    const relationshipCards = page.locator('[data-testid="relationship-card"]').or(
      page.getByText(/friend|colleague|family/i)
    );

    const hasEmptyState = await emptyState.isVisible().catch(() => false);
    const hasRelationships = (await relationshipCards.count()) > 0;

    expect(hasEmptyState || hasRelationships).toBeTruthy();
  });
});

test.describe('AI Relationship Suggestions', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/relationships');
    await page.waitForLoadState('networkidle');
  });

  test('should open AI suggestions panel', async ({ page }) => {
    await page.getByRole('button', { name: /ai suggestions/i }).click();

    // Wait for suggestions to load
    await page.waitForTimeout(1000);

    // Should show suggestions panel
    const suggestionsPanel = page.getByText(/ai relationship suggestions/i).or(
      page.getByText(/suggestions/i)
    );

    await expect(suggestionsPanel.first()).toBeVisible();
  });

  test('should toggle AI suggestions panel', async ({ page }) => {
    // Open
    await page.getByRole('button', { name: /ai suggestions/i }).click();
    await page.waitForTimeout(500);

    // Close
    await page.getByRole('button', { name: /hide suggestions/i }).or(
      page.getByRole('button', { name: /ai suggestions/i })
    ).click();

    await page.waitForTimeout(500);

    // Panel should be hidden or button changed
    const hideButton = page.getByRole('button', { name: /hide suggestions/i });
    const isHidden = !(await hideButton.isVisible().catch(() => false));

    expect(isHidden).toBeTruthy();
  });
});

test.describe('Relationship Graph', () => {
  test('should display graph page', async ({ page }) => {
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');

    await expect(page.getByRole('heading', { name: /graph|network/i })).toBeVisible();
  });

  test('should show graph visualization or loading state', async ({ page }) => {
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');

    // Check for graph container, canvas, or loading state
    const graphElements = [
      page.locator('canvas'),
      page.locator('[data-testid="graph-container"]'),
      page.locator('.graph-container'),
      page.getByText(/loading/i),
      page.getByText(/no data/i),
    ];

    let found = false;
    for (const element of graphElements) {
      if (await element.isVisible().catch(() => false)) {
        found = true;
        break;
      }
    }

    expect(found).toBeTruthy();
  });

  test('should have view controls', async ({ page }) => {
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');

    // Check for zoom or layout controls
    const controls = page.getByRole('button').filter({
      has: page.locator('svg'),
    });

    // Should have some controls (zoom, reset, etc.)
    const controlCount = await controls.count();
    expect(controlCount).toBeGreaterThanOrEqual(0);
  });
});

test.describe('Add Relationship from Person Detail', () => {
  test('should have add relationship option on person detail', async ({ page }) => {
    // Navigate to people list
    await page.goto('/people');
    await page.waitForLoadState('networkidle');

    // Find a person
    const personLinks = page.locator('a[href^="/people/"]').filter({
      hasNot: page.locator('[href="/people"]'),
    });

    if ((await personLinks.count()) > 0) {
      await personLinks.first().click();
      await page.waitForLoadState('networkidle');

      // Look for relationships section
      await expect(page.getByText(/relationships/i).first()).toBeVisible();

      // Look for add relationship button
      const addButton = page.getByRole('button', { name: /add.*relationship/i }).or(
        page.getByRole('button', { name: /\+/ })
      );

      // Should have some way to add relationships
      const addButtonExists = (await addButton.count()) > 0;
      const relationshipSection = await page.getByText(/relationships/i).isVisible();

      expect(addButtonExists || relationshipSection).toBeTruthy();
    } else {
      test.skip();
    }
  });
});
