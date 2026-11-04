'use client';
import { FormEvent, useCallback, useEffect, useRef, useState } from 'react';
import { api, CartLine, Dish, money, Order, Outlet, User } from './api';
import { Staff } from './staff';

const areas = [{ name: 'Kondapur', lat: 17.462, lng: 78.357 }, { name: 'Gachibowli', lat: 17.441, lng: 78.349 }, { name: 'Madhapur', lat: 17.448, lng: 78.391 }];
const storageKey = 'dumhouse-cart-v1';
export default function Home() {
  const [user, setUser] = useState<User | null>(null);
  const [view, setView] = useState('menu');
  const [location, setLocation] = useState(areas[0]);
  const [outlets, setOutlets] = useState<Outlet[]>([]);
  const [outlet, setOutlet] = useState(0);
  const [dishes, setDishes] = useState<Dish[]>([]);
  const [cart, setCart] = useState<CartLine[]>([]);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [orders, setOrders] = useState<Order[]>([]);
  const [category, setCategory] = useState('All');
  const [address, setAddress] = useState('');
  const [method, setMethod] = useState('upi');
  const [register, setRegister] = useState(false);
  const checkoutKey = useRef('');
  const expiry = useRef(0);
  const restoredOutlet = useRef(0);

  useEffect(() => {
    api<User>('/auth/me').then(setUser).catch(() => {});
    try {
      const saved = JSON.parse(localStorage.getItem(storageKey) || 'null');
      if (saved && saved.expires > Date.now() && Array.isArray(saved.lines) && saved.location && typeof saved.outlet === 'number') {
        setCart(saved.lines); setLocation(saved.location); restoredOutlet.current = saved.outlet; expiry.current = saved.expires;
      }
    } catch { localStorage.removeItem(storageKey); }
    setReady(true);
  }, []);

  useEffect(() => {
    if (!ready) return;
    let active = true;
    api<Outlet[]>(`/outlets?lat=${location.lat}&lng=${location.lng}`).then(result => {
      if (!active) return;
      setOutlets(result);
      if (restoredOutlet.current && !result.some(item => item.id === restoredOutlet.current)) {
        setCart([]); setError('Your saved kitchen is no longer eligible. We cleared the cart; choose a kitchen to start again.');
      }
      setOutlet(result.some(item => item.id === restoredOutlet.current) ? restoredOutlet.current : result[0]?.id || 0);
      restoredOutlet.current = 0;
    }).catch(problem => active && setError(problem.message));
    return () => { active = false; };
  }, [location, ready]);

  useEffect(() => {
    let active = true;
    setDishes([]);
    if (outlet) api<Dish[]>(`/outlets/${outlet}/menu`).then(result => active && setDishes(result)).catch(problem => active && setError(problem.message));
    return () => { active = false; };
  }, [outlet]);

  useEffect(() => {
    checkoutKey.current = '';
    if (ready && outlet) {
      try { localStorage.setItem(storageKey, JSON.stringify({ lines: cart, outlet, location, expires: expiry.current })); }
      catch { setError('Browser storage is unavailable. Your cart cannot survive a refresh.'); }
    }
  }, [cart, outlet, location, ready]);

  useEffect(() => {
    const timer = setInterval(() => { if (expiry.current && Date.now() > expiry.current) { setCart([]); expiry.current = 0; } }, 30000);
    return () => clearInterval(timer);
  }, []);

  const refreshOrders = useCallback(async () => {
    if (user?.role === 'customer') setOrders(await api<Order[]>('/orders'));
  }, [user]);
  useEffect(() => {
    if (view !== 'orders' || user?.role !== 'customer') return;
    const refresh = () => refreshOrders().catch(problem => setError(`Tracking update failed: ${problem.message}`));
    refresh();
    const timer = setInterval(refresh, 4000);
    window.addEventListener('online', refresh); document.addEventListener('visibilitychange', refresh);
    return () => { clearInterval(timer); window.removeEventListener('online', refresh); document.removeEventListener('visibilitychange', refresh); };
  }, [view, user, refreshOrders]);

  async function action(work: () => Promise<void>) {
    setBusy(true); setError('');
    try { await work(); } catch (problem) { setError(problem instanceof Error ? problem.message : 'Something went wrong. Try again.'); }
    finally { setBusy(false); }
  }
  function changeLocation(next: typeof location) {
    if (cart.length && !window.confirm('Changing delivery area clears your cart. Continue?')) return;
    setCart([]); setOutlet(0); setOutlets([]); setLocation(next);
  }
  function changeOutlet(next: number) {
    if (cart.length && !window.confirm('Switching kitchens clears your cart. Continue?')) return;
    setCart([]); setOutlet(next);
  }
  function add(dish: Dish, portion: string, addon: boolean) {
    expiry.current = Date.now() + 3600000;
    setCart(previous => {
      const index = previous.findIndex(line => line.dish_id === dish.id && line.portion === portion && line.addon === addon);
      if (index >= 0) return previous.map((line, position) => position === index ? { ...line, quantity: Math.min(20, line.quantity + 1) } : line);
      return [...previous, { dish_id: dish.id, name: dish.name, quantity: 1, portion, addon, price: dish.price + dish.options[portion] + (addon ? 3000 : 0) }];
    });
  }
  async function checkout() {
    if (!user) { setView('signin'); return; }
    if (expiry.current <= Date.now()) { setCart([]); throw new Error('Your cart expired. Please add your dishes again.'); }
    if (!checkoutKey.current) checkoutKey.current = crypto.randomUUID();
    const body = { outlet_id: outlet, lat: location.lat, lng: location.lng, address, method, key: checkoutKey.current, lines: cart.map(({ dish_id, quantity, portion, addon }) => ({ dish_id, quantity, portion, addon })) };
    await api('/checkout/quote', 'POST', body);
    await api<Order>('/orders', 'POST', body);
    setCart([]); setView('orders'); await refreshOrders();
  }
  async function signin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    await action(async () => {
      const account = await api<User>(register ? '/auth/register' : '/auth/login', 'POST', { email: form.get('email'), password: form.get('password') });
      setUser(account); setView('menu');
    });
  }
  const count = cart.reduce((total, line) => total + line.quantity, 0);
  return <>
    <header><a className="brand" href="/">DumHouse<span>Hyderabad, served warm.</span></a><nav aria-label="Main navigation">
      <button className={view === 'menu' ? 'selected' : 'quiet'} onClick={() => setView('menu')}>Menu</button>
      {user?.role === 'customer' && <button className={view === 'orders' ? 'selected' : 'quiet'} onClick={() => setView('orders')}>Your orders</button>}
      {user ? <button className="quiet" disabled={busy} onClick={() => action(async () => { await api('/auth/logout', 'POST'); setUser(null); setOrders([]); setView('menu'); })}>Sign out</button> : <button className="quiet" onClick={() => setView('signin')}>Sign in</button>}
      {(!user || user.role === 'customer') && <button onClick={() => { setView('menu'); document.getElementById('cart')?.scrollIntoView({ behavior: 'smooth' }); }}>Your bag · {count}</button>}
    </nav></header>
    <div className="demo">Fictional restaurant demo · Test payments only · Sample Hyderabad delivery areas</div>
    {error && <div className="error" role="alert">{error}<button className="quiet" onClick={() => setError('')} aria-label="Dismiss error">Dismiss</button></div>}
    <main>
      {view === 'signin' ? <section className="auth"><h1>{register ? 'A seat at our table.' : 'Welcome back.'}</h1><p>Sign in to order, or use your assigned staff account.</p><form onSubmit={signin}><label>Email<input name="email" type="email" autoComplete="email" required /></label><label>Password<input name="password" type="password" minLength={10} maxLength={128} autoComplete={register ? 'new-password' : 'current-password'} required /></label><button disabled={busy}>{busy ? 'Please wait…' : register ? 'Create account' : 'Sign in'}</button></form><button className="quiet" onClick={() => setRegister(!register)}>{register ? 'Already registered? Sign in' : 'New here? Create an account'}</button><p className="muted">Demo customer: customer@demo.test<br />Password: DemoPass123!</p></section> : user && user.role !== 'customer' ? <Staff user={user} /> : view === 'orders' ? <section><h1>Your kitchen, in the loop.</h1><p>Updates every 4 seconds. Stages are reported by kitchen staff.</p>{!orders.length && <p className="empty">No orders yet. Your first dum biryani is waiting on the menu.</p>}<div className="orders">{orders.map(order => <article className="order" key={order.id}><div className="row"><h2>Order #{order.id}</h2><strong>{money(order.total)}</strong></div><p>{order.lines.map(line => `${line.quantity} × ${line.name} (${line.portion})`).join(', ')}</p><p className="muted">{order.address}</p><strong>{order.status.replaceAll('_', ' ')}</strong>{order.minutes && <p>Estimated preparation: {order.minutes} min · {order.accepted && new Date((order.accepted + order.minutes * 60) * 1000).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}<br /><small>Estimate only; does not indicate delivery.</small></p>}{order.late && <p className="warning">The kitchen is running later than estimated.</p>}{order.status !== 'PENDING_PAYMENT' && <ol className="timeline">{['NEW', 'PREPARING', 'READY', 'HANDED_OFF'].map((stage, index) => <li className={index <= ['NEW', 'PREPARING', 'READY', 'HANDED_OFF'].indexOf(order.status) ? 'done' : ''} key={stage}>{stage.replaceAll('_', ' ')}</li>)}</ol>}<p>Payment: {order.payment.replaceAll('_', ' ')}{order.payment === 'DEPOSIT_PAID' ? ` · ${money(order.total - order.due)} due on handoff` : ''}</p>{order.status === 'PENDING_PAYMENT' && <div className="payment"><p>Simulate {money(order.due)} payment. No real money moves.</p><div className="row"><button disabled={busy} onClick={() => action(async () => { await api(`/payments/mock/${order.id}/complete`, 'POST', { event: crypto.randomUUID(), success: true }); await refreshOrders(); })}>Simulate successful payment</button><button className="secondary" disabled={busy} onClick={() => action(async () => { await api(`/payments/mock/${order.id}/complete`, 'POST', { event: crypto.randomUUID(), success: false }); setError('Test payment failed. Your order remains unpaid; you can retry.'); await refreshOrders(); })}>Simulate failure</button></div></div>}</article>)}</div></section> : <>
        <section className="hero"><div><h1>Good things<br />take <em>dum.</em></h1><p>Slow-cooked biryani. Big Hyderabad flavour.<br />From your neighbourhood kitchen to your table.</p></div><div className="hero-note"><span>Sealed with care.</span><p>Choose your kitchen.<br />Make it your meal.<br />Follow every stage.</p></div></section>
        <section className="location" aria-label="Delivery and outlet selection"><div><label>Delivering to<select value={areas.findIndex(area => area.name === location.name)} onChange={event => changeLocation(areas[Number(event.target.value)])}>{!areas.some(area => area.name === location.name) && <option value={-1}>Current location</option>}{areas.map((area, index) => <option value={index} key={area.name}>{area.name} · sample area</option>)}</select></label><button className="quiet" onClick={() => { if (!navigator.geolocation) { setError('Location is unavailable. Choose a sample area.'); return; } navigator.geolocation.getCurrentPosition(position => changeLocation({ name: 'Current location', lat: position.coords.latitude, lng: position.coords.longitude }), () => setError('Location permission unavailable. Choose a sample area.'), { timeout: 10000 }); }}>Use my location</button></div><div><p className="label">Your kitchen · nearest recommended, your choice</p><div className="outlets">{outlets.map((item, index) => <button className={item.id === outlet ? 'selected' : 'secondary'} key={item.id} onClick={() => changeOutlet(item.id)}>{item.name}<small>{item.distance} km{index === 0 ? ' · Nearest' : ''}</small></button>)}{ready && !outlets.length && <p>No eligible kitchens for this location. Choose a sample area to explore.</p>}</div></div></section>
        <div className="shop"><section><div className="row"><h2>Find your favourite.</h2><span className="muted">Prices include taxes</span></div><div className="filters" aria-label="Menu categories">{['All', 'Biryani', 'Sides', 'Sweets'].map(item => <button className={category === item ? 'selected' : 'quiet'} key={item} onClick={() => setCategory(item)}>{item}</button>)}</div><div className="menu">{dishes.filter(dish => category === 'All' || dish.category === category).map(dish => <DishCard key={dish.id} dish={dish} add={add} />)}{outlet > 0 && !dishes.length && <p>Menu loading or temporarily unavailable. Please refresh if this continues.</p>}</div></section>
        <aside id="cart"><h2>Your bag <span>{count}</span></h2><p className="muted">{outlets.find(item => item.id === outlet)?.name || 'Choose a kitchen'}</p>{!cart.length ? <p className="empty">Something delicious belongs here.<br />Add a dish to get started.</p> : <>{cart.map((line, index) => <div className="cart-line" key={`${line.dish_id}-${line.portion}-${line.addon}`}><strong>{line.name}</strong><small>{line.portion}{line.addon ? ' · extra raita' : ''}</small><div className="row"><label>Qty<input aria-label={`Quantity ${line.name}`} type="number" min="1" max="20" value={line.quantity} onChange={event => { expiry.current = Date.now() + 3600000; setCart(cart.map((item, position) => position === index ? { ...item, quantity: Math.max(1, Math.min(20, Number(event.target.value))) } : item)); }} /></label><span>{money(line.price * line.quantity)}</span><button className="quiet" aria-label={`Remove ${line.name}`} onClick={() => setCart(cart.filter((_, position) => position !== index))}>Remove</button></div></div>)}<div className="row total"><strong>Estimated total</strong><strong>{money(cart.reduce((total, line) => total + line.quantity * line.price, 0))}</strong></div><form onSubmit={event => { event.preventDefault(); action(checkout); }}><label>Delivery address<textarea required minLength={5} maxLength={500} placeholder="Flat, building and landmark in your selected area" value={address} onChange={event => { setAddress(event.target.value); checkoutKey.current = ''; }} /></label><label>Payment<select value={method} onChange={event => { setMethod(event.target.value); checkoutKey.current = ''; }}><option value="upi">Test UPI</option><option value="card">Test card</option>{user?.cod && <option value="cod">Demo COD</option>}</select></label>{method === 'cod' && <small>Demo policy: orders above ₹1,500 need a 20% test deposit.</small>}<button disabled={busy || !outlet} type="submit">{busy ? 'Checking your order…' : user ? 'Continue to payment' : 'Sign in to checkout'}</button><small>Prices and availability are checked at checkout. Cart retained for 60 minutes.</small></form></>}</aside></div>
      </>}
    </main><footer>DumHouse · A fictional single-brand ordering project.<span>Prepared by people. Estimated by software.</span></footer>
  </>;
}

function DishCard({ dish, add }: { dish: Dish; add: (dish: Dish, portion: string, addon: boolean) => void }) {
  const [portion, setPortion] = useState(Object.keys(dish.options)[0]);
  const [addon, setAddon] = useState(false);
  const [added, setAdded] = useState(false);
  return <article className="dish"><div className="row"><span className={dish.veg ? 'diet veg' : 'diet'}>{dish.veg ? 'Vegetarian' : 'Non-vegetarian'}</span><span className="muted">{dish.category}</span></div><h3>{dish.name}</h3><p>{dish.description}</p><small>Allergens: {dish.allergens || 'None listed'}</small><div className="options"><label>Portion<select aria-label={`Portion for ${dish.name}`} value={portion} onChange={event => setPortion(event.target.value)}>{Object.entries(dish.options).map(([name, price]) => <option value={name} key={name}>{name}{price ? ` +${money(price)}` : ''}</option>)}</select></label><label className="check"><input type="checkbox" checked={addon} onChange={event => setAddon(event.target.checked)} /> Extra raita +₹30</label></div><div className="row"><strong>{money(dish.price + (dish.options[portion] || 0) + (addon ? 3000 : 0))}</strong><button aria-label={`Add ${dish.name}`} onClick={() => { add(dish, portion, addon); setAdded(true); setTimeout(() => setAdded(false), 1200); }}>{added ? 'Added to bag' : 'Add to bag'}</button></div></article>;
}
