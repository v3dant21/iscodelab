import { test, expect, Page } from '@playwright/test';

async function signIn(page:Page,email:string){
 await page.goto('/signin');await page.getByLabel('Email',{exact:true}).fill(email);await page.getByLabel('Password',{exact:true}).fill('DemoPass123!');await page.getByRole('button',{name:'Sign in',exact:true}).click();await page.waitForURL(email==='customer@demo.test'?'**/menu':'**/staff');
}

test('party request stays pending until the catering desk confirms it',async({page,browser,baseURL})=>{
 await signIn(page,'customer@demo.test');await page.goto('/party');
 await page.getByLabel('Preparing outlet').selectOption('1');
 await page.getByLabel('Event date and time · IST',{exact:true}).fill(new Date(Date.now()+72*3600000).toISOString().slice(0,16));
 await page.getByLabel('Venue and address',{exact:true}).fill('Browser test party venue, Kondapur');
 await page.getByLabel('Your menu and serving preferences',{exact:true}).fill('Vegetarian biryani and starters for twenty');
 const response=page.waitForResponse(r=>r.url().endsWith('/api/party/requests')&&r.request().method()==='POST');
 await page.getByRole('button',{name:'Request catering confirmation',exact:true}).click();
 const party=await (await response).json();expect(party.status).toBe('REQUESTED');
 const context=await browser.newContext({baseURL});const admin=await context.newPage();
 await signIn(admin,'admin@demo.test');await admin.getByRole('button',{name:'catering',exact:true}).click();
 const request=admin.locator('.catering-desk article').filter({has:admin.getByRole('heading',{name:`Party #${party.id} · 20 guests`,exact:true})});
 await request.getByLabel('Message to customer',{exact:true}).fill('Menu and catering arrangements confirmed with customer.');
 await request.getByRole('button',{name:'Send decision',exact:true}).click();await expect(request).toHaveCount(0);
 await page.reload();await expect(page.locator('.party-history article').filter({has:page.getByRole('heading',{name:`Party #${party.id} · 20 guests`,exact:true})})).toContainText('CONFIRMED');
 await context.close();
});

test('central menu editor exposes city pricing, serving windows, dietary marks and photos',async({page})=>{
 await signIn(page,'admin@demo.test');await page.getByRole('button',{name:'catalog',exact:true}).click();await page.getByRole('button',{name:'Edit Tomato Soup',exact:true}).click();
 const form=page.locator('.menu-editor');await expect(form.getByLabel('Photo URL',{exact:true})).toBeVisible();
 await form.getByLabel('Spice level').selectOption('mild');
 await form.getByRole('button',{name:'Add city price',exact:true}).click();
 await expect(form.getByLabel('City',{exact:true}).last()).toBeVisible();
 await form.getByRole('button',{name:'Add serving window',exact:true}).click();
 await expect(form.getByLabel('From',{exact:true}).last()).toBeVisible();
 await expect(form.getByLabel('Mon',{exact:true}).last()).toBeChecked();
 await page.setViewportSize({width:390,height:844});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
});
