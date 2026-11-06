'use client';
import { useEffect, useState } from 'react';
import { api, User } from './api';
export function PrivacySettings({user,onChange}:{user:User;onChange:(u:User)=>void}) {
 const [checked,setChecked]=useState(user.marketing_opt_in || false);
 const [busy,setBusy]=useState(false);
 const [error,setError]=useState('');
 useEffect(()=>setChecked(user.marketing_opt_in || false),[user.marketing_opt_in]);
 async function save(granted:boolean) {
   setChecked(granted);setBusy(true);setError('');
   try { onChange(await api<User>('/account/marketing-consent','PATCH',{granted})); }
   catch(problem) {setChecked(user.marketing_opt_in || false);setError(problem instanceof Error ? problem.message : 'Could not save your choice.');}
   finally {setBusy(false);}
 }
 return <section><h2>Privacy & messages</h2><p>We use your account, delivery details and order history to fulfil orders, show bills and suggest reorders. Order updates and marketing are separate choices.</p><label className="check"><input type="checkbox" checked={checked} disabled={busy} onChange={event=>save(event.target.checked)}/>I want optional offers and marketing messages. I can withdraw this choice here at any time.</label>{busy && <p role="status">Saving your choice…</p>}{error && <p role="alert" className="error">{error}</p>}<p><a href="/privacy.html">Read the privacy notice</a></p></section>;
}
