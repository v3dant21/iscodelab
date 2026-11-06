'use client';
import Link from 'next/link';
import { useEffect, useState } from 'react';
import { api, money, Order } from './api';
import { FoodImage } from './food-image';
import { Icon } from './ui-icon';

export function OrderHistory({ orders, busy, pay, focusedId, confirmed = false }: { focusedId?:number; confirmed?:boolean; orders: Order[]; busy: boolean; pay: (order: Order, success: boolean) => void }) {
  const [notices,setNotices]=useState<{id:number;order_id:number;message:string;channel:string;state:string}[]>([]);
  useEffect(()=>{let active=true;const load=()=>api<typeof notices>('/notifications').then(items=>active && setNotices(items)).catch(()=>{});load();const timer=setInterval(load,15000);return()=>{active=false;clearInterval(timer);};},[]);
  const [billBusy, setBillBusy] = useState<number | null>(null);
  const [billError, setBillError] = useState('');
  async function openBill(order: Order, download = false) {
    setBillBusy(order.id); setBillError('');
    try { const result = await api<{url:string}>(`/orders/${order.id}/invoice`, 'POST'); window.location.assign(result.url + (download ? '?download=true' : '')); }
    catch (error) { setBillError(error instanceof Error ? error.message : 'Could not open bill.'); }
    finally { setBillBusy(null); }
  }
  const [history, setHistory] = useState(false);
  const visible = focusedId !== undefined ? orders.filter(order => order.id === focusedId) : history ? orders.filter(order => order.status === 'HANDED_OFF') : orders;
  const stages = ['NEW', 'PREPARING', 'READY', 'HANDED_OFF'];
  return <section className={`order-page ${focusedId !== undefined ? 'focused-order' : ''}`}><div className="page-title"><h1>{focusedId !== undefined ? visible[0]?.status === 'PENDING_PAYMENT' ? 'Complete payment' : 'Track your order' : 'Your orders'}</h1><p>{focusedId !== undefined ? 'Your meal, preparation updates and bill in one place.' : 'Track your meals and get bills for past orders.'}</p>{focusedId !== undefined && <Link href="/orders">← All orders</Link>}</div>
    {confirmed && visible[0] && visible[0].status !== 'PENDING_PAYMENT' && <section className="order-confirmation" role="status"><h2>Order confirmed</h2><p>Your kitchen has received order #{visible[0].id}. Your demo bill is ready.</p><div className="review-actions"><a href="#order-tracking">Track order</a><button className="secondary" disabled={billBusy !== null} onClick={() => openBill(visible[0])}>View bill</button></div></section>}
    {focusedId === undefined && <div className="order-tabs"><button className={!history ? 'selected' : 'quiet'} onClick={() => setHistory(false)}>All orders</button><button className={history ? 'selected' : 'quiet'} onClick={() => setHistory(true)}>Past</button></div>}
    <p className="tracking-note"><Icon name="clock" size={15} />Kitchen updates every 4 seconds · No live rider GPS</p>
    {!visible.length && <div className="empty-state"><Icon name="receipt" size={40} /><h2>{focusedId !== undefined ? 'Order unavailable' : history ? 'Your next favourite is waiting.' : 'Nothing cooking just yet.'}</h2><p>{focusedId !== undefined ? 'Loading your orders. If this persists, return to All orders to choose an order belonging to your account.' : history ? 'Completed kitchen handoffs will appear here.' : 'Choose something delicious from the menu to get started.'}</p></div>}
    {billError && <p role="alert" className="error">{billError}</p>}
    <div className="orders">{visible.map(order => <article className="order" key={order.id}>
      <div className="row"><h2><Link href={`/orders/${order.id}`}>Order #{order.id}</Link></h2><strong>{money(order.total)}</strong></div>
      <div className="order-outlet"><Icon name="pin" size={14} />{({1:'Kondapur',2:'Gachibowli',3:'Madhapur'} as Record<number,string>)[order.outlet_id] || 'Your selected'} kitchen</div>
      <div className="order-lines">{order.lines.map((line, index) => <div className="order-line" key={index}><FoodImage name={line.name} /><div><strong>{line.name}</strong><small>{line.quantity} × {line.portion}{line.addon ? ' · extra raita' : ''}</small></div><span>{money(line.price * line.quantity)}</span></div>)}</div>
      <p className="delivery-address"><Icon name="pin" size={16} /><span>Delivering to<small>{order.address}</small></span></p>
      <div id={focusedId ? "order-tracking" : undefined} className="order-state"><strong>{order.status.replaceAll('_', ' ')}</strong>{order.minutes && <span><Icon name="clock" size={15} />{order.minutes} min prep estimate</span>}</div>
      {order.minutes && <p className="muted">Estimated ready {order.accepted && new Date((order.accepted + order.minutes * 60) * 1000).toLocaleTimeString('en-IN', { hour:'2-digit', minute:'2-digit' })}. Preparation only, not a delivery promise.</p>}
      {order.late && <p className="warning">Your kitchen is taking longer than estimated.</p>}
      {order.status !== 'PENDING_PAYMENT' && <ol className="timeline">{stages.map((stage,index) => <li className={index <= stages.indexOf(order.status) ? 'done' : ''} key={stage}><span className="stage-dot">{index <= stages.indexOf(order.status) && <Icon name="check" size={12} />}</span><span>{stage === 'NEW' ? 'Order confirmed' : stage === 'PREPARING' ? 'Preparing your food' : stage === 'READY' ? 'Ready for pickup' : 'Handed to delivery partner'}{stage === order.status && <small>Latest kitchen update</small>}</span></li>)}</ol>}
      {order.estimate_reason && <p className="warning">Updated by the manager: {order.estimate_reason}</p>}
      {notices.filter(n=>n.order_id===order.id).slice(0,5).map(n=><p key={n.id} className="order-notice">{n.message}{n.channel !== 'in_app' && <small>{n.channel.toUpperCase()}: {n.state === 'submitted' ? 'Submitted to messaging service' : n.state === 'failed' ? 'Could not send — update shown here' : 'Waiting for messaging service'}</small>}</p>)}
      <p>Payment: {order.payment.replaceAll('_', ' ')}</p>{order.payment === 'DEPOSIT_PAID' && <small>{money(order.total - order.due)} due on handoff</small>}
      {order.status === 'PENDING_PAYMENT' && <div className="payment"><p>Test payment · {money(order.due)}<small>No actual money will be charged.</small></p><button disabled={busy} onClick={() => pay(order,true)}>Simulate successful payment <Icon name="arrow" size={18} /></button><button className="quiet" disabled={busy} onClick={() => pay(order,false)}>Simulate failure</button></div>}
      {order.status !== 'PENDING_PAYMENT' && <div className="bill-actions"><button className="secondary" disabled={billBusy !== null} onClick={() => openBill(order)}>{billBusy === order.id ? 'Preparing bill…' : 'View / print demo bill'}</button><button className="quiet" disabled={billBusy !== null} onClick={() => openBill(order, true)}>Download bill</button><small>Sample tax invoice · not valid for tax purposes</small></div>}
      {order.status === 'HANDED_OFF' && <small>Kitchen handoff recorded. Delivery completion is not tracked in this demo.</small>}
    </article>)}</div>
  </section>;
}
