'use client';
import { lineDescription } from './dish-options';
import { FormEvent, useCallback, useEffect, useState } from 'react';
import { api, Dish, money, Order, Outlet, User } from './api';

export function Staff({ user }: { user: User }) {
  const [alerts,setAlerts]=useState<{id:number;message:string;order_id:number}[]>([]);
  const [lastUpdate,setLastUpdate]=useState<number>(0);
  const [online,setOnline]=useState(true);
  const [orders, setOrders] = useState<Order[]>([]);
  const [dishes, setDishes] = useState<Dish[]>([]);
  const [outlets, setOutlets] = useState<Outlet[]>([]);
  const [outlet, setOutlet] = useState(1);
  const [assignments, setAssignments] = useState<Dish[]>([]);
  const [tab, setTab] = useState(user.role !== 'admin' ? 'queue' : 'catalog');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);
  const [editing, setEditing] = useState<Dish | null>(null);
  const refresh = useCallback(async () => {
    if (user.role !== 'admin') {
      const [queue, menu] = await Promise.all([api<Order[]>('/kitchen/orders'), api<Dish[]>('/kitchen/menu')]);
      setOrders(queue); setDishes(menu);
    } else {
      const [menu, kitchens, assigned] = await Promise.all([api<Dish[]>('/admin/menu-items'), api<Outlet[]>('/admin/outlets'), api<Dish[]>(`/admin/outlets/${outlet}/menu`)]);
      setDishes(menu); setOutlets(kitchens); setAssignments(assigned);
      if(tab==='queue') setOrders(await api<Order[]>(`/admin/outlets/${outlet}/orders`));
    }
    if(user.role==='manager'||user.role==='admin') setAlerts(await api<typeof alerts>('/notifications'));
    setLastUpdate(Date.now()); setOnline(navigator.onLine);
  }, [user.role, outlet, tab]);
  useEffect(() => {
    let active = true;
    const reload = () => { if (active) refresh().catch(problem => active && setError(problem.message)); };
    reload();
    const timer = setInterval(reload, user.role !== 'admin' || tab==='queue' ? 5000 : 30000);
    const offline=()=>setOnline(false); window.addEventListener('offline',offline);
    window.addEventListener('online', reload); document.addEventListener('visibilitychange', reload);
    return () => { active = false; clearInterval(timer); window.removeEventListener('offline',offline); window.removeEventListener('online', reload); document.removeEventListener('visibilitychange', reload); };
  }, [refresh, user.role]);
  async function change(work: () => Promise<unknown>) {
    setBusy(true); setError(''); setNotice('');
    try { await work(); await refresh(); setNotice('Changes saved.'); } catch (problem) { setError(problem instanceof Error ? problem.message : 'Could not save. Try again.'); }
    finally { setBusy(false); }
  }
  function saveDish(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    change(async () => {
      await api(`/admin/menu-items${editing?.id ? `/${editing.id}` : ''}`, editing?.id ? 'PATCH' : 'POST', { name: form.get('name'), description: form.get('description'), category: form.get('category'), price: Math.round(Number(form.get('price')) * 100), veg: form.get('veg') === 'on', allergens: form.get('allergens'), weight: Number(form.get('weight')), options: JSON.parse(String(form.get('options'))) });
      setEditing(null);
    });
  }
  return <section className="staff-workspace"><div className="row"><div><h1>{user.role !== 'admin' ? 'At the pass.' : 'One menu. Every kitchen.'}</h1><p>{user.email}{user.role !== 'admin' ? ' · Queue refreshes every 5 seconds' : ' · Central menu administrator'}</p></div></div>
    {error && <div className="error" role="alert">{error}</div>}{notice && <p role="status">{notice}</p>}
    <div className="filters">{(user.role !== 'admin' ? ['queue', 'availability'] : ['queue','catalog', 'assignments']).map(name => <button key={name} className={tab === name ? 'selected' : 'quiet'} onClick={() => setTab(name)}>{name}</button>)}</div>
    {!online && <p className="error" role="alert">Offline — this queue may be stale. Reconnect before changing an order.</p>}
    <p className="muted">Last refreshed: {lastUpdate ? new Date(lastUpdate).toLocaleTimeString() : 'Connecting…'}</p>
    {alerts.slice(0,10).map(a=><p className="warning" key={a.id}>Manager alert · {a.message}</p>)}
    {user.role==='admin' && tab==='queue' && <label>Kitchen<select value={outlet} onChange={event=>setOutlet(Number(event.target.value))}>{outlets.map(o=><option key={o.id} value={o.id}>{o.name}</option>)}</select></label>}
    {tab === 'queue' && <div className="board">{['NEW', 'PREPARING', 'READY'].map(stage => <section key={stage}><h2>{stage.toLowerCase()} <span>{orders.filter(order => order.status === stage).length}</span></h2>{orders.filter(order => order.status === stage).map(order => <article className={order.late ? "order kitchen-late" : "order"} key={order.id}><div className="row"><h3>#{order.id}</h3><strong>{money(order.total)}</strong></div>{order.lines.map((line, index) => <p className="kitchen-dish" key={index}><strong>{line.quantity} ×</strong> {line.name}<small>{lineDescription(line)}</small></p>)}<p className="kitchen-contact">{order.contact?.name}{order.contact?.phone && <> · <a href={`tel:${order.contact.phone}`}>{order.contact.phone}</a></>}</p><p className="kitchen-promise">Prep: {order.minutes} min</p><p className="muted">{order.accepted ? Math.floor((Date.now() / 1000 - order.accepted) / 60) : 0} min elapsed</p>{order.late && <p className="warning">OVERDUE · More than 10 minutes past the original promise</p>}{(user.role==='manager'||user.role==='admin') && stage !== 'READY' && <form key={`${order.id}-${order.version}`} className="estimate-form" onSubmit={event=>{event.preventDefault();const form=new FormData(event.currentTarget);change(()=>api(`/manager/orders/${order.id}/estimate`,'PATCH',{minutes:Number(form.get('minutes')),reason:form.get('reason'),version:order.version}));}}><label>Total minutes from order confirmation<input name="minutes" type="number" min={order.ai_minutes || 1} max={1440} defaultValue={order.minutes || 20} required /></label><label>Reason shown to customer<input name="reason" minLength={5} maxLength={300} required /></label><button disabled={busy || !online}>Update promise</button></form>}{user.role!=='admin' && <button disabled={busy || !online} onClick={() => change(() => api(`/kitchen/orders/${order.id}/status`, 'PATCH', { status: stage === 'NEW' ? 'PREPARING' : stage === 'PREPARING' ? 'READY' : 'HANDED_OFF', version: order.version }))}>{stage === 'NEW' ? 'Start preparing' : stage === 'PREPARING' ? 'Mark ready' : 'Mark handed off'}</button>}</article>)}{!orders.some(order => order.status === stage) && <p className="empty">No orders here.</p>}</section>)}</div>}
    {tab === 'availability' && <div className="list">{dishes.filter(dish => dish.enabled).map(dish => <div className="row" key={dish.id}><div><h3>{dish.name}</h3><p>{dish.available ? 'Available to order' : 'Sold out at your kitchen'}</p></div><button disabled={busy} className={dish.available ? 'secondary' : ''} onClick={() => change(() => api(`/kitchen/menu/${dish.id}`, 'PATCH', { available: !dish.available }))}>{dish.available ? 'Mark sold out' : 'Restore availability'}</button></div>)}</div>}
    {tab === 'catalog' && <><button onClick={() => setEditing({ id: 0, name: '', description: '', category: 'Biryani', price: 10000, veg: true, allergens: '', weight: 10, options: { regular: 0 }, available: true, enabled: true, override: null })}>Create dish</button>{editing && <form className="editor" key={editing.id} onSubmit={saveDish}><h2>{editing.id ? 'Edit dish' : 'New dish'}</h2><label>Name<input name="name" defaultValue={editing.name} required minLength={2} maxLength={100} /></label><label>Description<textarea name="description" defaultValue={editing.description} required minLength={5} /></label><div className="row"><label>Category<input name="category" defaultValue={editing.category} required /></label><label>Price in rupees<input name="price" type="number" min={1} max={10000} step="0.01" defaultValue={editing.price / 100} required /></label></div><label className="check"><input name="veg" type="checkbox" defaultChecked={editing.veg} />Vegetarian</label><label>Allergens<input name="allergens" defaultValue={editing.allergens} /></label><label>Preparation weight<input name="weight" type="number" min={1} max={60} defaultValue={editing.weight} required /></label><label>Portions and extra price in paise (JSON)<input name="options" defaultValue={JSON.stringify(editing.options)} required /></label><div className="row"><button disabled={busy}>Save dish</button><button type="button" className="quiet" onClick={() => setEditing(null)}>Cancel</button></div></form>}<div className="list">{dishes.map(dish => <div className="row" key={dish.id}><div><h3>{dish.name}</h3><p>{dish.category} · {money(dish.price)}</p></div><button className="secondary" onClick={() => setEditing(dish)}>Edit {dish.name}</button></div>)}</div></>}
    {tab === 'assignments' && <><label>Kitchen<select value={outlet} onChange={event => setOutlet(Number(event.target.value))}>{outlets.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><form onSubmit={event=>{event.preventDefault();const form=new FormData(event.currentTarget);change(()=>api(`/admin/outlets/${outlet}/licence`,'PATCH',{fssai:form.get('fssai')}));}}><label>Verified FSSAI licence number<input name="fssai" inputMode="numeric" pattern="[0-9]{14}" minLength={14} maxLength={14} required /></label><label className="check"><input type="checkbox" required />I verified this number against this outlet’s licence.</label><button disabled={busy}>Save outlet licence</button></form><p>Leave override blank to use the central price. Availability remains controlled by each kitchen.</p><div className="list">{dishes.map(dish => { const assignment = assignments.find(item => item.id === dish.id); return <form className="assignment row" key={`${outlet}-${dish.id}-${assignment?.enabled}-${assignment?.override}`} onSubmit={event => { event.preventDefault(); const form = new FormData(event.currentTarget); change(() => api(`/admin/outlets/${outlet}/menu/${dish.id}`, 'PATCH', { enabled: form.get('enabled') === 'on', price: form.get('price') ? Math.round(Number(form.get('price')) * 100) : null })); }}><h3>{dish.name}</h3><label className="check"><input name="enabled" type="checkbox" defaultChecked={assignment?.enabled || false} />Assigned</label><label>Override ₹<input name="price" type="number" min={1} max={10000} step="0.01" placeholder={String(dish.price / 100)} defaultValue={assignment?.override ? assignment.override / 100 : ''} /></label><button disabled={busy}>Save</button></form>; })}</div></>}
  </section>;
}
