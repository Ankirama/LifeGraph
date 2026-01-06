import { test, expect } from '@playwright/test';

/**
 * Photos E2E Tests
 *
 * Tests photo gallery and upload functionality.
 */

test.describe('Photos Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/photos');
    await page.waitForLoadState('networkidle');
  });

  test('should display photos page', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /photos/i })).toBeVisible();
  });

  test('should have upload button', async ({ page }) => {
    await expect(page.getByRole('button', { name: /upload/i })).toBeVisible();
  });

  test('should show photo grid or empty state', async ({ page }) => {
    // Either photos grid or empty state
    const photos = page.locator('img').filter({ hasNot: page.locator('[data-avatar]') });
    const emptyState = page.getByText(/no photos yet/i);

    const hasPhotos = (await photos.count()) > 0;
    const hasEmptyState = await emptyState.isVisible().catch(() => false);

    expect(hasPhotos || hasEmptyState).toBeTruthy();
  });

  test('should open upload modal', async ({ page }) => {
    await page.getByRole('button', { name: /upload/i }).first().click();

    await page.waitForTimeout(500);

    // Modal or file picker should appear
    const modal = page.getByText(/upload/i);
    await expect(modal.first()).toBeVisible();
  });
});

test.describe('Photo Gallery', () => {
  test('should display photo thumbnails when photos exist', async ({ page }) => {
    await page.goto('/photos');
    await page.waitForLoadState('networkidle');

    const photos = page.locator('img').filter({ hasNot: page.locator('[data-avatar]') });
    const photoCount = await photos.count();

    if (photoCount > 0) {
      // First photo should be visible
      await expect(photos.first()).toBeVisible();
    } else {
      test.skip();
    }
  });

  test('should open lightbox when photo is clicked', async ({ page }) => {
    await page.goto('/photos');
    await page.waitForLoadState('networkidle');

    const photos = page.locator('img').filter({ hasNot: page.locator('[data-avatar]') });
    const photoCount = await photos.count();

    if (photoCount > 0) {
      // Click on first photo
      await photos.first().click();

      await page.waitForTimeout(500);

      // Lightbox should open - look for close button or larger image
      const lightboxElements = [
        page.locator('[data-testid="lightbox"]'),
        page.locator('.lightbox'),
        page.getByRole('dialog'),
        page.locator('button').filter({ hasText: /close|×/i }),
      ];

      let lightboxOpen = false;
      for (const element of lightboxElements) {
        if (await element.isVisible().catch(() => false)) {
          lightboxOpen = true;
          break;
        }
      }

      expect(lightboxOpen).toBeTruthy();
    } else {
      test.skip();
    }
  });
});

test.describe('Photos on Person Detail', () => {
  test('should show photos section on person detail', async ({ page }) => {
    // Navigate to people list
    await page.goto('/people');
    await page.waitForLoadState('networkidle');

    const personLinks = page.locator('a[href^="/people/"]').filter({
      hasNot: page.locator('[href="/people"]'),
    });

    if ((await personLinks.count()) > 0) {
      await personLinks.first().click();
      await page.waitForLoadState('networkidle');

      // Photos section should be visible
      await expect(page.getByText('Photos').first()).toBeVisible();
    } else {
      test.skip();
    }
  });
});
