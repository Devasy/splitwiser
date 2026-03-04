import { test, expect } from '@playwright/test';
import path from 'path';

test('Profile Image Cropper Test', async ({ page }) => {
  // Go to the app
  await page.goto('http://localhost:5173');

  // Set auth state locally
  await page.evaluate(() => {
    localStorage.setItem('access_token', 'fake-token');
    localStorage.setItem('user', JSON.stringify({
      id: "1",
      _id: "1",
      name: "Test User",
      email: "test@example.com",
    }));
  });

  // Intercept the profile request to fake successful login
  await page.route('**/users/me', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: "1",
        _id: "1",
        name: "Test User",
        email: "test@example.com",
      })
    });
  });

  // Reload to apply token
  await page.reload();

  // Wait for the app to load
  await page.waitForTimeout(1000);

  // Go to profile page directly
  await page.goto('http://localhost:5173/#/profile');

  await page.waitForTimeout(1000);

  // Click on "Change Avatar" button
  const fileChooserPromise = page.waitForEvent('filechooser');
  await page.getByText('Change Avatar').click();
  const fileChooser = await fileChooserPromise;

  // Upload a file
  await fileChooser.setFiles(path.join(__dirname, 'public/vite.svg'));

  await page.waitForTimeout(1000);

  // Verify the cropper modal appears
  await expect(page.getByText('Crop Image')).toBeVisible();
  await expect(page.getByText('Cancel', { exact: true })).toBeVisible();
  await expect(page.getByText('Apply', { exact: true })).toBeVisible();

  // Take a screenshot
  await page.screenshot({ path: 'cropper-modal-screenshot.png' });

  // Click apply
  await page.getByText('Apply', { exact: true }).click();

  // Modal should disappear
  await page.waitForTimeout(500);
  await expect(page.getByText('Crop Image')).not.toBeVisible();
});
