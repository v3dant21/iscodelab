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
  for (const width of [390, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto('/');
    await expect(page.getByRole('heading', { name: 'Dum chicken biryani', exact: true })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy();
    await page.screenshot({ path: `test-results/menu-${width}.png`, fullPage: true });
  }
});
