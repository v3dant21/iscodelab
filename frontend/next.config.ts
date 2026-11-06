import type { NextConfig } from 'next';
const apiOrigin = process.env.API_INTERNAL_URL?.replace(/\/$/, '');
if (process.env.VERCEL && (!apiOrigin || !apiOrigin.startsWith('https://'))) {
  throw new Error('Set API_INTERNAL_URL to the deployed HTTPS API before deploying to Vercel.');
}
const config: NextConfig = {
  async rewrites() {
    return [{ source: '/api/:path*', destination: `${apiOrigin || 'http://127.0.0.1:8000'}/:path*` }];
  },
};
export default config;
