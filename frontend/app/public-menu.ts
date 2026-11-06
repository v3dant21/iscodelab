import 'server-only';
import { Dish } from './api';
export async function publicMenu(): Promise<Dish[]> {
  try {
    const response = await fetch(`${process.env.API_INTERNAL_URL || 'http://127.0.0.1:8000'}/catalog`, { cache: 'no-store', signal: AbortSignal.timeout(5000) });
    return response.ok ? await response.json() : [];
  } catch { return []; }
}
