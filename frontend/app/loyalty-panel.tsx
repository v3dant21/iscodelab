'use client';
import { useEffect, useState } from 'react';
import { api } from './api';
export type Rewards={balance:number;entries:{order_id:number;kind:string;points:number;created:number}[]};
export function LoyaltyPanel(){
 const [rewards,setRewards]=useState<Rewards|null>(null);const [error,setError]=useState('');
 useEffect(()=>{api<Rewards>('/account/loyalty').then(setRewards).catch(e=>setError(e.message));},[]);
 return <section className="loyalty-panel"><h2>Your rewards</h2>{error?<p role="alert">{error}</p>:<p><strong>{rewards?.balance ?? '…'} points</strong> · 1 point = ₹1 at checkout</p>}<p>Earn 1 point for every ₹100 paid on direct orders, after rider handoff. Redeemed points do not earn more points. Cancelled orders earn none.</p>{!!rewards?.entries.length&&<details><summary>Points history</summary><ul>{rewards.entries.map((e,i)=><li key={i}>Order #{e.order_id} · {e.kind==='earn'?'Earned':e.kind==='refund'?'Returned':'Redeemed'} · {e.points>0?'+':''}{e.points} points</li>)}</ul></details>}</section>;
}
