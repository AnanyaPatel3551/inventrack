import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

const API = '/api';

const STATUSES = ['IN_STOCK', 'LOW_STOCK', 'OUT_OF_STOCK'];
const STATUS_LABELS = {
  IN_STOCK: 'In stock',
  LOW_STOCK: 'Low stock',
  OUT_OF_STOCK: 'Out of stock',
};
const CATEGORIES = ['Electronics', 'Office Supplies', 'Furniture', 'Grocery', 'Hardware', 'General'];

const USER = { name: 'Ananya Patel', initials: 'AP', role: '24bcs10019' };

const EMPTY_STATS = { total: 0, inStock: 0, lowStock: 0, outOfStock: 0 };

const currency = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' });

function nextStatus(status) {
  const index = STATUSES.indexOf(status);
  return STATUSES[(index + 1) % STATUSES.length];
}

function greeting() {
  const hour = new Date().getHours();
  if (hour < 12) return 'Good morning';
  if (hour < 17) return 'Good afternoon';
  return 'Good evening';
}

async function request(path, options = {}) {
  const response = await fetch(`${API}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = typeof body.detail === 'string' ? body.detail : 'Request failed';
    throw new Error(detail);
  }
  return response.status === 204 ? null : response.json();
}

function App() {
  const [products, setProducts] = useState([]);
  const [stats, setStats] = useState(EMPTY_STATS);
  const [filter, setFilter] = useState('ALL');
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  async function load() {
    try {
      setError('');
      const [productList, statsData] = await Promise.all([
        request('/products'),
        request('/products/stats'),
      ]);
      setProducts(productList);
      setStats(statsData);
    } catch (err) {
      setError('Backend unavailable');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function changeStatus(product) {
    await request(`/products/${product.id}`, {
      method: 'PUT',
      body: JSON.stringify({ status: nextStatus(product.status) }),
    });
    load();
  }

  async function removeProduct(product) {
    if (!window.confirm(`Delete ${product.name}?`)) return;
    await request(`/products/${product.id}`, { method: 'DELETE' });
    load();
  }

  async function addProduct(product) {
    await request('/products', { method: 'POST', body: JSON.stringify(product) });
    setShowForm(false);
    load();
  }

  const visible = filter === 'ALL' ? products : products.filter((p) => p.status === filter);
  const attention = products.filter((p) => p.status !== 'IN_STOCK').slice(0, 5);

  return (
    <div className="app">
      <Sidebar />

      <main className="main">
        <header>
          <div>
            <p className="eyebrow">INVENTORY / OVERVIEW</p>
            <h1>{greeting()}, {USER.name.split(' ')[0]} 👋</h1>
            <p className="muted">Here’s the current state of your stock.</p>
          </div>
          <button className="primary" onClick={() => setShowForm(true)}>＋ Add product</button>
        </header>

        {error && (
          <div className="alert">⚠ {error}. Start the backend and PostgreSQL, then refresh.</div>
        )}

        <section className="stats">
          <Stat label="Total products" value={stats.total} icon="▦" />
          <Stat label="In stock" value={stats.inStock} icon="✓" tone="good" />
          <Stat label="Low stock" value={stats.lowStock} icon="◔" tone="warn" />
          <Stat label="Out of stock" value={stats.outOfStock} icon="✕" tone="bad" />
        </section>

        <section className="content-grid">
          <div className="panel">
            <div className="panel-head">
              <div>
                <h2>Products</h2>
                <p className="muted">All items tracked in the warehouse.</p>
              </div>
              <StatusFilters value={filter} onChange={setFilter} />
            </div>

            {loading ? (
              <div className="empty">Loading products…</div>
            ) : (
              <ProductTable
                products={visible}
                onChangeStatus={changeStatus}
                onDelete={removeProduct}
              />
            )}
          </div>

          <aside className="panel side-panel">
            <div className="panel-head">
              <div>
                <h2>Needs attention</h2>
                <p className="muted">Items that are low or out of stock.</p>
              </div>
            </div>
            {attention.length === 0 && <div className="empty">Everything is stocked up.</div>}
            {attention.map((p) => (
              <div className="alert-row" key={p.id}>
                <span className={`dot ${p.status.toLowerCase()}`}></span>
                <div>
                  <b>{p.name}</b>
                  <small>{p.sku} · {p.quantity} left · {p.supplier || 'No supplier'}</small>
                </div>
              </div>
            ))}
            <div className="pipeline">
              <span>Test</span><i></i>
              <span>Build</span><i></i>
              <span>Scan</span><i></i>
              <span>Deploy</span>
            </div>
          </aside>
        </section>

        {showForm && <ProductModal onClose={() => setShowForm(false)} onSave={addProduct} />}
      </main>
    </div>
  );
}

function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="brand">
        <span className="brand-mark">I</span>
        <div>
          <b>InvenTrack</b>
          <small>Inventory Management</small>
        </div>
      </div>
      <nav>
        <a className="active">▦ <span>Dashboard</span></a>
        <a>▤ <span>Products</span></a>
        <a>⇄ <span>Stock movements</span></a>
        <a>◫ <span>Suppliers</span></a>
      </nav>
      <div className="side-bottom">
        <div className="upgrade">
          <strong>Never run out.</strong>
          <p>Keep an eye on low-stock items and restock before orders slip.</p>
        </div>
        <div className="profile">
          <div className="avatar">{USER.initials}</div>
          <div>
            <b>{USER.name}</b>
            <small>{USER.role}</small>
          </div>
          <span>⋮</span>
        </div>
      </div>
    </aside>
  );
}

function Stat({ label, value, icon, tone = '' }) {
  return (
    <div className="stat">
      <div className={`stat-icon ${tone}`}>{icon}</div>
      <div>
        <small>{label}</small>
        <strong>{value}</strong>
        <span>Updated just now</span>
      </div>
    </div>
  );
}

function StatusFilters({ value, onChange }) {
  return (
    <div className="filters">
      {['ALL', ...STATUSES].map((status) => (
        <button
          key={status}
          className={value === status ? 'selected' : ''}
          onClick={() => onChange(status)}
        >
          {status === 'ALL' ? 'All' : STATUS_LABELS[status]}
        </button>
      ))}
    </div>
  );
}

function ProductTable({ products, onChangeStatus, onDelete }) {
  if (!products.length) {
    return <div className="empty">No products in this filter.</div>;
  }

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Product</th>
            <th>Category</th>
            <th className="num">Qty</th>
            <th className="num">Price</th>
            <th>Supplier</th>
            <th>Status</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {products.map((p) => (
            <tr key={p.id}>
              <td>
                <div className="product-name">
                  <span className={`dot ${p.status.toLowerCase()}`}></span>
                  <div>
                    <b>{p.name}</b>
                    <small>{p.sku}</small>
                  </div>
                </div>
              </td>
              <td>{p.category}</td>
              <td className="num">{p.quantity}</td>
              <td className="num">{currency.format(p.price)}</td>
              <td>{p.supplier || '—'}</td>
              <td>
                <span className={`status ${p.status.toLowerCase()}`}>{STATUS_LABELS[p.status]}</span>
              </td>
              <td className="actions">
                <button
                  className="icon-btn"
                  onClick={() => onChangeStatus(p)}
                  title={`Mark as ${STATUS_LABELS[nextStatus(p.status)]}`}
                >
                  ↻
                </button>
                <button className="icon-btn danger" onClick={() => onDelete(p)} title="Delete product">
                  🗑
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ProductModal({ onClose, onSave }) {
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState('');

  async function handleSubmit(event) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setSaving(true);
    setFormError('');
    try {
      await onSave({
        name: form.get('name'),
        sku: form.get('sku'),
        category: form.get('category'),
        quantity: Number(form.get('quantity')),
        price: Number(form.get('price')),
        supplier: form.get('supplier'),
        status: form.get('status'),
      });
    } catch (err) {
      setFormError(err.message);
      setSaving(false);
    }
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <form className="modal" onSubmit={handleSubmit} onClick={(e) => e.stopPropagation()}>
        <div className="modal-head">
          <div>
            <p className="eyebrow">NEW PRODUCT</p>
            <h2>Add a product</h2>
          </div>
          <button type="button" className="close" onClick={onClose}>×</button>
        </div>

        {formError && <div className="alert">⚠ {formError}</div>}

        <label>
          Product name
          <input name="name" required placeholder="e.g. Wireless Mouse" />
        </label>

        <div className="form-row">
          <label>
            SKU
            <input name="sku" required placeholder="e.g. ELEC-1001" />
          </label>
          <label>
            Category
            <select name="category" defaultValue="General">
              {CATEGORIES.map((c) => <option key={c}>{c}</option>)}
            </select>
          </label>
        </div>

        <div className="form-row">
          <label>
            Quantity
            <input name="quantity" type="number" min="0" step="1" defaultValue="0" required />
          </label>
          <label>
            Price (₹)
            <input name="price" type="number" min="0" step="0.01" defaultValue="0" required />
          </label>
        </div>

        <div className="form-row">
          <label>
            Supplier
            <input name="supplier" placeholder="e.g. Logi Distributors" />
          </label>
          <label>
            Status
            <select name="status" defaultValue="IN_STOCK">
              {STATUSES.map((s) => <option key={s} value={s}>{STATUS_LABELS[s]}</option>)}
            </select>
          </label>
        </div>

        <button className="primary full" disabled={saving}>
          {saving ? 'Saving…' : 'Add product'}
        </button>
      </form>
    </div>
  );
}

createRoot(document.getElementById('root')).render(<App />);
