'use client';
import Script from 'next/script';
import { useEffect, useRef, useState } from 'react';
import { api, User } from './api';

type GoogleIdentity = { accounts: { id: {
  initialize: (options: { client_id: string; nonce: string; callback: (response: { credential: string }) => void }) => void;
  renderButton: (element: HTMLElement, options: { theme: string; size: string; text: string }) => void;
} } };
export function GoogleSignIn({ onSignedIn }: { onSignedIn: (user: User) => void }) {
  const [config, setConfig] = useState<{ client_id: string; nonce: string } | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState('');
  const button = useRef<HTMLDivElement>(null);
  const callback = useRef(onSignedIn);
  callback.current = onSignedIn;
  useEffect(() => { api<{ client_id: string; nonce: string }>('/auth/google/config').then(setConfig).catch(() => setError('Google sign-in is unavailable. Please use email.')); }, []);
  useEffect(() => {
    const google = (window as Window & { google?: GoogleIdentity }).google;
    if (!loaded || !google || !config?.client_id || !button.current) return;
    google.accounts.id.initialize({ client_id: config.client_id, nonce: config.nonce, callback: async ({ credential }) => {
      setError('');
      try { callback.current(await api<User>('/auth/google', 'POST', { credential, nonce: config.nonce })); }
      catch (problem) { setError(problem instanceof Error ? problem.message : 'Google sign-in failed. Please try email.'); }
    } });
    google.accounts.id.renderButton(button.current, { theme: 'outline', size: 'large', text: 'continue_with' });
  }, [loaded, config]);
  if (config && !config.client_id) return null;
  return <div className="google-signin">{config?.client_id && <Script src="https://accounts.google.com/gsi/client" onReady={() => setLoaded(true)} onError={() => setError('Google could not load. Please use email sign-in.')} />}<div ref={button} />{error && <p role="alert">{error}</p>}</div>;
}
