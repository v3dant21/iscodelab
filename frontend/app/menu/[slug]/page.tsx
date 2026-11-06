import type { Metadata } from 'next';
import { notFound, permanentRedirect } from 'next/navigation';
import { publicMenu } from '../../public-menu';
import { dishPath, slugify } from '../../menu-links';
export const dynamic = 'force-dynamic';
export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  const { slug } = await params;
  const dish = (await publicMenu()).find(item => slugify(item.name) === slug || String(item.id) === slug);
  if (!dish) return { title: 'Dish unavailable · DumHouse', robots: { index: false } };
  return { title: `${dish.name} · DumHouse`, description: dish.description, alternates: { canonical: dishPath(dish) } };
}
export default async function Page({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const catalog = await publicMenu();
  const dish = catalog.find(item => slugify(item.name) === slug || String(item.id) === slug);
  if (!dish) notFound();
  if (slug !== slugify(dish.name)) permanentRedirect(dishPath(dish));
  return null;
}
