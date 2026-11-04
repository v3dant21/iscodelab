import type { Metadata } from 'next';
import './style.css';
export const metadata: Metadata = { title: 'DumHouse · Hyderabad, served warm', description: 'A fictional Hyderabad kitchen. Order biryani, choose your outlet, and follow your order.' };
export default function Layout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
