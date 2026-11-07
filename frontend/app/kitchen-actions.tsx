'use client';
import { useState } from 'react';
import { api, money, Order } from './api';
export function KitchenActions({order,disabled,change}:{order:Order;disabled:boolean;change:(work:()=>Promise<unknown>)=>void}){
 const [rider,setRider]=useState('');const [cash,setCash]=useState(false);
 const remaining=(order.payable_total??order.total)-(order.payment==='DEPOSIT_PAID'?order.due:0);
 return <div className="kitchen-actions">{order.status==='READY'&&<><label>Rider / pickup reference · optional<input value={rider} onChange={e=>setRider(e.target.value)} maxLength={80} autoComplete="off"/></label>{['COD_DUE','DEPOSIT_PAID'].includes(order.payment)&&<label className="check"><input type="checkbox" checked={cash} onChange={e=>setCash(e.target.checked)}/>Collected {money(remaining)} outstanding cash</label>}</>}<button disabled={disabled||(order.status==='READY'&&['COD_DUE','DEPOSIT_PAID'].includes(order.payment)&&!cash)} onClick={()=>change(()=>api(`/kitchen/orders/${order.id}/status`,'PATCH',{status:order.status==='NEW'?'PREPARING':order.status==='PREPARING'?'READY':'HANDED_OFF',version:order.version,rider_reference:rider,cash_collected:cash}))}>{order.status==='NEW'?'Start preparing':order.status==='PREPARING'?'Ready for pickup':'Confirm rider handoff'}</button></div>;
}
export function CancelOrder({order,disabled,change}:{order:Order;disabled:boolean;change:(work:()=>Promise<unknown>)=>void}){
 return <details className="cancel-order"><summary>Cancel order</summary><form onSubmit={e=>{e.preventDefault();const f=new FormData(e.currentTarget);change(()=>api(`/manager/orders/${order.id}/cancel`,'POST',{reason:f.get('reason'),version:order.version}));}}><label>Reason shown to customer<textarea name="reason" minLength={5} maxLength={500} required/></label><label className="check"><input type="checkbox" required/>Cancel this order and return its reserved loyalty points</label><button disabled={disabled}>Confirm cancellation</button></form></details>;
}
