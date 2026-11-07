import type { MetadataRoute } from 'next';
export default function robots(): MetadataRoute.Robots {
  const base = process.env.SITE_URL;
  return { rules: { userAgent: '*', allow: '/', disallow: ['/api/', '/bag', '/account', '/orders', '/saved', '/signin', '/verify-email', '/party'] }, ...(base ? { sitemap: `${base}/sitemap.xml` } : {}) };
}
