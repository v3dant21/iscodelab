'use client';
import { FormEvent, useCallback, useEffect, useRef, useState } from 'react';
import { api, CartLine, Dish, money, Order, Outlet, User } from './api';
import { Staff } from './staff';
import { Icon } from './ui-icon';
import { FoodImage } from './food-image';
import { OrderHistory } from './order-history';

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
  const [search, setSearch] = useState('');
  const [vegetarian, setVegetarian] = useState(false);
  const [menuLoading, setMenuLoading] = useState(true);
  const [bagRequested, setBagRequested] = useState(false);
  const [address, setAddress] = useState('');
  const [method, setMethod] = useState('upi');
  const [register, setRegister] = useState(false);
  const [saved, setSaved] = useState<number[]>([]);
  const [searchRequested, setSearchRequested] = useState(false);
  const checkoutKey = useRef('');
  const checkoutAfterLogin = useRef(false);
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
    try { const favorites = JSON.parse(localStorage.getItem('dumhouse-saved') || '[]'); if (Array.isArray(favorites)) setSaved(favorites.filter(value => typeof value === 'number')); } catch {}
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
    setMenuLoading(Boolean(outlet));
    if (outlet) api<Dish[]>(`/outlets/${outlet}/menu`).then(result => { if (active) { setDishes(result); setMenuLoading(false); } }).catch(problem => { if (active) { setError(problem.message); setMenuLoading(false); } });
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

  useEffect(() => {
    if (bagRequested && view === 'bag') {
      const bag = document.getElementById('cart');
      if (bag) {
        bag.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth', block: 'start' });
        bag.focus({ preventScroll: true });
        setBagRequested(false);
      }
    }
  }, [bagRequested, view]);
  function openBag() { setView('bag'); setBagRequested(true); }
  function toggleSaved(id: number) {
    const updated = saved.includes(id) ? saved.filter(item => item !== id) : [...saved, id];
    setSaved(updated);
    try { localStorage.setItem('dumhouse-saved', JSON.stringify(updated)); } catch { setError('Saved dishes cannot be stored in this browser.'); }
  }
  function openSaved() { setSearch(''); setCategory('All'); setVegetarian(false); setView('saved'); }
  useEffect(() => {
    if (searchRequested && view === 'menu') {
      document.getElementById('menu-search')?.focus();
      document.getElementById('menu-search')?.scrollIntoView({ block: 'center', behavior: 'smooth' });
      setSearchRequested(false);
    }
  }, [searchRequested, view]);
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
  function editLine(index: number, portion: string, addon: boolean) {
    const line = cart[index];
    const dish = dishes.find(item => item.id === line.dish_id);
    if (!dish || !(portion in dish.options)) { setError('This item is no longer available. Remove it and choose another dish.'); return; }
    const match = cart.findIndex((item, position) => position !== index && item.dish_id === line.dish_id && item.portion === portion && item.addon === addon);
    if (match >= 0 && cart[match].quantity + line.quantity > 20) { setError('You can order up to 20 of the same customization. Reduce the quantity first.'); return; }
    const updated = { ...line, portion, addon, price: dish.price + dish.options[portion] + (addon ? 3000 : 0) };
    expiry.current = Date.now() + 3600000;
    setCart(cart.flatMap((item, position) => {
      if (position === index) return match >= 0 ? [] : [updated];
      return [position === match ? { ...updated, quantity: item.quantity + line.quantity } : item];
    }));
  }
  async function checkout() {
    if (!user) { checkoutAfterLogin.current = true; setView('signin'); return; }
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
      setUser(account); setView(checkoutAfterLogin.current && account.role === 'customer' ? 'bag' : 'menu');
      checkoutAfterLogin.current = false;
    });
  }
  const count = cart.reduce((total, line) => total + line.quantity, 0);
  const cartTotal = cart.reduce((total, line) => total + line.quantity * line.price, 0);
  const selectedOutlet = outlets.find(item => item.id === outlet);
  const visibleDishes = dishes.filter(dish => (view !== 'saved' || saved.includes(dish.id)) && (category === 'All' || dish.category === category) && (!vegetarian || dish.veg) && `${dish.name} ${dish.description}`.toLowerCase().includes(search.toLowerCase()));
  const categories = ['All', ...Array.from(new Set(dishes.map(dish => dish.category)))];
  return <>
    <a className="skip-link" href="#main">Skip to content</a><header><a className="brand" href="/" aria-label="DumHouse home"><span className="brand-symbol"><Icon name="food" size={22} /></span><span className="brand-text">DumHouse<small>HYDERABAD KITCHENS</small></span></a><nav aria-label="Main navigation">
      <button className={view === 'menu' ? 'selected' : 'quiet'} onClick={() => setView('menu')}>Menu</button><button className={view === 'saved' ? 'selected' : 'quiet'} onClick={openSaved}>Saved</button>
      {user?.role === 'customer' && <button className={view === 'orders' ? 'selected' : 'quiet'} onClick={() => setView('orders')}>Your orders</button>}
      {user ? <button className="quiet" disabled={busy} onClick={() => action(async () => { await api('/auth/logout', 'POST'); setUser(null); setOrders([]); setView('menu'); })}>Sign out</button> : <button className="quiet" onClick={() => setView('signin')}>Sign in</button>}
      {(!user || user.role === 'customer') && <button className="header-bag" onClick={openBag} aria-label={`Your bag · ${count}`}><Icon name="bag" /><span>Your bag</span><span className="bag-count">{count}</span></button>}
    </nav></header>
    <div className="demo"><span>Hyderabad flavours. One DumHouse.</span><span>Demo kitchens · Test payments only</span></div>
    {error && <div className="error" role="alert">{error}<button className="quiet" onClick={() => setError('')} aria-label="Dismiss error">Dismiss</button></div>}
    <main id="main" className={`${view}-view`}>
      {view === 'signin' ? <section className="auth"><h1>{register ? 'A seat at our table.' : 'Welcome back.'}</h1><p>Sign in to order, or use your assigned staff account.</p><form onSubmit={signin}><label>Email<input name="email" type="email" autoComplete="email" required /></label><label>Password<input name="password" type="password" minLength={10} maxLength={128} autoComplete={register ? 'new-password' : 'current-password'} required /></label><button disabled={busy}>{busy ? 'Please wait…' : register ? 'Create account' : 'Sign in'}</button></form><button className="quiet" onClick={() => setRegister(!register)}>{register ? 'Already registered? Sign in' : 'New here? Create an account'}</button><p className="muted">Demo customer: customer@demo.test<br />Password: DemoPass123!</p></section> : user && user.role !== 'customer' ? <Staff user={user} /> : view === 'account' && user ? <section className="account-page"><div className="profile-avatar"><Icon name="user" size={34} /></div><h1>Your account</h1><p>{user.email}</p><div className="account-actions"><button className="secondary" onClick={() => setView('orders')}><Icon name="receipt" />Your orders<Icon name="arrow" /></button><button className="secondary" onClick={openSaved}><Icon name="heart" />Saved dishes<Icon name="arrow" /></button><button className="secondary" onClick={openBag}><Icon name="bag" />Your bag<Icon name="arrow" /></button></div><p className="muted">{user.cod ? 'Demo COD available on this account.' : 'This account uses prepaid test payments.'}</p><button className="quiet" disabled={busy} onClick={() => action(async () => { await api('/auth/logout', 'POST'); setUser(null); setOrders([]); setView('menu'); })}>Sign out</button></section> : view === 'orders' ? <OrderHistory orders={orders} busy={busy} pay={(order, success) => action(async () => { await api(`/payments/mock/${order.id}/complete`, 'POST', { event: crypto.randomUUID(), success }); if (!success) setError('Test payment failed. Your order remains unpaid; you can retry.'); await refreshOrders(); })} /> : <>
        <section className="location" aria-label="Delivery and outlet selection">
          <div className="delivery-control"><Icon name="pin" /><label>Delivering to<select value={areas.findIndex(area => area.name === location.name)} onChange={event => changeLocation(areas[Number(event.target.value)])}>{!areas.some(area => area.name === location.name) && <option value={-1}>Current location</option>}{areas.map((area, index) => <option value={index} key={area.name}>{area.name} · sample area</option>)}</select></label></div>
          <div className="kitchen-control"><label>Your kitchen<select aria-label="Your kitchen" value={outlet} disabled={!outlets.length} onChange={event => changeOutlet(Number(event.target.value))}>{!outlets.length && <option value={0}>No eligible kitchen</option>}{outlets.map((item, index) => <option value={item.id} key={item.id}>{item.name} · {item.distance} km{index === 0 ? ' · Nearest' : ''}</option>)}</select></label></div>
          <div className="prep-note"><Icon name="clock" /><span>{selectedOutlet ? `From ${selectedOutlet.minimum} min` : 'Choose your location'}<small>Preparation estimate</small></span></div>
          <button className="quiet locate" onClick={() => { if (!navigator.geolocation) { setError('Location is unavailable. Choose a sample area.'); return; } navigator.geolocation.getCurrentPosition(position => changeLocation({ name: 'Current location', lat: position.coords.latitude, lng: position.coords.longitude }), () => setError('Location permission unavailable. Choose a sample area.'), { timeout: 10000 }); }}>Use my location <Icon name="pin" size={16} /></button>
          {ready && !outlets.length && <p className="location-empty">No kitchens deliver here. Select a sample area to explore the menu.</p>}
        </section>
        {view === 'menu' && <><div className="welcome"><h1>What are you craving?</h1><p>A proper Hyderabadi meal is just a few taps away.</p></div>
        <section className="hero">
          <div className="hero-copy"><h2>Hyderabad's heart.<br /><em>In every dum.</em></h2><p>Slow-cooked biryani, bold sides<br />and a sweet finish.</p><a className="button-link" href="#menu">Find your favourite <Icon name="arrow" size={17} /></a></div>
          <figure className="hero-image"><img src="/images/dumhouse-biryani.png" alt="Illustrative Hyderabadi biryani in a brass bowl, served with raita" width="1536" height="1024" fetchPriority="high" /><figcaption>Illustrative food photography</figcaption></figure>
        </section></>}
        {view === 'saved' && <div className="page-title"><h1>Saved for your next craving</h1><p>Your favourites, ready when you are. Saved on this browser.</p></div>}
        {view === 'bag' && <div className="page-title"><button className="quiet back-menu" onClick={() => setView('menu')}>Back to menu</button><h1>Your order</h1><p>From {selectedOutlet?.name || 'your selected'} kitchen, with love.</p></div>}
        <div className="shop" id="menu"><section className="menu-column" aria-label="Food menu">
          <div className="menu-heading"><div><h2>{view === 'saved' ? 'Your saved dishes' : 'The DumHouse menu'}</h2><p>{view === 'saved' ? 'Tap the heart to keep a favourite.' : 'Biryani, sides & a little something sweet.'}</p></div><span className="tax-note">Prices include taxes</span></div>
          <div className="menu-tools"><label className="search-control"><Icon name="search" size={18} /><input id="menu-search" aria-label="Search the menu" type="search" placeholder="Search biryani, sides, sweets…" value={search} onChange={event => setSearch(event.target.value)} /></label><button className={vegetarian ? 'veg-filter active' : 'veg-filter'} aria-pressed={vegetarian} onClick={() => setVegetarian(!vegetarian)}><Icon name="leaf" size={17} /> Vegetarian</button></div>
          <div className="filters" aria-label="Menu categories">{categories.map(item => <button aria-label={item === 'All' ? 'Full menu' : item} aria-pressed={category === item} className={category === item ? 'selected' : 'quiet'} key={item} onClick={() => setCategory(item)}><span className="category-art">{item === 'Biryani' ? <FoodImage name="Dum chicken biryani" /> : item === 'Sides' ? <FoodImage name="Chicken 65" /> : item === 'Sweets' ? <FoodImage name="Double ka meetha" /> : <Icon name="food" size={24} />}</span>{item === 'All' ? 'Full menu' : item}<span className="category-count">{item === 'All' ? dishes.length : dishes.filter(dish => dish.category === item).length}</span></button>)}</div>
          <div className="menu" aria-busy={menuLoading}>{visibleDishes.map(dish => <DishCard key={dish.id} dish={dish} add={add} saved={saved.includes(dish.id)} toggleSaved={() => toggleSaved(dish.id)} />)}{menuLoading ? <p className="empty" role="status">Your kitchen is setting the menu…</p> : !visibleDishes.length && <div className="empty"><h3>{view === 'saved' ? 'Make room for your favourites.' : dishes.length ? 'Nothing on this page, yet.' : 'The menu is taking a break.'}</h3><p>{view === 'saved' ? 'Tap a heart on the menu to save a dish here.' : dishes.length ? 'Try another search or explore the full menu.' : 'Choose another eligible kitchen, or check back shortly.'}</p>{dishes.length > 0 && <button className="secondary" onClick={() => { setSearch(''); setVegetarian(false); setCategory('All'); setView('menu'); }}>Show full menu</button>}</div>}</div>
          <p className="menu-footnote">Photos are illustrative. Portions, prices and availability come from your selected kitchen.</p>
        </section>
        <aside id="cart" tabIndex={-1} aria-label="Your bag"><div className="bag-heading"><h2>Your bag</h2><span className="bag-count">{count}</span></div><p className="bag-kitchen"><Icon name="pin" size={14} />{selectedOutlet?.name || 'Choose a kitchen'} kitchen</p>{!cart.length ? <div className="empty-bag"><Icon name="bag" size={40} /><h3>A good meal starts here.</h3><p>Add something you love.<br />We’ll take it from there.</p><a href="#menu" onClick={() => setView('menu')}>Discover the menu <Icon name="arrow" size={16} /></a></div> : <>{cart.map((line, index) => <div className="cart-line" key={`${line.dish_id}-${index}`}><FoodImage className="cart-thumbnail" name={line.name} /><strong>{line.name}</strong><small>{line.portion}{line.addon ? ' · extra raita' : ''}</small>{dishes.find(dish => dish.id === line.dish_id) && <details className="bag-customize"><summary>Edit item</summary><label>Portion<select aria-label={`Bag portion for ${line.name}`} value={line.portion} onChange={event => editLine(index, event.target.value, line.addon)}>{Object.entries(dishes.find(dish => dish.id === line.dish_id)!.options).map(([portion, price]) => <option key={portion} value={portion}>{portion}{price ? ` +${money(price)}` : ''}</option>)}</select></label><label className="check"><input aria-label={`Extra raita for ${line.name}`} type="checkbox" checked={line.addon} onChange={event => editLine(index, line.portion, event.target.checked)} />Extra raita +₹30</label><small>Changes save automatically.</small></details>}<div className="row"><label>Qty<input aria-label={`Quantity ${line.name}`} type="number" min="1" max="20" value={line.quantity} onChange={event => { expiry.current = Date.now() + 3600000; setCart(cart.map((item, position) => position === index ? { ...item, quantity: Math.max(1, Math.min(20, Number(event.target.value))) } : item)); }} /></label><span>{money(line.price * line.quantity)}</span><button className="quiet" aria-label={`Remove ${line.name}`} onClick={() => setCart(cart.filter((_, position) => position !== index))}>Remove</button></div></div>)}<div className="row total"><strong>Estimated total</strong><strong>{money(cartTotal)}</strong></div><form onSubmit={event => { event.preventDefault(); action(checkout); }}><label>Delivery address<textarea required minLength={5} maxLength={500} placeholder="Flat, building and landmark in your selected area" value={address} onChange={event => { setAddress(event.target.value); checkoutKey.current = ''; }} /></label><label>Payment<select value={method} onChange={event => { setMethod(event.target.value); checkoutKey.current = ''; }}><option value="upi">Test UPI</option><option value="card">Test card</option>{user?.cod && <option value="cod">Demo COD</option>}</select></label>{method === 'cod' && <small>Demo policy: orders above ₹1,500 need a 20% test deposit.</small>}<button disabled={busy || !outlet} type="submit">{busy ? 'Checking your order…' : user ? 'Continue to payment' : 'Sign in to checkout'}</button><small>Prices and availability are checked at checkout. Cart retained for 60 minutes.</small></form></>}</aside></div>
      </>}
    </main>
    {(view === 'menu' || view === 'saved') && (!user || user.role === 'customer') && count > 0 && <button className="mobile-bag" onClick={openBag}><span><Icon name="bag" /><strong>{count} {count === 1 ? 'item' : 'items'}</strong><span>{money(cartTotal)}</span></span><span>View bag <Icon name="arrow" size={18} /></span></button>}
    {(!user || user.role === 'customer') && <nav className="bottom-nav" aria-label="App navigation">
      <button className={view === 'menu' && !searchRequested ? 'active' : ''} onClick={() => { setView('menu'); window.scrollTo({top:0,behavior:'smooth'}); }}><Icon name="home" /><span>Home</span></button>
      <button onClick={() => { setView('menu'); setSearchRequested(true); }}><Icon name="search" /><span>Search</span></button>
      <button className={view === 'orders' ? 'active' : ''} onClick={() => setView(user ? 'orders' : 'signin')}><Icon name="receipt" /><span>Orders</span></button>
      <button className={view === 'saved' ? 'active' : ''} onClick={openSaved}><Icon name="heart" /><span>Saved</span></button>
      <button className={view === 'account' || view === 'signin' ? 'active' : ''} onClick={() => setView(user ? 'account' : 'signin')}><Icon name="user" /><span>Account</span></button>
    </nav>}
    <footer><div><a className="footer-brand" href="/">dumhouse</a><p>Hyderabad, served warm.</p></div><div><p>One menu. Your neighbourhood kitchen.</p><small>Fictional restaurant · Test payments only</small><small>Prepared by people. Estimated by software.</small></div></footer>
  </>;
}

function DishCard({ dish, add, saved, toggleSaved }: { dish: Dish; add: (dish: Dish, portion: string, addon: boolean) => void; saved: boolean; toggleSaved: () => void }) {
  const [portion, setPortion] = useState(Object.keys(dish.options)[0]);
  const [addon, setAddon] = useState(false);
  const [added, setAdded] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const optionsRef = useRef<HTMLDetailsElement>(null);
  function customize() {
    setExpanded(true);
    requestAnimationFrame(() => optionsRef.current?.querySelector('select')?.focus());
  }
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(() => () => { if (timer.current) clearTimeout(timer.current); }, []);
  return <article className="dish" onClick={event => { if (!(event.target as HTMLElement).closest('button, a, input, select, label, details')) customize(); }}>
    <div className="dish-photo"><FoodImage name={dish.name} /><button className={saved ? 'favorite saved' : 'favorite'} aria-label={`${saved ? 'Unsave' : 'Save'} ${dish.name}`} aria-pressed={saved} onClick={toggleSaved}><Icon name="heart" size={19} /></button><span className={dish.veg ? 'photo-diet veg' : 'photo-diet'}>{dish.veg ? 'VEG' : 'NON-VEG'}</span></div>
    <div className="dish-main">
      <div className="dish-copy"><div className="dish-meta"><span className={dish.veg ? 'diet veg' : 'diet'}><span />{dish.veg ? 'Vegetarian' : 'Non-vegetarian'}</span><span>{dish.category}</span></div><h3 aria-label={dish.name}><button className="dish-title" aria-label={`Customize ${dish.name}`} aria-expanded={expanded} aria-controls={`dish-options-${dish.id}`} onClick={customize}>{dish.name}</button></h3><p>{dish.description}</p></div>
      <div className="dish-action"><strong>{money(dish.price + (dish.options[portion] || 0) + (addon ? 3000 : 0))}</strong><button className={added ? 'add-button added' : 'add-button'} aria-label={`Add ${dish.name}`} onClick={() => { add(dish, portion, addon); setAdded(true); if (timer.current) clearTimeout(timer.current); timer.current = setTimeout(() => setAdded(false), 1600); }}>{added ? <><Icon name="check" size={16} /> Added</> : <>Add <span aria-hidden="true">+</span></>}</button><span className="sr-only" role="status">{added ? `${dish.name} added to your bag` : ''}</span></div>
    </div>
    <details className="customize" id={`dish-options-${dish.id}`} ref={optionsRef} open={expanded} onToggle={event => setExpanded(event.currentTarget.open)}><summary>Make it yours <span>{portion}{addon ? ' · extra raita' : ''}</span></summary><div className="options"><label>Portion<select aria-label={`Portion for ${dish.name}`} value={portion} onChange={event => setPortion(event.target.value)}>{Object.entries(dish.options).map(([name, price]) => <option value={name} key={name}>{name}{price ? ` +${money(price)}` : ''}</option>)}</select></label><label className="check"><input type="checkbox" checked={addon} onChange={event => setAddon(event.target.checked)} /> Extra raita +₹30</label></div><small>Allergens: {dish.allergens || 'None listed'}</small></details>
  </article>;
}
