import Image from 'next/image';
import photos from './food-photos.json';
import { Icon } from './ui-icon';
export function foodPhoto(name: string) {
  return (photos as Record<string, { src: string; title: string; source: string; author: string; license: string; licenseUrl: string }>)[name.toLowerCase()];
}
export function foodImage(name: string) { return foodPhoto(name)?.src; }
export function FoodImage({ name, className = '' }: { name: string; className?: string }) {
  const source = foodImage(name);
  return source ? <Image className={className} src={source} alt={`${name} — representative food photograph`} width={1000} height={750} sizes="(max-width: 760px) 100vw, 640px" loading="lazy" /> : <span className={`food-placeholder ${className}`} role="img" aria-label={`${name} — photo not available`}><Icon name="food" size={38} /><span>{name}</span></span>;
}
