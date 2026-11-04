'use client';
import { useState } from 'react';
import { money, Order } from './api';
import { FoodImage } from './food-image';
import { Icon } from './ui-icon';

export function OrderHistory({ orders, busy, pay }: { orders: Order[]; busy: boolean; pay: (order: Order, success: boolean) => void }) {
  const [history, setHistory] = useState(false);
  const visible = history ? orders.filter(order => order.status === 'HANDED_OFF') : orders;
  const stages = ['NEW', 'PREPARING', 'READY', 'HANDED_OFF'];
  return <section className="order-page"><div className="page-title"><h1>Your orders</h1><p>From our kitchen to your doorstep. Follow the preparation here.</p></div>
    <div className="order-tabs"><button className={!history ? 'selected' : 'quiet'} onClick={() => setHistory(false)}>All orders</button><button className={history ? 'selected' : 'quiet'} onClick={() => setHistory(true)}>Past</button></div>
    <p className="tracking-note"><Icon name="clock" size={15} />Kitchen updates every 4 seconds · No live rider GPS</p>
    {!visible.length && <div className="empty-state"><Icon name="receipt" size={40} /><h2>{history ? 'Your next favourite is waiting.' : 'Nothing cooking just yet.'}</h2><p>{history ? 'Completed kitchen handoffs will appear here.' : 'Choose something delicious from the menu to get started.'}</p></div>}
    <div className="orders">{visible.map(order => <article className="order" key={order.id}>
      <div className="row"><h2>Order #{order.id}</h2><strong>{money(order.total)}</strong></div>
      <div className="order-outlet"><Icon name="pin" size={14} />{({1:'Kondapur',2:'Gachibowli',3:'Madhapur'} as Record<number,string>)[order.outlet_id] || 'Your selected'} kitchen</div>
      <div className="order-lines">{order.lines.map((line, index) => <div className="order-line" key={index}><FoodImage name={line.name} /><div><strong>{line.name}</strong><small>{line.quantity} × {line.portion}{line.addon ? ' · extra raita' : ''}</small></div><span>{money(line.price * line.quantity)}</span></div>)}</div>
      <p className="delivery-address"><Icon name="pin" size={16} /><span>Delivering to<small>{order.address}</small></span></p>
      <div className="order-state"><strong>{order.status.replaceAll('_', ' ')}</strong>{order.minutes && <span><Icon name="clock" size={15} />{order.minutes} min prep estimate</span>}</div>
      {order.minutes && <p className="muted">Estimated ready {order.accepted && new Date((order.accepted + order.minutes * 60) * 1000).toLocaleTimeString('en-IN', { hour:'2-digit', minute:'2-digit' })}. Preparation only, not a delivery promise.</p>}
      {order.late && <p className="warning">Your kitchen is taking longer than estimated.</p>}
      {order.status !== 'PENDING_PAYMENT' && <ol className="timeline">{stages.map((stage,index) => <li className={index <= stages.indexOf(order.status) ? 'done' : ''} key={stage}><span className="stage-dot">{index <= stages.indexOf(order.status) && <Icon name="check" size={12} />}</span><span>{stage === 'NEW' ? 'Order confirmed' : stage === 'PREPARING' ? 'Preparing your food' : stage === 'READY' ? 'Ready for pickup' : 'Handed to delivery partner'}{stage === order.status && <small>Latest kitchen update</small>}</span></li>)}</ol>}
      <p>Payment: {order.payment.replaceAll('_', ' ')}</p>{order.payment === 'DEPOSIT_PAID' && <small>{money(order.total - order.due)} due on handoff</small>}
      {order.status === 'PENDING_PAYMENT' && <div className="payment"><p>Test payment · {money(order.due)}<small>No actual money will be charged.</small></p><button disabled={busy} onClick={() => pay(order,true)}>Simulate successful payment <Icon name="arrow" size={18} /></button><button className="quiet" disabled={busy} onClick={() => pay(order,false)}>Simulate failure</button></div>}
      {order.status === 'HANDED_OFF' && <small>Kitchen handoff recorded. Delivery completion is not tracked in this demo.</small>}
    </article>)}</div>
  </section>;
}
