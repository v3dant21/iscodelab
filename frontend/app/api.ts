export type User = { id: number; email: string; role: 'customer' | 'kitchen' | 'manager' | 'admin'; outlet_id: number | null; cod: boolean; marketing_opt_in: boolean; name:string; phone:string; profile_complete:boolean; email_verified:boolean; email_delivery_configured:boolean };
export type Outlet = { id: number; name: string; distance?: number; minimum?: number; fssai?:string | null };
export type CustomizationGroup = { id: string; label: string; default: string; note: string; choices: { id: string; label: string }[] };
export type Dish = { id: number; name: string; description: string; category: string; price: number; veg: boolean; allergens: string; options: Record<string, number>; customizations?: CustomizationGroup[]; raita_available?: boolean; weight: number; enabled: boolean; available: boolean; override: number | null };
export type CartLine = { dish_id: number; quantity: number; portion: string; addon: boolean; selections?: Record<string,string>; customization_labels?: string[]; name: string; price: number };
export type Order = { id: number; outlet_id: number; lines: { name: string; quantity: number; portion: string; addon: boolean; selections?: Record<string,string>; customization_labels?: string[]; price: number }[]; total: number; due: number; payment: string; status: string; version: number; accepted: number | null; minutes: number | null; prediction: string | null; late: boolean; address: string; contact?: {name?:string;phone?:string}; ai_minutes?:number; original_promise?:number; estimate_reason?:string };
export const money = (paise: number) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(paise / 100);
export async function api<T>(path: string, method = 'GET', body?: unknown): Promise<T> {
  const csrf = document.cookie.split('; ').find(cookie => cookie.startsWith('csrf='))?.slice(5) || '';
  const response = await fetch(`/api${path}`, { method, credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrf }, body: body === undefined ? undefined : JSON.stringify(body), cache: 'no-store' });
  const data = await response.json();
  if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Please check the form and try again.');
  return data as T;
}
