'use client';
import {FormEvent, useState} from 'react';
import {api, User} from './api';

export function ContactFields({user}:{user?:User}) {
  return <><label>Your name<input name="name" autoComplete="name" minLength={2} maxLength={100} defaultValue={user?.name || ''} required /></label><label>Contact phone<input name="phone" type="tel" autoComplete="tel" placeholder="+919876543210" pattern="\+[1-9][0-9]{7,14}" title="Country code followed by digits, without spaces. Example: +919876543210" defaultValue={user?.phone || ''} required /></label><small>Include the country code without spaces. Used to contact you about your order; this is not phone verification.</small></>;
}
export function CustomerProfile({user,onChange,required=false}:{user:User;onChange:(user:User)=>void;required?:boolean}) {
  const [busy,setBusy]=useState(false);
  const [message,setMessage]=useState('');
  const [error,setError]=useState('');
  async function save(event:FormEvent<HTMLFormElement>) {
    event.preventDefault();setBusy(true);setError('');setMessage('');
    const form=new FormData(event.currentTarget);
    try {onChange(await api<User>('/account/profile','PATCH',{name:form.get('name'),phone:form.get('phone')}));setMessage('Contact details saved.');}
    catch(e){setError(e instanceof Error?e.message:'Could not save your details.');}
    finally {setBusy(false);}
  }
  async function verify() {
    setBusy(true);setError('');
    try {const result=await api<{configured:boolean;verified:boolean}>('/auth/email/request-verification','POST');setMessage(result.verified?'Your email is verified.':result.configured?'Verification email queued. Check your inbox shortly.':'Email delivery is not connected yet. Your verification request is saved.');}
    catch(e){setError(e instanceof Error?e.message:'Could not request verification.');}
    finally{setBusy(false);}
  }
  return <section className="customer-profile"><h2>{required?'A few details before you order':'Your contact details'}</h2><p>We need your name and phone number so the kitchen can contact you about your order. Marketing remains optional.</p><form onSubmit={save}><ContactFields user={user}/><button disabled={busy}>{busy?'Saving…':required?'Save and continue':'Save contact details'}</button></form><p>{user.email} · {user.email_verified?'Email verified':'Email not yet verified'}</p>{!user.email_verified && <><p>Verify your email to receive tracking links and invoice PDFs. You can still track orders and download bills in the app.</p><button className="secondary" disabled={busy} onClick={verify}>Request verification email</button></>}{!user.email_delivery_configured && <p className="muted">Email delivery setup is pending. Order updates and bills remain available here.</p>}{message && <p role="status">{message}</p>}{error && <p role="alert" className="error">{error}</p>}</section>;
}
