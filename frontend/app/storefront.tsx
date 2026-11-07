'use client';
import Link from 'next/link';
import { dishPath, slugify, categoryPath } from './menu-links';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import { CustomerProfile, ContactFields } from './customer-profile';
import { EmailVerification } from './email-verification';
import { PasswordRecovery } from './password-recovery';
import { StaffPortal } from './staff-portal';
import { GoogleSignIn } from './google-signin';
import { FormEvent, useCallback, useEffect, useRef, useState } from 'react';
import { api, CartLine, Dish, money, Order, Outlet, User } from './api';
import { Staff } from './staff';
import { Icon } from './ui-icon';
import { FoodImage, foodImage } from './food-image';
import { PrivacySettings } from './privacy-settings';
import { CheckoutReview, Review } from './checkout-review';
import { OrderHistory } from './order-history';
import { LoyaltyPanel, Rewards } from './loyalty-panel';
import { PartyOrders } from './party-orders';
import { DishOptions, defaultSelections, choiceLabels, selectionKey, lineDescription, Selections } from './dish-options';

const areas = [{ name: 'Kondapur', lat: 17.462, lng: 78.357 }, { name: 'Gachibowli', lat: 17.441, lng: 78.349 }, { name: 'Madhapur', lat: 17.448, lng: 78.391 }];
const storageKey = 'dumhouse-cart-v1';
export default function Storefront({ initialDishes }: { initialDishes: Dish[] }) {
  const [user, setUser] = useState<User | null>(null);
  const [authReady,setAuthReady]=useState(false);
  const pathname = usePathname();
  const router = useRouter();
  const view = pathname.startsWith('/orders/') ? 'orders' : pathname.startsWith('/menu/') ? 'dish' : pathname === '/' || pathname === '/menu' ? 'menu' : pathname.slice(1);
  const dishSlug = view === 'dish' ? pathname.split('/')[2] : null;
  const searchParams = useSearchParams();
  const categorySlug = searchParams.get('category') || '';
  const [pageSize, setPageSize] = useState(12);
  function setCategory(next: string) { router.push(categoryPath(next).replace('/menu', view === 'saved' ? '/saved' : '/menu'), { scroll: false }); }
  function setView(next: string) { router.push(next === 'menu' ? '/menu' : `/${next}`); }
  const [location, setLocation] = useState(areas[0]);
  const [outlets, setOutlets] = useState<Outlet[]>([]);
  const [outlet, setOutlet] = useState(0);
  const [dishes, setDishes] = useState<Dish[]>(initialDishes);
  const [cart, setCart] = useState<CartLine[]>([]);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [rewards,setRewards]=useState<Rewards|null>(null);
  const [redeemPoints,setRedeemPoints]=useState(0);
  useEffect(()=>{setRedeemPoints(0);if(user?.role==='customer')api<Rewards>('/account/loyalty').then(setRewards).catch(()=>setRewards(null));else setRewards(null);},[user?.id,pathname]);
  const [review, setReview] = useState<Review | null>(null);
  useEffect(() => { if (review) window.scrollTo({ top: 0 }); }, [review]);
  const reviewedBody = useRef<string>('');
  useEffect(() => { setReview(null); }, [pathname]);
  const [orders, setOrders] = useState<Order[]>([]);
  const category = dishes.find(dish => slugify(dish.category) === categorySlug)?.category || (categorySlug ? 'Unknown category' : 'All');
  const [search, setSearch] = useState('');
  const [vegetarian, setVegetarian] = useState(false);
  const [menuLoading, setMenuLoading] = useState(true);
  const [bagRequested, setBagRequested] = useState(false);
  const [address, setAddress] = useState('');
  const [routing, setRouting] = useState<'auto'|'selected'>('auto');
  const [updateChannel, setUpdateChannel] = useState('in_app');
  const [updatePhone, setUpdatePhone] = useState('');
  const [updateConsent, setUpdateConsent] = useState(false);
  const [recommendations, setRecommendations] = useState<Dish[]>([]);
  useEffect(() => {
    if (!user || user.role !== 'customer' || !outlet) {setRecommendations([]);return;}
    let active=true; api<Dish[]>(`/recommendations?outlet_id=${outlet}`).then(items=>active && setRecommendations(items)).catch(()=>setRecommendations([]));
    return ()=>{active=false;};
  },[user,outlet]);
  const [method, setMethod] = useState('upi');
  const [register, setRegister] = useState(false);
  const [saved, setSaved] = useState<number[]>([]);
  const [searchRequested, setSearchRequested] = useState(false);
  const checkoutKey = useRef('');
  const checkoutAfterLogin = useRef(false);
  const expiry = useRef(0);
  const restoredOutlet = useRef(0);

  useEffect(() => {
    api<User>('/auth/me').then(setUser).catch(() => {}).finally(()=>setAuthReady(true));
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
    const reloadStock = () => { if (outlet && document.visibilityState === 'visible') api<Dish[]>(`/outlets/${outlet}/menu`).then(items=>{if(active)setDishes(items);}).catch(()=>{}); };
    const timer = setInterval(reloadStock, 15000); document.addEventListener('visibilitychange',reloadStock);
    return () => { active = false; clearInterval(timer); document.removeEventListener('visibilitychange',reloadStock); };
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
  function add(dish: Dish, portion: string, addon: boolean, quantity = 1, selections: Selections = defaultSelections(dish)): boolean {
    const existing = cart.find(line => line.dish_id === dish.id && line.portion === portion && line.addon === addon && selectionKey(line.selections || defaultSelections(dish)) === selectionKey(selections))?.quantity || 0;
    if (existing + quantity > 20) { setError(`You can order up to 20 of the same customization. Your bag already has ${existing}; reduce the quantity before adding.`); return false; }
    setError('');
    expiry.current = Date.now() + 3600000;
    setCart(previous => {
      const index = previous.findIndex(line => line.dish_id === dish.id && line.portion === portion && line.addon === addon && selectionKey(line.selections || defaultSelections(dish)) === selectionKey(selections));
      if (index >= 0) return previous.map((line, position) => position === index ? { ...line, quantity: line.quantity + quantity } : line);
      return [...previous, { dish_id: dish.id, name: dish.name, quantity, portion, addon, selections, customization_labels: choiceLabels(dish, selections), price: dish.price + dish.options[portion] + (addon ? 3000 : 0) }];
    });
    return true;
  }
  function editLine(index: number, portion: string, addon: boolean, selections: Selections) {
    const line = cart[index];
    const dish = dishes.find(item => item.id === line.dish_id);
    if (!dish || !(portion in dish.options)) { setError('This item is no longer available. Remove it and choose another dish.'); return; }
    const match = cart.findIndex((item, position) => position !== index && item.dish_id === line.dish_id && item.portion === portion && item.addon === addon && selectionKey(item.selections || defaultSelections(dish)) === selectionKey(selections));
    if (match >= 0 && cart[match].quantity + line.quantity > 20) { setError('You can order up to 20 of the same customization. Reduce the quantity first.'); return; }
    const updated = { ...line, portion, addon, selections, customization_labels: choiceLabels(dish, selections), price: dish.price + dish.options[portion] + (addon ? 3000 : 0) };
    expiry.current = Date.now() + 3600000;
    setCart(cart.flatMap((item, position) => {
      if (position === index) return match >= 0 ? [] : [updated];
      return [position === match ? { ...updated, quantity: item.quantity + line.quantity } : item];
    }));
  }
  async function checkout(confirm = false) {
    if (!user) { checkoutAfterLogin.current = true; setView('signin'); return; }
    if (!user.profile_complete) { setView('account'); throw new Error('Add your name and contact phone number before checkout.'); }
    if (expiry.current <= Date.now()) { setCart([]); throw new Error('Your cart expired. Please add your dishes again.'); }
    if (!checkoutKey.current) checkoutKey.current = crypto.randomUUID();
    const body = { outlet_id: outlet, redeem_points:redeemPoints, routing, updates:{channel:updateChannel, phone:updatePhone, consent:updateConsent}, lat: location.lat, lng: location.lng, address, method, key: checkoutKey.current, lines: cart.map(({ dish_id, quantity, portion, addon, selections }) => ({ dish_id, quantity, portion, addon, selections: selections || {} })) };
    const quoted = await api<Review>('/checkout/quote', 'POST', body);
    const fingerprint = JSON.stringify({body, quoted});
    if (!confirm || fingerprint !== reviewedBody.current) {
      reviewedBody.current = fingerprint; setReview(quoted);
      if (confirm) throw new Error('Your order details or prices changed. Review the updated total and confirm again.');
      return;
    }
    const order = await api<Order>('/orders', 'POST', {...body, expected_total: quoted.total, expected_outlet: quoted.outlet_id});
    setCart([]); setReview(null); setRedeemPoints(0); await refreshOrders(); router.push(`/orders/${order.id}${order.status === 'PENDING_PAYMENT' ? '' : '?confirmed=1'}`);
  }
  async function signin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    await action(async () => {
      const account = await api<User>(register ? '/auth/register' : '/auth/login', 'POST', { email: form.get('email'), password: form.get('password'), ...(register ? {name:form.get('name'),phone:form.get('phone')} : {}) });
      setUser(account); if (view !== 'orders' || account.role !== 'customer') setView(account.role!=='customer'?'staff':checkoutAfterLogin.current?'bag':'menu');
      checkoutAfterLogin.current = false;
    });
  }
  const count = cart.reduce((total, line) => total + line.quantity, 0);
  const cartTotal = cart.reduce((total, line) => total + line.quantity * line.price, 0);
  const selectedOutlet = outlets.find(item => item.id === outlet);
  const visibleDishes = dishes.filter(dish => (view !== 'saved' || saved.includes(dish.id)) && (category === 'All' || dish.category === category) && (!vegetarian || dish.veg) && `${dish.name} ${dish.description}`.toLowerCase().includes(search.toLowerCase()));
  const selectedDish = dishes.find(dish => slugify(dish.name) === dishSlug);
  useEffect(() => { setPageSize(12); }, [categorySlug, search, vegetarian, view, outlet]);
  if(view==='forgot-password'||view==='reset-password') return <main><PasswordRecovery reset={view==='reset-password'}/></main>;
  if(pathname==='/staff'||pathname.startsWith('/staff/')||(user&&user.role!=='customer')) return <StaffPortal user={user} ready={authReady} onUser={setUser}/>;
  const categories = ['All', ...Array.from(new Set(dishes.map(dish => dish.category)))];
  return <>
    <a className="skip-link" href="#main">Skip to content</a><header><a className="brand" href="/" aria-label="Dum & Dastaan home"><span className="brand-symbol"><Icon name="food" size={22} /></span><span className="brand-text">Dum & Dastaan<small>HYDERABAD KITCHENS</small></span></a><nav aria-label="Main navigation">
      <Link className={`nav-link ${view === 'menu' || view === 'dish' ? 'selected' : ''}`} href='/menu'>Menu</Link><Link className={`nav-link ${view === 'party' ? 'selected' : ''}`} href="/party">Party orders</Link><Link className={`nav-link ${view === 'saved' ? 'selected' : ''}`} href='/saved' onClick={() => { setSearch(''); setCategory('All'); setVegetarian(false); }}>Saved</Link>
      {user?.role === 'customer' && <Link className={`nav-link ${view === 'orders' ? 'selected' : ''}`} href='/orders'>Your orders</Link>}
      {user ? <button className="quiet" disabled={busy} onClick={() => action(async () => { await api('/auth/logout', 'POST'); setUser(null); setOrders([]); setView('menu'); })}>Sign out</button> : <Link className='nav-link' href='/signin'>Sign in</Link>}
      {(!user || user.role === 'customer') && <button className="header-bag" onClick={openBag} aria-label={`Your bag · ${count}`}><Icon name="bag" /><span>Your bag</span><span className="bag-count">{count}</span></button>}
    </nav></header>
    <div className="demo"><span>Hyderabad flavours. Stories worth sharing.</span><span>Demo kitchens · Test payments only</span></div>
    {error && <div className="error" role="alert">{error}<button className="quiet" onClick={() => setError('')} aria-label="Dismiss error">Dismiss</button></div>}
    <main id="main" className={`${view}-view`}>
      {view === 'party' && (!user || user.role==='customer') ? <PartyOrders user={user}/> : view === 'verify-email' ? <EmailVerification /> : view === 'signin' || (view === 'account' && !user) || (view === 'orders' && !user) ? <section className="auth"><h1>{register ? 'A seat at our table.' : 'Welcome back.'}</h1><p>Sign in to order, or use your assigned staff account.</p><GoogleSignIn onSignedIn={account => { setUser(account); if (view !== 'orders') setView(checkoutAfterLogin.current ? 'bag' : 'menu'); checkoutAfterLogin.current = false; }} /><form onSubmit={signin}>{register && <ContactFields />}<label>Email<input name="email" type="email" autoComplete="email" required /></label><label>Password<input name="password" type="password" minLength={10} maxLength={128} autoComplete={register ? 'new-password' : 'current-password'} required /></label><button disabled={busy}>{busy ? 'Please wait…' : register ? 'Create account' : 'Sign in'}</button></form>{!register&&<p><Link href="/forgot-password">Forgot password?</Link></p>}<button className="quiet" onClick={() => setRegister(!register)}>{register ? 'Already registered? Sign in' : 'New here? Create an account'}</button></section> : user && user.role !== 'customer' ? <Staff user={user} /> : user?.role === 'customer' && !user.profile_complete ? <section className="auth"><CustomerProfile user={user} onChange={setUser} required /></section> : view === 'account' && user ? <section className="account-page"><div className="profile-avatar"><Icon name="user" size={34} /></div><h1>Your account</h1><p>{user.email}</p><div className="account-actions"><button className="secondary" onClick={() => setView('orders')}><Icon name="receipt" />Your orders<Icon name="arrow" /></button><button className="secondary" onClick={openSaved}><Icon name="heart" />Saved dishes<Icon name="arrow" /></button><button className="secondary" onClick={openBag}><Icon name="bag" />Your bag<Icon name="arrow" /></button></div><CustomerProfile user={user} onChange={setUser} /><PrivacySettings user={user} onChange={setUser} /><LoyaltyPanel/><Link className="button-link secondary" href="/party">Plan a party order</Link><p className="muted">{user.cod ? 'Demo COD available on this account.' : 'This account uses prepaid test payments.'}</p><button className="quiet" disabled={busy} onClick={() => action(async () => { await api('/auth/logout', 'POST'); setUser(null); setOrders([]); setView('menu'); })}>Sign out</button></section> : view === 'orders' ? <OrderHistory focusedId={pathname.startsWith('/orders/') ? Number(pathname.split('/')[2]) : undefined} confirmed={searchParams.get('confirmed') === '1'} orders={orders} busy={busy} pay={(order, success) => action(async () => { await api(`/payments/mock/${order.id}/complete`, 'POST', { event: crypto.randomUUID(), success }); if (!success) setError('Test payment failed. Your order remains unpaid; you can retry.'); await refreshOrders(); if (success) router.push(`/orders/${order.id}?confirmed=1`); })} /> : review ? <CheckoutReview quote={review} address={address} method={method} busy={busy} back={() => setReview(null)} confirm={() => action(() => checkout(true))} /> : <>
        <section className="location" aria-label="Delivery and outlet selection">
          <div className="delivery-control"><Icon name="pin" /><label>Delivering to<select value={areas.findIndex(area => area.name === location.name)} onChange={event => changeLocation(areas[Number(event.target.value)])}>{!areas.some(area => area.name === location.name) && <option value={-1}>Current location</option>}{areas.map((area, index) => <option value={index} key={area.name}>{area.name} · sample area</option>)}</select></label></div>
          <div className="kitchen-control"><label>Your kitchen<select aria-label="Your kitchen" value={outlet} disabled={!outlets.length} onChange={event => {setRouting('selected');changeOutlet(Number(event.target.value));}}>{!outlets.length && <option value={0}>No eligible kitchen</option>}{outlets.map((item, index) => <option value={item.id} key={item.id}>{item.name} · {item.distance} km{index === 0 ? ' · Nearest' : ''} · FSSAI: {item.fssai || 'pending'}</option>)}</select></label></div>
          <div className="prep-note"><Icon name="clock" /><span>{selectedOutlet ? `From ${selectedOutlet.minimum} min` : 'Choose your location'}<small>Preparation estimate</small></span></div>
          <button className="quiet locate" onClick={() => { if (!navigator.geolocation) { setError('Location is unavailable. Choose a sample area.'); return; } navigator.geolocation.getCurrentPosition(position => changeLocation({ name: 'Current location', lat: position.coords.latitude, lng: position.coords.longitude }), () => setError('Location permission unavailable. Choose a sample area.'), { timeout: 10000 }); }}>Use my location <Icon name="pin" size={16} /></button>
          {ready && !outlets.length && <p className="location-empty">No kitchens deliver here. Select a sample area to explore the menu.</p>}
        </section>
        {view === 'menu' && recommendations.length > 0 && <section className="reorder-suggestions"><h2>Order again</h2><p>Suggested from your order history. Choose a dish to review it; nothing is added automatically.</p><div className="review-actions">{recommendations.filter(suggestion=>dishes.some(dish=>dish.id===suggestion.id)).map(dish=><Link key={dish.id} href={dishPath(dish)}>{dish.name}</Link>)}</div></section>}
        {view === 'menu' && <>
        <section className="hero">
          <div className="hero-copy"><h1>Hyderabad, served warm.</h1><p>Slow-cooked biryani, bold sides and a sweet finish.</p><a className="button-link" href="#menu">Find your favourite <Icon name="arrow" size={17} /></a></div>
          <figure className="hero-image"><img src="/images/dishes/nizam-chicken-biryani.webp" alt="Chicken biryani served in a bowl" width="1536" height="1024" fetchPriority="high" /><figcaption>Representative food photo · <a href="/photo-credits.html">Photo credit</a></figcaption></figure>
        </section></>}
        {view === 'saved' && <div className="page-title"><h1>Saved for your next craving</h1><p>Your favourites, ready when you are. Saved on this browser.</p></div>}
        {view === 'bag' && <div className="page-title"><button className="quiet back-menu" onClick={() => setView('menu')}>Back to menu</button><h1>Your order</h1><p>From {selectedOutlet?.name || 'your selected'} kitchen, with love.</p></div>}
        {view === 'dish' && <><nav className="breadcrumbs" aria-label="Breadcrumb"><Link href="/menu">Menu</Link><span aria-hidden="true">/</span>{selectedDish && <><Link href={categoryPath(selectedDish.category)}>{selectedDish.category}</Link><span aria-hidden="true">/</span></>}<span>{selectedDish?.name || 'Dish'}</span></nav>{menuLoading ? <p role="status">Loading your dish…</p> : selectedDish ? <DishDetail key={`${outlet}-${selectedDish.id}`} dish={selectedDish} add={add} openBag={openBag} /> : <section className="empty-state"><h1>Unavailable at this kitchen</h1><p>Choose another kitchen above or explore the current menu.</p><Link className="button-link" href="/menu">Browse menu</Link></section>}</>}
        <div className="shop" id="menu"><section className="menu-column" aria-label="Food menu">
          <p className="licence-note">{selectedOutlet?.name} kitchen · FSSAI licence: {selectedOutlet?.fssai || 'Pending verification'}</p><div className="menu-heading"><div><h2>{view === 'saved' ? 'Your saved dishes' : 'The Dum & Dastaan menu'}</h2><p>{view === 'saved' ? 'Tap the heart to keep a favourite.' : 'Biryani, sides & a little something sweet.'}</p></div><span className="tax-note">Prices include 5% GST</span></div>
          <div className="menu-tools"><label className="search-control"><Icon name="search" size={18} /><input id="menu-search" aria-label="Search the menu" type="search" placeholder="Search biryani, sides, sweets…" value={search} onChange={event => setSearch(event.target.value)} /></label><button className={vegetarian ? 'veg-filter active' : 'veg-filter'} aria-pressed={vegetarian} onClick={() => setVegetarian(!vegetarian)}><Icon name="leaf" size={17} /> Vegetarian</button></div>
          <div className="category-navigation"><label>Browse categories<select aria-label="Browse categories" value={category} onChange={event => setCategory(event.target.value)}>{categories.map(item => <option key={item} value={item}>{item === 'All' ? 'Full menu' : item} ({item === 'All' ? dishes.length : dishes.filter(dish => dish.category === item).length})</option>)}</select></label><p role="status">{visibleDishes.length} {visibleDishes.length === 1 ? 'dish' : 'dishes'}{category !== 'All' ? ` in ${category}` : ' to explore'}</p></div>
          <div className="menu" aria-busy={menuLoading}>{visibleDishes.slice(0, pageSize).map(dish => <DishCard key={dish.id} dish={dish} add={add} saved={saved.includes(dish.id)} toggleSaved={() => toggleSaved(dish.id)} />)}{menuLoading ? <p className="empty" role="status">Your kitchen is setting the menu…</p> : !visibleDishes.length && <div className="empty"><h3>{view === 'saved' ? 'Make room for your favourites.' : dishes.length ? 'Nothing on this page, yet.' : 'The menu is taking a break.'}</h3><p>{view === 'saved' ? 'Tap a heart on the menu to save a dish here.' : dishes.length ? 'Try another search or explore the full menu.' : 'Choose another eligible kitchen, or check back shortly.'}</p>{dishes.length > 0 && <button className="secondary" onClick={() => { setSearch(''); setVegetarian(false); setCategory('All'); setView('menu'); }}>Show full menu</button>}</div>}</div>
          {visibleDishes.length > pageSize && <div className="menu-pagination"><p>Showing {pageSize} of {visibleDishes.length} dishes</p><button className="secondary" onClick={() => setPageSize(size => size + 12)}>Show more dishes</button></div>}
          <p className="menu-footnote">Photos are illustrative. Portions, prices and availability come from your selected kitchen.</p>
        </section>
        <aside id="cart" tabIndex={-1} aria-label="Your bag"><div className="bag-heading"><h2>Your bag</h2><span className="bag-count">{count}</span></div><p className="bag-kitchen"><Icon name="pin" size={14} />{selectedOutlet?.name || 'Choose a kitchen'} kitchen</p><p className="licence-note">FSSAI: {selectedOutlet?.fssai || 'Licence details pending verification'}</p>{!cart.length ? <div className="empty-bag"><Icon name="bag" size={40} /><h3>A good meal starts here.</h3><p>Add something you love.<br />We’ll take it from there.</p><Link href="/menu">Discover the menu <Icon name="arrow" size={16} /></Link></div> : <>{cart.map((line, index) => <div className="cart-line" key={`${line.dish_id}-${index}`}><FoodImage className="cart-thumbnail" name={line.name} /><strong>{line.name}</strong><small>{lineDescription(line)}</small>{dishes.find(dish => dish.id === line.dish_id) && <details className="bag-customize"><summary>Edit item</summary><DishOptions compact dish={dishes.find(dish => dish.id === line.dish_id)!} portion={line.portion} addon={line.addon} selections={line.selections || defaultSelections(dishes.find(dish => dish.id === line.dish_id)!)} onChange={(portion, addon, selections) => editLine(index, portion, addon, selections)} /><small>Changes save automatically.</small></details>}<div className="row"><label>Qty<input aria-label={`Quantity ${line.name}`} type="number" min="1" max="20" value={line.quantity} onChange={event => { expiry.current = Date.now() + 3600000; setCart(cart.map((item, position) => position === index ? { ...item, quantity: Math.max(1, Math.min(20, Number(event.target.value))) } : item)); }} /></label><span>{money(line.price * line.quantity)}</span><button className="quiet" aria-label={`Remove ${line.name}`} onClick={() => setCart(cart.filter((_, position) => position !== index))}>Remove</button></div></div>)}<div className="row total"><strong>Estimated total</strong><strong>{money(cartTotal)}</strong></div><form onSubmit={event => { event.preventDefault(); action(() => checkout()); }}><label>Delivery address<textarea required minLength={5} maxLength={500} placeholder="Flat, building and landmark in your selected area" value={address} onChange={event => { setAddress(event.target.value); checkoutKey.current = ''; }} /></label><label>Kitchen routing<select value={routing} onChange={event=>setRouting(event.target.value as 'auto'|'selected')}><option value="auto">Automatically choose nearest kitchen with all items</option><option value="selected">Use my selected kitchen</option></select></label><label>Order updates<select value={updateChannel} onChange={event=>{setUpdateChannel(event.target.value);setUpdateConsent(false);}}><option value="in_app">In the app</option><option value="sms">SMS (provider setup pending)</option><option value="whatsapp">WhatsApp (provider setup pending)</option></select></label>{updateChannel !== 'in_app' && <><label>Phone number with country code<input type="tel" autoComplete="tel" value={updatePhone} onChange={event=>setUpdatePhone(event.target.value)} placeholder="+919876543210" pattern="\+[1-9][0-9]{7,14}" required /></label><label className="check"><input type="checkbox" required checked={updateConsent} onChange={event=>setUpdateConsent(event.target.checked)} />Send order-service updates to this number. This does not opt me into marketing.</label><small>Messaging is not connected yet. Updates remain available in Your orders.</small></>}{user && rewards && <fieldset className="checkout-rewards"><legend>Use loyalty points</legend><p>{rewards.balance} points available · 1 point = ₹1</p><label>Points to redeem<input type="number" min={0} max={Math.min(rewards.balance,Math.floor(cartTotal/100))} step={1} value={redeemPoints} onChange={e=>{setRedeemPoints(Math.max(0,Math.floor(Number(e.target.value))));checkoutKey.current='';}}/></label><small>Points are reserved when you place the order. Cancel an unpaid order to return them.</small>{redeemPoints>0&&<p>Estimated payable: {money(Math.max(0,cartTotal-redeemPoints*100))}</p>}</fieldset>}<label>Payment<select value={method} onChange={event => { setMethod(event.target.value); checkoutKey.current = ''; }}><option value="upi">Test UPI</option><option value="card">Test card</option>{user?.cod && <option value="cod">Demo COD</option>}</select></label>{method === 'cod' && <small>Demo policy: orders above ₹1,500 need a 20% test deposit.</small>}<button disabled={busy || !outlet} type="submit">{busy ? 'Checking your order…' : user ? 'Continue to payment' : 'Sign in to checkout'}</button><small>Prices and availability are checked at checkout. Cart retained for 60 minutes.</small></form></>}</aside></div>
      </>}
    </main>
    {(view === 'menu' || view === 'saved' || view === 'dish') && (!user || user.role === 'customer') && count > 0 && <button className="mobile-bag" onClick={openBag}><span><Icon name="bag" /><strong>{count} {count === 1 ? 'item' : 'items'}</strong><span>{money(cartTotal)}</span></span><span>View bag <Icon name="arrow" size={18} /></span></button>}
    {(!user || user.role === 'customer') && <nav className="bottom-nav" aria-label="App navigation">
      <Link href="/menu" className={view === 'menu' && !searchRequested ? 'active' : ''}><Icon name="home" /><span>Home</span></Link>
      <button onClick={() => { setView('menu'); setSearchRequested(true); }}><Icon name="search" /><span>Search</span></button>
      <Link href="/orders" className={view === 'orders' ? 'active' : ''}><Icon name="receipt" /><span>Orders</span></Link>
      <Link href="/saved" className={view === 'saved' ? 'active' : ''}><Icon name="heart" /><span>Saved</span></Link>
      <Link href="/account" className={view === 'account' ? 'active' : ''}><Icon name="user" /><span>Account</span></Link>
    </nav>}
    <footer><div><a className="footer-brand" href="/">Dum &amp; Dastaan</a><p>Hyderabad, served warm.</p></div><div><nav aria-label="Footer navigation"><Link href="/menu">Menu</Link><Link href="/orders">Orders</Link><Link href="/account">Account</Link><Link href="/party">Party orders</Link><a href="/privacy.html">Privacy</a><a href="/photo-credits.html">Photo credits</a></nav><p>© 2026 Dum & Dastaan. All rights reserved.</p></div></footer>
  </>;
}

function DishCard({ dish, add, saved, toggleSaved }: { dish: Dish; add: (dish: Dish, portion: string, addon: boolean, quantity?: number, selections?: Selections) => boolean; saved: boolean; toggleSaved: () => void }) {
  const [portion, setPortion] = useState(Object.keys(dish.options)[0]);
  const [addon, setAddon] = useState(false);
  const [selections, setSelections] = useState<Selections>(() => defaultSelections(dish));
  const [added, setAdded] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const optionsRef = useRef<HTMLDetailsElement>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(() => () => { if (timer.current) clearTimeout(timer.current); }, []);
  const router = useRouter();
  return <article className="dish" onClick={event => { if (!(event.target as HTMLElement).closest('button, a, input, select, label, details')) router.push(dishPath(dish)); }}>
    <div className="dish-photo"><Link href={dishPath(dish)} aria-label={`View ${dish.name}`}><FoodImage name={dish.name} photoUrl={dish.photo_url} /></Link><button className={saved ? 'favorite saved' : 'favorite'} aria-label={`${saved ? 'Unsave' : 'Save'} ${dish.name}`} aria-pressed={saved} onClick={toggleSaved}><Icon name="heart" size={19} /></button><span className={dish.veg ? 'photo-diet veg' : 'photo-diet'}><span className={dish.veg ? 'food-symbol veg-symbol' : 'food-symbol nonveg-symbol'} aria-hidden="true" />{dish.veg ? 'VEG' : 'NON-VEG'}</span></div>
    <div className="dish-main">
      <div className="dish-copy"><div className="dish-meta"><span className={dish.veg ? 'diet veg' : 'diet'}><span />{dish.veg ? 'Vegetarian' : 'Non-vegetarian'}</span><span>{dish.category}{dish.spice_level && dish.spice_level !== 'not_set' ? ` · ${dish.spice_level.replace('_',' ')} spice` : ''}</span></div><h3 aria-label={dish.name}><Link className="dish-title" href={dishPath(dish)}>{dish.name}</Link></h3>{!dish.description.includes("from our ") && <p>{dish.description}</p>}<small className="allergen-note">Allergens: {dish.allergens || 'Not verified — ask the kitchen'}</small></div>
      <div className="dish-action"><strong>{money(dish.price + (dish.options[portion] || 0) + (addon ? 3000 : 0))}</strong><button className={added ? 'add-button added' : 'add-button'} aria-label={`Add ${dish.name}`} onClick={() => { setAdded(add(dish, portion, addon, 1, selections)); if (timer.current) clearTimeout(timer.current); timer.current = setTimeout(() => setAdded(false), 1600); }}>{added ? <><Icon name="check" size={16} /> Added</> : <>Add <span aria-hidden="true">+</span></>}</button><span className="sr-only" role="status">{added ? `${dish.name} added to your bag` : ''}</span></div>
    </div>
    <details className="customize" id={`dish-options-${dish.id}`} ref={optionsRef} open={expanded} onToggle={event => setExpanded(event.currentTarget.open)}><summary>Customize <span>{dish.customizations?.map(group => group.label).join(' · ') || 'Portion & extras'}</span></summary><DishOptions compact dish={dish} portion={portion} addon={addon} selections={selections} onChange={(portion, addon, selections) => { setPortion(portion); setAddon(addon); setSelections(selections); setAdded(false); }} /><small>Allergens: {dish.allergens || 'Not verified — ask the kitchen before ordering'}</small></details>
  </article>;
}

function DishDetail({ dish, add, openBag }: { dish: Dish; add: (dish: Dish, portion: string, addon: boolean, quantity?: number, selections?: Selections) => boolean; openBag: () => void }) {
  const [portion, setPortion] = useState(Object.keys(dish.options)[0]);
  const [addon, setAddon] = useState(false);
  const [selections, setSelections] = useState<Selections>(() => defaultSelections(dish));
  const [quantity, setQuantity] = useState(1);
  const [added, setAdded] = useState(false);
  const price = dish.price + (dish.options[portion] || 0) + (addon ? 3000 : 0);
  return <section className="dish-detail">
    <div className="detail-image"><FoodImage name={dish.name} photoUrl={dish.photo_url} />{(dish.photo_url || foodImage(dish.name)) && <small>{dish.photo_url ? dish.photo_credit || "Restaurant menu photo" : <>Representative food photo · presentation may vary · <a href="/photo-credits.html">Photo credit</a></>}</small>}</div>
    <div className="detail-copy"><h1>{dish.name}</h1><p className="detail-category"><span className={dish.veg ? 'food-symbol veg-symbol' : 'food-symbol nonveg-symbol'} aria-hidden="true" /> {dish.category} · {dish.veg ? 'Vegetarian' : 'Non-vegetarian'}{dish.spice_level && dish.spice_level !== 'not_set' ? ` · ${dish.spice_level.replace('_',' ')} spice` : ''}</p><p>{dish.description}</p><p className="detail-price">{money(price)} <small>per portion · includes 5% GST</small></p>
      <DishOptions dish={dish} portion={portion} addon={addon} selections={selections} onChange={(portion, addon, selections) => { setPortion(portion); setAddon(addon); setSelections(selections); setAdded(false); }} />
      <p className="allergen-note">Allergens: {dish.allergens || 'Not verified — ask the kitchen before ordering'}.</p>
      <div className="detail-order"><label>Quantity<input aria-label="Dish quantity" type="number" min="1" max="20" value={quantity} onChange={event => { setQuantity(Math.max(1, Math.min(20, Number(event.target.value)))); setAdded(false); }} /></label><button onClick={() => { setAdded(add(dish, portion, addon, quantity, selections)); }}>{added ? 'Added to bag' : `Add to bag · ${money(price * quantity)}`}</button></div>
      <p role="status" className="detail-feedback">{added ? `${quantity} × ${dish.name} added.` : 'Choose your options, then add to your bag.'}</p>{added && <button className="secondary" onClick={openBag}>View your bag <Icon name="arrow" /></button>}
    </div>
  </section>;
}
