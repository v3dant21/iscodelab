import { test, expect, Page } from '@playwright/test';

async function login(page: Page, email: string) {
  await page.goto('/signin');
  await page.getByLabel('Email', { exact: true }).fill(email);
  await page.getByLabel('Password', { exact: true }).fill('DemoPass123!');
  await page.getByRole('button', { name: 'Sign in', exact: true }).last().click();
  await expect(page.getByRole('button', { name: 'Sign out', exact: true }).first()).toBeVisible();
  if (await page.getByRole('heading', {name:'A few details before you order'}).isVisible()) {
    await page.getByLabel('Your name').fill('Test Customer');
    await page.getByLabel('Contact phone').fill('+919000000000');
    await page.getByRole('button', {name:'Save and continue'}).click();
    await expect(page.getByRole('heading', {name:'A few details before you order'})).toHaveCount(0);
  }
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
  await expect(page.getByRole('heading', { name: 'Review your order' })).toBeVisible();
  await expect(page.getByText('CGST · 2.5%', { exact: true })).toBeVisible();
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({ path: '../.impeccable/review/checkout-review.png', fullPage: true });
  await page.getByRole('button', { name: 'Place order & continue to payment' }).click();
  const orderCard = page.locator('.order').first();
  await expect(orderCard.getByText('PENDING PAYMENT', { exact: true })).toBeVisible();
  const title = await orderCard.getByRole('heading').innerText();
  const id = title.replace('Order #', '');
  await orderCard.getByRole('button', { name: 'Simulate failure' }).click();
  await expect(page.locator('.error[role="alert"]')).toContainText('Test payment failed');
  await orderCard.getByRole('button', { name: 'Simulate successful payment' }).click();
  await expect(orderCard.getByText('Payment: PAID', { exact: true })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Order confirmed', exact: true })).toBeVisible();
  await expect(page).toHaveURL(new RegExp(`/orders/${id}\\?confirmed=1$`));
  await page.reload();
  await expect(page.getByRole('button', { name: 'View bill', exact: true })).toBeVisible();
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({ path: '../.impeccable/review/order-confirmation.png', fullPage: true });
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
    await expect(page.locator('.menu')).toHaveAttribute('aria-busy', 'false');
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
  await expect(page.locator('.dish')).toHaveCount(12);
  await page.getByRole('button', { name: 'Vegetarian', exact: true }).click();
  await expect(page.locator('.dish')).toHaveCount(12);
  await page.getByLabel('Browse categories').selectOption('Biryani');
  await expect(page.locator('.dish')).toHaveCount(4);
  await page.getByRole('searchbox', { name: 'Search the menu' }).fill('nothing-like-this');
  await expect(page.getByRole('heading', { name: 'Nothing on this page, yet.' })).toBeVisible();
  await page.getByRole('button', { name: 'Show full menu' }).click();
  await expect(page.locator('.dish')).toHaveCount(12);
  await page.getByRole('button', { name: 'Add Dum chicken biryani', exact: true }).click();
  await page.getByRole('button', { name: /1 item.*View bag/ }).click();
  await expect(page.locator('#cart')).toBeFocused();
  await expect(page.getByLabel('Delivery address')).toBeVisible();
  await page.screenshot({ path: 'test-results/bag-mobile.png', fullPage: true });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy();
});

test('clickable cards and bag customizations persist with updated totals', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/');
  const card = page.locator('.dish').filter({ has: page.getByRole('heading', { name: 'Dum chicken biryani', exact: true }) });
  await card.locator('.dish-photo img').click();
  await expect(page).toHaveURL(/\/menu\/dum-chicken-biryani$/);
  await page.getByLabel('Portion for Dum chicken biryani').selectOption('large');
  await page.getByRole('checkbox', { name: /Extra raita/ }).check();
  await page.getByRole('button', { name: 'Add to bag · ₹449' }).click();
  await page.getByRole('button', { name: 'Your bag · 1' }).click();
  const line = page.locator('.cart-line').first();
  await line.locator('summary').click();
  await line.getByLabel('Portion for Dum chicken biryani').selectOption('regular');
  await line.getByLabel('Extra raita for Dum chicken biryani').uncheck();
  await line.getByLabel('Quantity Dum chicken biryani').fill('2');
  await expect(page.locator('.total')).toContainText('₹598');
  await page.screenshot({ path: 'test-results/edit-bag-mobile.png', fullPage: true });
  await page.reload();
  await page.getByRole('button', { name: 'Your bag · 2' }).click();
  await expect(page.locator('.total')).toContainText('₹598');
  await page.getByRole('button', { name: 'Back to menu' }).click();
  await card.getByRole('link', { name: 'Dum chicken biryani', exact: true }).focus();
  await page.keyboard.press('Enter');
  await expect(page).toHaveURL(/\/menu\/dum-chicken-biryani$/);
});

test('saved dishes persist and mobile account navigation works', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/');
  await page.getByRole('button', { name: 'Save Chicken 65', exact: true }).click();
  await page.reload();
  await page.locator('.bottom-nav').getByRole('link', { name: 'Saved', exact: true }).click();
  await expect(page.locator('.dish')).toHaveCount(1);
  await expect(page.getByRole('heading', { name: 'Chicken 65', exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Unsave Chicken 65', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Make room for your favourites.' })).toBeVisible();
  await page.locator('.bottom-nav').getByRole('link', { name: 'Account', exact: true }).click();
  await expect(page.getByLabel('Email', { exact: true })).toBeVisible();
});


test('dish deep links, history, meal options and metadata', async ({ page, request }) => {
  await page.goto('/menu/6');
  await expect(page.getByRole('heading', { name: 'Double ka meetha', exact: true })).toBeVisible();
  await expect(page.getByRole('checkbox', { name: /Extra raita/ })).toHaveCount(0);
  await expect(page).toHaveTitle('Double ka meetha · Dum & Dastaan');
  await page.getByRole('button', { name: 'Add to bag · ₹129' }).click();
  await page.getByRole('button', { name: 'View your bag', exact: true }).click();
  await expect(page).toHaveURL(/\/bag$/);
  await page.goBack();
  await expect(page).toHaveURL(/\/menu\/double-ka-meetha$/);
  await page.reload();
  await expect(page.getByRole('button', { name: 'Your bag · 1' })).toBeVisible();
  const sitemap = await request.get('/sitemap.xml');
  expect(await sitemap.text()).toContain('/menu/double-ka-meetha');
  await page.goto('/account');
  await expect(page.locator('meta[name="robots"]')).toHaveAttribute('content', /noindex/);
});

test('capture warm menu and detail on desktop and mobile', async ({ page }) => {
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: 900 });
    for (const [route, name] of [['/menu', 'menu'], ['/menu/1', 'detail']]) {
      await page.goto(route);
      await expect(page.getByRole('heading', { name: 'Dum chicken biryani', exact: true })).toBeVisible();
      await expect(page.locator('.menu')).toHaveAttribute('aria-busy', 'false');
    await page.evaluate(() => document.fonts.ready);
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
      await page.screenshot({ path: `../.impeccable/review/${name}-${width}.png`, fullPage: true });
    }
  }
});


test('quantity limit rejects excess without overstating additions', async ({ page }) => {
  await page.goto('/menu/1');
  await page.getByLabel('Dish quantity').fill('19');
  await page.getByRole('button', { name: 'Add to bag · ₹5,681' }).click();
  await expect(page.getByRole('button', { name: 'Your bag · 19' })).toBeVisible();
  await page.getByLabel('Dish quantity').fill('5');
  await page.getByRole('button', { name: 'Add to bag · ₹1,495' }).click();
  await expect(page.locator('.error[role="alert"]')).toContainText('Your bag already has 19');
  await expect(page.getByRole('button', { name: 'Your bag · 19' })).toBeVisible();
  await expect(page.locator('.detail-feedback')).not.toContainText('5 ×');
});


test('expanded reference menu supports category URLs and named dish links', async ({ page, request }) => {
  await page.goto('/menu');
  await page.getByLabel('Browse categories').selectOption('Breads');
  await expect(page).toHaveURL(/category=breads/);
  await page.getByRole('link', { name: 'Garlic Naan', exact: true }).click();
  await expect(page).toHaveURL(/\/menu\/garlic-naan$/);
  await expect(page.getByRole('heading', { name: 'Garlic Naan', exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Add to bag · ₹79' }).click();
  await page.getByRole('button', { name: 'View your bag', exact: true }).click();
  await expect(page.locator('.cart-line')).toContainText('Garlic Naan');
  await page.goBack();
  await page.locator('.breadcrumbs').getByRole('link', { name: 'Breads', exact: true }).click();
  await expect(page).toHaveURL(/category=breads/);
  await page.reload();
  await expect(page.getByLabel('Browse categories')).toHaveValue('Breads');
  const old = await request.get('/menu/1', { maxRedirects: 0 });
  expect(old.status()).toBe(308);
  expect(old.headers()['location']).toBe('/menu/dum-chicken-biryani');
  const unknown = await request.get('/menu/this-dish-does-not-exist');
  expect(unknown.status()).toBe(404);
});


test('curated light menu has 70 dishes and an image for every item', async ({ page, request }) => {
  const catalog = await (await request.get('/api/catalog')).json();
  expect(catalog).toHaveLength(70);
  expect(catalog.filter((dish: {veg: boolean}) => dish.veg)).toHaveLength(35);
  await page.goto('/menu');
  await page.waitForLoadState('networkidle');
  await expect(page.locator('.dish')).toHaveCount(12);
  for (let i = 0; i < 5; i++) await page.getByRole('button', { name: 'Show more dishes' }).click();
  await expect(page.locator('.dish')).toHaveCount(70);
  await expect(page.locator('.dish-photo img')).toHaveCount(70);
  await expect(page.locator('.dish-photo .food-placeholder')).toHaveCount(0);
  const photoSources = await page.locator('.dish-photo img').evaluateAll(images => images.map(image => image.getAttribute('src') || ''));
  expect(photoSources.every(source => source.includes('dishes%2F'))).toBe(true);
  expect(new Set(photoSources).size).toBe(70);
  const credits = await request.get('/photo-credits.html');
  expect(credits.status()).toBe(200);
  expect(await credits.text()).toContain('Wikimedia Commons');
  expect(await page.evaluate(() => getComputedStyle(document.documentElement).colorScheme)).toBe('light');
  for (const img of await page.locator('.dish-photo img').all()) {
    await img.scrollIntoViewIfNeeded();
    await expect(img).toHaveJSProperty('complete', true);
    expect(await img.evaluate((image: HTMLImageElement) => image.naturalWidth)).toBeGreaterThan(0);
  }
});

test('customer can view, download and print a saved demo bill', async ({ page }) => {
  await login(page, 'customer@demo.test');
  await page.waitForURL('**/menu');
  await page.goto('/orders');
  const card = page.locator('.order').filter({ has: page.getByRole('button', { name: 'View / print demo bill', exact: true }) }).first();
  await expect(card).toBeVisible();
  const downloadEvent = page.waitForEvent('download');
  await card.getByRole('button', { name: 'Download bill', exact: true }).click();
  const download = await downloadEvent;
  expect(download.suggestedFilename()).toMatch(/^DEMO-\d+\.pdf$/);
  await card.getByRole('button', { name: 'View / print demo bill', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Demo tax invoice', exact: true })).toBeVisible();
  await expect(page.getByText('DEMO TAX INVOICE — NOT VALID FOR TAX PURPOSES', { exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Print / Save as PDF' })).toBeVisible();
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({ path: '../.impeccable/review/demo-bill.png', fullPage: true });
  await page.pdf({ path: '../.impeccable/review/demo-bill.pdf', format: 'A4', printBackground: true });
});


test('real drink and dessert photos render on desktop and mobile', async ({ page }) => {
  for (const width of [1280, 390]) {
    await page.setViewportSize({ width, height: 900 });
    for (const category of ['drinks', 'sweets']) {
      await page.goto(`/menu?category=${category}`);
      await page.waitForLoadState('networkidle');
      for (const img of await page.locator('.dish-photo img').all()) {
        await img.scrollIntoViewIfNeeded();
        await expect(img).toHaveJSProperty('complete', true);
        expect(await img.evaluate((image: HTMLImageElement) => image.naturalWidth)).toBeGreaterThan(0);
      }
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
      await page.evaluate(() => scrollTo(0,0));
      await page.screenshot({ path: `../.impeccable/review/real-${category}-${width}.png`, fullPage: true });
    }
  }
});

test('food disclosures, separate marketing consent and tablet kitchen controls', async ({page}) => {
  await page.goto('/menu');
  await expect(page.getByText('Prices include 5% GST', {exact:true})).toBeVisible();
  await expect(page.locator('.licence-note').first()).toContainText('FSSAI');
  await expect(page.locator('.food-symbol').first()).toBeVisible();
  await expect(page.locator('.dish-copy .allergen-note').first()).toBeVisible();
  await login(page,'customer@demo.test');
  await page.goto('/account');
  const consent = page.getByRole('checkbox', {name:/optional offers and marketing/});
  await expect(consent).toBeVisible();
  if (await consent.isChecked()) { await consent.uncheck(); await expect(consent).toBeEnabled(); }
  await expect(consent).not.toBeChecked();
  await Promise.all([page.waitForResponse(response=>response.url().endsWith('/account/marketing-consent') && response.request().method()==='PATCH'),consent.check()]);
  await page.reload();
  await expect(consent).toBeChecked();
  await Promise.all([page.waitForResponse(response=>response.url().endsWith('/account/marketing-consent') && response.request().method()==='PATCH'),consent.uncheck()]);
  await page.reload();
  await expect(consent).not.toBeChecked();
  await page.getByRole('button',{name:'Sign out',exact:true}).first().click();
  await login(page,'kondapur@demo.test');
  await page.setViewportSize({width:800,height:1000});
  await expect(page.locator('.staff-workspace')).toBeVisible();
  await expect(page.getByText(/Last refreshed:/)).toBeVisible();
  const height=await page.locator('.staff-workspace button').first().evaluate(el=>el.getBoundingClientRect().height);
  expect(height).toBeGreaterThanOrEqual(56);
  await page.screenshot({path:'../.impeccable/review/kitchen-tablet.png',fullPage:true});
});


test('signup collects contact details and shows truthful email status', async ({page}) => {
  await page.setViewportSize({width:390,height:844});
  await page.goto('/signin');
  await page.getByRole('button',{name:'New here? Create an account'}).click();
  await page.getByLabel('Your name').fill('Browser Customer');
  await page.getByLabel('Contact phone').fill('+919876543210');
  await page.getByLabel('Email',{exact:true}).fill(`browser-${Date.now()}@example.test`);
  await page.getByLabel('Password',{exact:true}).fill('BrowserPassword123!');
  await page.screenshot({path:'../.impeccable/review/signup-contact-mobile.png',fullPage:true});
  await page.getByRole('button',{name:'Create account',exact:true}).click();
  await page.waitForURL('**/menu');
  await page.goto('/account');
  await expect(page.getByLabel('Your name')).toHaveValue('Browser Customer');
  await expect(page.getByText('Email delivery setup is pending.',{exact:false})).toBeVisible();
  await page.getByLabel('Your name').fill('Updated Customer');
  await page.getByRole('button',{name:'Save contact details'}).click();
  await expect(page.getByRole('status')).toContainText('Contact details saved.');
  await page.reload();
  await expect(page.getByLabel('Your name')).toHaveValue('Updated Customer');
  await page.getByRole('button',{name:'Request verification email'}).click();
  await expect(page.getByRole('status')).toContainText('not connected');
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
  await page.screenshot({path:'../.impeccable/review/profile-contact-mobile.png',fullPage:true});
});
