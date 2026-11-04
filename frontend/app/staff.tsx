'use client';
import { FormEvent, useCallback, useEffect, useState } from 'react';
import { api, Dish, money, Order, Outlet, User } from './api';

export function Staff({ user }: { user: User }) {
  const [orders, setOrders] = useState<Order[]>([]);
  const [dishes, setDishes] = useState<Dish[]>([]);
  const [outlets, setOutlets] = useState<Outlet[]>([]);
  const [outlet, setOutlet] = useState(1);
  const [assignments, setAssignments] = useState<Dish[]>([]);
  const [tab, setTab] = useState(user.role === 'kitchen' ? 'queue' : 'catalog');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);
  const [editing, setEditing] = useState<Dish | null>(null);
  const refresh = useCallback(async () => {
    if (user.role === 'kitchen') {
      const [queue, menu] = await Promise.all([api<Order[]>('/kitchen/orders'), api<Dish[]>('/kitchen/menu')]);
      setOrders(queue); setDishes(menu);
    } else {
      const [menu, kitchens, assigned] = await Promise.all([api<Dish[]>('/admin/menu-items'), api<Outlet[]>('/admin/outlets'), api<Dish[]>(`/admin/outlets/${outlet}/menu`)]);
      setDishes(menu); setOutlets(kitchens); setAssignments(assigned);
    }
  }, [user.role, outlet]);
  useEffect(() => {
    let active = true;
    const reload = () => { if (active) refresh().catch(problem => active && setError(problem.message)); };
    reload();
    const timer = user.role === 'kitchen' ? setInterval(reload, 3000) : undefined;
    window.addEventListener('online', reload); document.addEventListener('visibilitychange', reload);
    return () => { active = false; clearInterval(timer); window.removeEventListener('online', reload); document.removeEventListener('visibilitychange', reload); };
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
  return <section><div className="row"><div><h1>{user.role === 'kitchen' ? 'At the pass.' : 'One menu. Every kitchen.'}</h1><p>{user.email}{user.role === 'kitchen' ? ' · Queue refreshes every 3 seconds' : ' · Central menu administrator'}</p></div></div>
    {error && <div className="error" role="alert">{error}</div>}{notice && <p role="status">{notice}</p>}
    <div className="filters">{(user.role === 'kitchen' ? ['queue', 'availability'] : ['catalog', 'assignments']).map(name => <button key={name} className={tab === name ? 'selected' : 'quiet'} onClick={() => setTab(name)}>{name}</button>)}</div>
    {tab === 'queue' && <div className="board">{['NEW', 'PREPARING', 'READY'].map(stage => <section key={stage}><h2>{stage.toLowerCase()} <span>{orders.filter(order => order.status === stage).length}</span></h2>{orders.filter(order => order.status === stage).map(order => <article className="order" key={order.id}><div className="row"><h3>#{order.id}</h3><strong>{money(order.total)}</strong></div>{order.lines.map((line, index) => <p key={index}>{line.quantity} × {line.name}<small>{line.portion}{line.addon ? ' · extra raita' : ''}</small></p>)}<p>Preparation estimate: {order.minutes} min</p><p className="muted">{order.accepted ? Math.floor((Date.now() / 1000 - order.accepted) / 60) : 0} min elapsed</p>{order.late && <p className="warning">Over 10 minutes past estimate</p>}<button disabled={busy} onClick={() => change(() => api(`/kitchen/orders/${order.id}/status`, 'PATCH', { status: stage === 'NEW' ? 'PREPARING' : stage === 'PREPARING' ? 'READY' : 'HANDED_OFF', version: order.version }))}>{stage === 'NEW' ? 'Start preparing' : stage === 'PREPARING' ? 'Mark ready' : 'Mark handed off'}</button></article>)}{!orders.some(order => order.status === stage) && <p className="empty">No orders here.</p>}</section>)}</div>}
    {tab === 'availability' && <div className="list">{dishes.filter(dish => dish.enabled).map(dish => <div className="row" key={dish.id}><div><h3>{dish.name}</h3><p>{dish.available ? 'Available to order' : 'Sold out at your kitchen'}</p></div><button disabled={busy} className={dish.available ? 'secondary' : ''} onClick={() => change(() => api(`/kitchen/menu/${dish.id}`, 'PATCH', { available: !dish.available }))}>{dish.available ? 'Mark sold out' : 'Restore availability'}</button></div>)}</div>}
    {tab === 'catalog' && <><button onClick={() => setEditing({ id: 0, name: '', description: '', category: 'Biryani', price: 10000, veg: true, allergens: '', weight: 10, options: { regular: 0 }, available: true, enabled: true, override: null })}>Create dish</button>{editing && <form className="editor" key={editing.id} onSubmit={saveDish}><h2>{editing.id ? 'Edit dish' : 'New dish'}</h2><label>Name<input name="name" defaultValue={editing.name} required minLength={2} maxLength={100} /></label><label>Description<textarea name="description" defaultValue={editing.description} required minLength={5} /></label><div className="row"><label>Category<input name="category" defaultValue={editing.category} required /></label><label>Price in rupees<input name="price" type="number" min={1} max={10000} step="0.01" defaultValue={editing.price / 100} required /></label></div><label className="check"><input name="veg" type="checkbox" defaultChecked={editing.veg} />Vegetarian</label><label>Allergens<input name="allergens" defaultValue={editing.allergens} /></label><label>Preparation weight<input name="weight" type="number" min={1} max={60} defaultValue={editing.weight} required /></label><label>Portions and extra price in paise (JSON)<input name="options" defaultValue={JSON.stringify(editing.options)} required /></label><div className="row"><button disabled={busy}>Save dish</button><button type="button" className="quiet" onClick={() => setEditing(null)}>Cancel</button></div></form>}<div className="list">{dishes.map(dish => <div className="row" key={dish.id}><div><h3>{dish.name}</h3><p>{dish.category} · {money(dish.price)}</p></div><button className="secondary" onClick={() => setEditing(dish)}>Edit {dish.name}</button></div>)}</div></>}
    {tab === 'assignments' && <><label>Kitchen<select value={outlet} onChange={event => setOutlet(Number(event.target.value))}>{outlets.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><p>Leave override blank to use the central price. Availability remains controlled by each kitchen.</p><div className="list">{dishes.map(dish => { const assignment = assignments.find(item => item.id === dish.id); return <form className="assignment row" key={`${outlet}-${dish.id}-${assignment?.enabled}-${assignment?.override}`} onSubmit={event => { event.preventDefault(); const form = new FormData(event.currentTarget); change(() => api(`/admin/outlets/${outlet}/menu/${dish.id}`, 'PATCH', { enabled: form.get('enabled') === 'on', price: form.get('price') ? Math.round(Number(form.get('price')) * 100) : null })); }}><h3>{dish.name}</h3><label className="check"><input name="enabled" type="checkbox" defaultChecked={assignment?.enabled || false} />Assigned</label><label>Override ₹<input name="price" type="number" min={1} max={10000} step="0.01" placeholder={String(dish.price / 100)} defaultValue={assignment?.override ? assignment.override / 100 : ''} /></label><button disabled={busy}>Save</button></form>; })}</div></>}
  </section>;
}
