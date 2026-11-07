'use client';
import {useEffect,useState} from 'react';
import {api} from './api';
export function EmailVerification() {
 const [token,setToken]=useState('');const [busy,setBusy]=useState(false);const [done,setDone]=useState(false);const [error,setError]=useState('');
 useEffect(()=>{setToken(new URLSearchParams(window.location.hash.slice(1)).get('token') || '');window.history.replaceState(null,'',window.location.pathname);},[]);
 async function verify(){setBusy(true);setError('');try{await api('/auth/email/verify','POST',{token});setDone(true);}catch(e){setError(e instanceof Error?e.message:'Could not verify email.');}finally{setBusy(false);}}
 return <section className="auth"><h1>{done?'Email verified':'Confirm your email'}</h1><p>{done?'Your confirmed orders can now receive tracking links and invoice PDFs when email delivery is connected.':'Confirm this email address for your Dum & Dastaan account.'}</p>{!done && <button disabled={busy || !token} onClick={verify}>{busy?'Verifying…':'Verify email address'}</button>}{!token && !done && <p>Open the full link from your verification email. You can request a fresh link from your account.</p>}{error && <p role="alert" className="error">{error}</p>}<a href="/account">Go to your account</a></section>;
}
