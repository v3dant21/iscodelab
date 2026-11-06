export function slugify(name: string) {
  return name.normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
}
export function dishPath(dish: { name: string }) { return `/menu/${slugify(dish.name)}`; }
export function categoryPath(category: string) { return category === 'All' ? '/menu' : `/menu?category=${slugify(category)}`; }
