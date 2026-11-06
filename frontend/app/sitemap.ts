import type { MetadataRoute } from 'next';
import { dishPath } from './menu-links';
import { publicMenu } from './public-menu';
export const dynamic = 'force-dynamic';
export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const base = process.env.SITE_URL || 'http://localhost:3000';
  return [{ url: base }, { url: `${base}/menu` }, ...(await publicMenu()).map(dish => ({ url: `${base}${dishPath(dish)}` }))];
}
