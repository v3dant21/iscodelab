import type { Metadata } from 'next';
import './style.css';
import Storefront from './storefront';
import { publicMenu } from './public-menu';
export const dynamic = 'force-dynamic';
export const metadata: Metadata = { metadataBase: new URL(process.env.SITE_URL || 'http://localhost:3000'), title: 'DumHouse · Hyderabad, served warm', description: 'A fictional Hyderabad kitchen. Order biryani, choose your outlet, and follow your order.' };
export default async function Layout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body><Storefront initialDishes={await publicMenu()} />{children}</body></html>;
}
