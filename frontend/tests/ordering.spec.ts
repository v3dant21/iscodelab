import { test, expect, Page } from '@playwright/test';

async function login(page: Page, email: string) {
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await page.getByLabel('Email', { exact: true }).fill(email);
  await page.getByLabel('Password', { exact: true }).fill('DemoPass123!');
  await page.getByRole('button', { name: 'Sign in', exact: true }).last().click();
}

test('persisted cart, test payment, kitchen stages and customer tracking', async ({ page, browser }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Dum chicken biryani', exact: true })).toBeVisible();
  await page.locator('.dish').filter({ has: page.getByRole('heading', { name: 'Dum chicken biryani', exact: true }) }).locator('summary').click();
  await page.getByLabel('Portion for Dum chicken biryani').selectOption('large');
  await page.getByRole('button', { name: 'Add Dum chicken biryani', exact: true }).click();
  await page.reload();
  await expect(page.getByRole('button', { name: 'Your bag · 1' })).toBeVisible();
  await login(page, 'customer@demo.test');
  await page.getByLabel('Delivery address').fill('Browser test flat, Kondapur');
  await page.getByRole('button', { name: 'Continue to payment' }).click();
  const orderCard = page.locator('.order').first();
  await expect(orderCard.getByText('PENDING PAYMENT', { exact: true })).toBeVisible();
  const title = await orderCard.getByRole('heading').innerText();
  const id = title.replace('Order #', '');
  await orderCard.getByRole('button', { name: 'Simulate failure' }).click();
  await expect(page.locator('.error[role="alert"]')).toContainText('Test payment failed');
  await orderCard.getByRole('button', { name: 'Simulate successful payment' }).click();
  await expect(orderCard.getByText('Payment: PAID', { exact: true })).toBeVisible();
  const kitchenContext = await browser.newContext();
  const kitchen = await kitchenContext.newPage();
  await kitchen.goto('http://localhost:3000');
  await login(kitchen, 'kondapur@demo.test');
  const kitchenCard = kitchen.locator('.order').filter({ has: kitchen.getByRole('heading', { name: `#${id}`, exact: true }) });
  await expect(kitchenCard).toBeVisible();
  await kitchenCard.getByRole('button', { name: 'Start preparing' }).click();
  await expect(orderCard.locator('strong').filter({ hasText: /^PREPARING$/ })).toBeVisible({ timeout: 10000 });
  await kitchenCard.getByRole('button', { name: 'Mark ready' }).click();
  await expect(orderCard.locator('strong').filter({ hasText: /^READY$/ })).toBeVisible({ timeout: 10000 });
  await kitchenCard.getByRole('button', { name: 'Mark handed off' }).click();
  await expect(orderCard.locator('strong').filter({ hasText: /^HANDED OFF$/ })).toBeVisible({ timeout: 10000 });
  await kitchenContext.close();
});

test('menu works without horizontal overflow on mobile and desktop', async ({ page }) => {
  for (const width of [390, 942, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto('/');
    await expect(page.getByRole('heading', { name: 'Dum chicken biryani', exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Use my location' })).toBeVisible();
    await page.evaluate(() => document.fonts.ready);
    await expect(page.locator('.hero-image img')).toHaveJSProperty('complete', true);
    expect(await page.locator('.hero-image img').evaluate(image => (image as HTMLImageElement).naturalWidth)).toBeGreaterThan(0);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy();
    await page.screenshot({ path: `test-results/menu-${width}.png`, fullPage: true });
  }
});

test('menu search, vegetarian filter, categories, customization and mobile bag', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/');
  await expect(page.locator('.dish')).toHaveCount(6);
  await page.getByRole('button', { name: 'Vegetarian', exact: true }).click();
  await expect(page.locator('.dish')).toHaveCount(3);
  await page.locator('.filters').getByRole('button', { name: /^Biryani/ }).click();
  await expect(page.locator('.dish')).toHaveCount(1);
  await page.getByRole('searchbox', { name: 'Search the menu' }).fill('nothing-like-this');
  await expect(page.getByRole('heading', { name: 'Nothing on this page, yet.' })).toBeVisible();
  await page.getByRole('button', { name: 'Show full menu' }).click();
  await expect(page.locator('.dish')).toHaveCount(6);
  await page.getByRole('button', { name: 'Add Dum chicken biryani', exact: true }).click();
  await page.getByRole('button', { name: /1 item.*View bag/ }).click();
  await expect(page.locator('#cart')).toBeFocused();
  await expect(page.getByLabel('Delivery address')).toBeVisible();
  await page.screenshot({ path: 'test-results/bag-mobile.png', fullPage: true });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy();
});

test('saved dishes persist and mobile account navigation works', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/');
  await page.getByRole('button', { name: 'Save Chicken 65', exact: true }).click();
  await page.reload();
  await page.locator('.bottom-nav').getByRole('button', { name: 'Saved', exact: true }).click();
  await expect(page.locator('.dish')).toHaveCount(1);
  await expect(page.getByRole('heading', { name: 'Chicken 65', exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Unsave Chicken 65', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Make room for your favourites.' })).toBeVisible();
  await page.locator('.bottom-nav').getByRole('button', { name: 'Account', exact: true }).click();
  await expect(page.getByLabel('Email', { exact: true })).toBeVisible();
});
