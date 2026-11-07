import {test,expect} from '@playwright/test';
test('staff entrance opens assigned queue and history without shopping controls',async({page})=>{
 let signedIn=false;
 await page.route('**/api/**',async route=>{
  const path=new URL(route.request().url()).pathname;let body:unknown=[];let status=200;
  if(path==='/api/auth/me'){status=signedIn?200:401;body=signedIn?{id:2,email:'kitchen@example.test',role:'kitchen',outlet_id:1}:{detail:'Please sign in.'};}
  if(path==='/api/auth/staff/login'){signedIn=true;body={id:2,email:'kitchen@example.test',role:'kitchen',outlet_id:1};}
  if(path==='/api/auth/logout'){signedIn=false;body={ok:true};}
  if(path==='/api/staff/orders')body={orders:[{id:77,outlet_id:1,status:'HANDED_OFF',payment:'PAID',total:29900,lines:[{name:'Chicken biryani',quantity:1,portion:'regular',addon:false}],accepted:1700000000,minutes:25}],next_before:null};
  await route.fulfill({status,contentType:'application/json',body:JSON.stringify(body)});
 });
 await page.goto('/staff');await page.getByLabel('Staff email').fill('kitchen@example.test');await page.getByLabel('Password',{exact:true}).fill('TestPassword123!');await page.getByRole('button',{name:'Sign in to workspace'}).click();
 await expect(page.getByRole('button',{name:'queue',exact:true})).toBeVisible();await expect(page.getByRole('button',{name:/Your bag/})).toHaveCount(0);await expect(page.getByRole('button',{name:'catalog',exact:true})).toHaveCount(0);
 await page.getByRole('button',{name:'history',exact:true}).click();await page.getByText('#77',{exact:true}).click();await expect(page.getByText('1 × Chicken biryani',{exact:true})).toBeVisible();
 for(const width of [390,1440]){await page.setViewportSize({width,height:900});await expect(page.getByRole('button',{name:'Sign out',exact:true})).toBeVisible();expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();await page.screenshot({path:`/tmp/staff-history-${width}.png`,fullPage:true});}
 await page.getByRole('button',{name:'Sign out',exact:true}).click();await expect(page.getByRole('heading',{name:'Kitchen & staff sign-in'})).toBeVisible();
});
test('customer session cannot enter staff workspace',async({page})=>{
 await page.route('**/api/**',r=>r.fulfill({contentType:'application/json',body:JSON.stringify(new URL(r.request().url()).pathname==='/api/auth/me'?{id:1,role:'customer',email:'customer@example.test'}:[])}));
 await page.goto('/staff');await expect(page.getByRole('heading',{name:'Staff access only'})).toBeVisible();await expect(page.getByRole('button',{name:'queue',exact:true})).toHaveCount(0);
});
