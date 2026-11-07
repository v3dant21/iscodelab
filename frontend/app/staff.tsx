'use client';
import { StaffOrders } from './staff-orders';
import { MenuEditor } from './menu-editor';
import { OutletDashboard } from './outlet-dashboard';
import { CateringDesk } from './party-orders';
import { KitchenActions, CancelOrder } from './kitchen-actions';
import { lineDescription } from './dish-options';
import { FormEvent, useCallback, useEffect, useState } from 'react';
import { api, Dish, money, Order, Outlet, User } from './api';

export function Staff({user}:{user:User}) { return user.role==='catering_manager' ? <section className="staff-workspace"><h1>Catering desk</h1><CateringDesk /></section> : <StaffWorkspace user={user}/>; }

function StaffWorkspace({ user }: { user: User }) {
  const [now,setNow]=useState(Date.now());
  useEffect(()=>{const timer=setInterval(()=>setNow(Date.now()),1000);return()=>clearInterval(timer);},[]);
  const [alerts,setAlerts]=useState<{id:number;message:string;order_id:number}[]>([]);
  const [lastUpdate,setLastUpdate]=useState<number>(0);
  const [online,setOnline]=useState(true);
  const [orders, setOrders] = useState<Order[]>([]);
  const [dishes, setDishes] = useState<Dish[]>([]);
  const [outlets, setOutlets] = useState<Outlet[]>([]);
  const [outlet, setOutlet] = useState(1);
  const [assignments, setAssignments] = useState<Dish[]>([]);
  const [tab, setTab] = useState('queue');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);
  const [editing, setEditing] = useState<Dish | null>(null);
  useEffect(()=>{if(editing){document.querySelector('.menu-editor')?.scrollIntoView({block:'start'});document.querySelector<HTMLInputElement>('.menu-editor input[name="name"]')?.focus({preventScroll:true});}},[editing]);
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
    setLastUpdate(Date.now()); setOnline(navigator.onLine); setError('');
  }, [user.role, outlet, tab]);
  useEffect(() => {
    let active = true;
    const reload = () => { if (active) refresh().catch(problem => active && (setError(problem.message),setOnline(false))); };
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
  function saveDish(value: Record<string,unknown>) {
    change(async () => {
      await api(`/admin/menu-items${editing?.id ? `/${editing.id}` : ''}`, editing?.id ? 'PATCH' : 'POST', value);
      setEditing(null);
    });
  }
  return <section className="staff-workspace"><div className="row"><div><h1>{user.role !== 'admin' ? 'At the pass.' : 'One menu. Every kitchen.'}</h1><p>{user.name || user.email}{user.outlet_id ? ` · Outlet ${user.outlet_id}` : ''}{user.role !== 'admin' ? ' · Queue refreshes every 5 seconds' : ' · Central menu administrator'}</p></div></div>
    {error && <div className="error" role="alert">{error}</div>}{notice && <p role="status">{notice}</p>}
    <div className="filters">{(user.role !== 'admin' ? user.role==='manager'?['queue','history','availability','dashboard']:['queue','history', 'availability'] : ['queue','history','catalog', 'assignments','catering','dashboard']).map(name => <button key={name} className={tab === name ? 'selected' : 'quiet'} onClick={() => setTab(name)}>{name}</button>)}</div>
    {!online && <p className="error" role="alert">Connection interrupted — this queue may be stale. Reconnect before changing an order.</p>}
    <p className="muted">Last refreshed: {lastUpdate ? new Date(lastUpdate).toLocaleTimeString() : 'Connecting…'}</p>
    {alerts.slice(0,10).map(a=><p className="warning" key={a.id}>Manager alert · {a.message}</p>)}
    {user.role==='admin' && (tab==='queue'||tab==='history') && <label>Kitchen<select value={outlet} onChange={event=>setOutlet(Number(event.target.value))}>{outlets.map(o=><option key={o.id} value={o.id}>{o.name}</option>)}</select></label>}
    {tab==='history'&&<StaffOrders key={outlet} outlet={user.role==='admin'?outlet:undefined}/>}
    {tab === 'queue' && !lastUpdate && !error && <p role="status">Loading kitchen orders…</p>}
    {tab === 'queue' && lastUpdate>0 && <div className="board">{['NEW', 'PREPARING', 'READY'].map(stage => <section key={stage}><h2>{stage==='READY'?'Ready for pickup':stage==='PREPARING'?'Preparing':'New orders'} <span>{orders.filter(order => order.status === stage).length}</span></h2>{orders.filter(order => order.status === stage).map(order => <article className={order.late || (order.status!=='READY' && order.accepted && now/1000>order.accepted+(order.minutes||0)*60) ? "order kitchen-late" : "order"} key={order.id}><div className="row"><h3>#{order.id}</h3><strong>{money(order.total)}</strong></div>{order.lines.map((line, index) => <p className="kitchen-dish" key={index}><strong>{line.quantity} ×</strong> {line.name}<small>{lineDescription(line)}</small></p>)}<p className="kitchen-contact">{order.contact?.name}{order.contact?.phone && <> · <a href={`tel:${order.contact.phone}`}>{order.contact.phone}</a></>}</p><p className="kitchen-promise">Prep: {order.minutes} min</p><p className="kitchen-timer" role="timer">{order.status==='READY'?'Waiting for rider':'Elapsed'} · {Math.max(0,Math.floor((now/1000-(order.status==='READY'&&order.ready_at?order.ready_at:order.accepted||now/1000))/60))}:{String(Math.max(0,Math.floor(now/1000-(order.status==='READY'&&order.ready_at?order.ready_at:order.accepted||now/1000)))%60).padStart(2,'0')}</p>{order.late && <p className="warning">OVERDUE · More than 10 minutes past the original promise</p>}{(user.role==='manager'||user.role==='admin') && stage !== 'READY' && <form key={`${order.id}-${order.version}`} className="estimate-form" onSubmit={event=>{event.preventDefault();const form=new FormData(event.currentTarget);change(()=>api(`/manager/orders/${order.id}/estimate`,'PATCH',{minutes:Number(form.get('minutes')),reason:form.get('reason'),version:order.version}));}}><label>Total minutes from order confirmation<input name="minutes" type="number" min={order.ai_minutes || 1} max={1440} defaultValue={order.minutes || 20} required /></label><label>Reason shown to customer<input name="reason" minLength={5} maxLength={300} required /></label><button disabled={busy || !online}>Update promise</button></form>}{user.role!=='admin' && <KitchenActions key={order.version} order={order} disabled={busy||!online} change={change}/>} {['manager','admin'].includes(user.role)&&<CancelOrder order={order} disabled={busy||!online} change={change}/>}</article>)}{!orders.some(order => order.status === stage) && <p className="empty">No orders here.</p>}</section>)}</div>}
    {tab === 'availability' && <div className="list">{dishes.filter(dish => dish.enabled).map(dish => <div className="row" key={dish.id}><div><h3>{dish.name}</h3><p>{!dish.available ? 'Sold out at your kitchen' : dish.scheduled_now === false ? 'Outside serving hours' : 'Available to order'}</p></div><button disabled={busy||!online} className={dish.available ? 'secondary' : ''} onClick={() => change(() => api(`/kitchen/menu/${dish.id}`, 'PATCH', { available: !dish.available }))}>{dish.available ? 'Mark sold out' : 'Restore availability'}</button></div>)}</div>}
    {tab === 'catalog' && <><button onClick={() => setEditing({ id: 0, name: '', description: '', category: 'Biryani', price: 10000, veg: true, allergens: '', weight: 10, options: { regular: 0 }, available: true, enabled: true, override: null })}>Create dish</button>{editing && <MenuEditor key={editing.id} dish={editing} busy={busy} onSave={saveDish} onCancel={()=>setEditing(null)}/>}<div className="list">{dishes.map(dish => <div className="row" key={dish.id}><div><h3>{dish.name}</h3><p>{dish.category} · {money(dish.price)}</p></div><button className="secondary" onClick={() => setEditing(dish)}>Edit {dish.name}</button></div>)}</div></>}
    {tab === 'assignments' && <><label>Kitchen<select value={outlet} onChange={event => setOutlet(Number(event.target.value))}>{outlets.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><form onSubmit={event=>{event.preventDefault();const form=new FormData(event.currentTarget);change(()=>api(`/admin/outlets/${outlet}/licence`,'PATCH',{fssai:form.get('fssai')}));}}><label>Verified FSSAI licence number<input name="fssai" inputMode="numeric" pattern="[0-9]{14}" minLength={14} maxLength={14} required /></label><label className="check"><input type="checkbox" required />I verified this number against this outlet’s licence.</label><button disabled={busy}>Save outlet licence</button></form><form key={`city-${outlet}-${outlets.find(o=>o.id===outlet)?.city}`} onSubmit={e=>{e.preventDefault();const f=new FormData(e.currentTarget);change(()=>api(`/admin/outlets/${outlet}/city`,'PATCH',{city:f.get('city')}));}}><label>Outlet city<input name="city" defaultValue={outlets.find(o=>o.id===outlet)?.city || 'Hyderabad'} minLength={2} maxLength={80} required/></label><button disabled={busy}>Save city</button></form><p>Leave override blank to use the city price, or the base price if no city price is set. Availability remains controlled by each kitchen.</p><div className="list">{dishes.map(dish => { const assignment = assignments.find(item => item.id === dish.id); return <form className="assignment row" key={`${outlet}-${dish.id}-${assignment?.enabled}-${assignment?.override}`} onSubmit={event => { event.preventDefault(); const form = new FormData(event.currentTarget); change(() => api(`/admin/outlets/${outlet}/menu/${dish.id}`, 'PATCH', { enabled: form.get('enabled') === 'on', price: form.get('price') ? Math.round(Number(form.get('price')) * 100) : null })); }}><h3>{dish.name}</h3><label className="check"><input name="enabled" type="checkbox" defaultChecked={assignment?.enabled || false} />Assigned</label><label>Override ₹<input name="price" type="number" min={1} max={10000} step="0.01" placeholder={String(dish.price / 100)} defaultValue={assignment?.override ? assignment.override / 100 : ''} /></label><button disabled={busy}>Save</button></form>; })}</div></>}
    {tab==='catering'&&<CateringDesk/>}{tab==='dashboard'&&<OutletDashboard/>}
  </section>;
}
