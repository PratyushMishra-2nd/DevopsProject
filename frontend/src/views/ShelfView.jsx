import { useMemo, useState } from 'react'
import Icon from '../components/Icon.jsx'
import {
  CATEGORIES,
  STORAGE,
  formatQty,
  freshnessLabel,
  fuseFill,
  isOnShelf,
  labelFor,
  shortDate,
} from '../lib/format.js'

function KpiStrip({ summary }) {
  if (!summary) return null
  const stubs = [
    { label: 'Lots on the shelf', value: summary.active_lots, tone: 'forest' },
    { label: `Expiring in ${summary.warning_days} days`, value: summary.expiring_soon, tone: 'saffron' },
    { label: 'Expired, still shelved', value: summary.expired_on_shelf, tone: 'tomato' },
    { label: 'Dispatched this week', value: formatQty(summary.dispatched_this_week), tone: 'ink' },
    { label: 'Partners served', value: summary.partners_served, tone: 'ink' },
  ]
  return (
    <section className="stubs" aria-label="Pantry at a glance">
      {stubs.map((s) => (
        <div key={s.label} className={`stub stub--${s.tone}`}>
          <span className="stub__value">{s.value}</span>
          <span className="stub__label">{s.label}</span>
        </div>
      ))}
    </section>
  )
}

export function LotCard({ lot, onDispatch, onEdit, onDelete }) {
  const canDispatch = lot.status === 'available' && lot.days_left >= 0 && lot.quantity > 0
  return (
    <article className={`lot lot--${lot.freshness} ${isOnShelf(lot) ? '' : 'lot--archived'}`}>
      <header className="lot__tags">
        <span className={`tag tag--${lot.category}`}>
          <Icon name={lot.category} size={15} />
          {labelFor(CATEGORIES, lot.category)}
        </span>
        <span className="zone" title={`${labelFor(STORAGE, lot.storage)} storage`}>
          <Icon name={lot.storage} size={15} />
          {labelFor(STORAGE, lot.storage)}
        </span>
      </header>
      <h3 className="lot__name">{lot.item_name}</h3>
      <p className="lot__qty">
        <span className="num">{formatQty(lot.quantity)}</span> {lot.unit}
        {lot.status !== 'available' && (
          <span className={`status status--${lot.status}`}>{lot.status.replace('_', ' ')}</span>
        )}
      </p>
      <div className="fuse" aria-label={freshnessLabel(lot.days_left)}>
        <div className="fuse__track">
          <div className="fuse__fill" style={{ width: `${fuseFill(lot.days_left) * 100}%` }} />
        </div>
        <span className="fuse__label">
          {freshnessLabel(lot.days_left)} · best before {shortDate(lot.expires_on)}
        </span>
      </div>
      <p className="lot__meta">
        {lot.donor_name ? `From ${lot.donor_name}` : 'Anonymous donation'} · received{' '}
        {shortDate(lot.received_on)}
      </p>
      {lot.notes && <p className="lot__notes">“{lot.notes}”</p>}
      <footer className="lot__actions">
        <button className="btn btn--primary btn--sm" onClick={() => onDispatch(lot)} disabled={!canDispatch}>
          <Icon name="truck" size={16} /> Dispatch
        </button>
        <button className="icon-btn" onClick={() => onEdit(lot)} aria-label={`Edit ${lot.item_name}`}>
          <Icon name="edit" size={18} />
        </button>
        <button
          className="icon-btn icon-btn--danger"
          onClick={() => onDelete(lot)}
          aria-label={`Delete ${lot.item_name}`}
        >
          <Icon name="trash" size={18} />
        </button>
      </footer>
    </article>
  )
}

const VIEWS = [
  { id: 'shelf', label: 'On shelf' },
  { id: 'all', label: 'All lots' },
  { id: 'archived', label: 'Depleted & discarded' },
]

export default function ShelfView({ lots, summary, onDispatch, onEdit, onDelete, onReceive }) {
  const [category, setCategory] = useState('')
  const [view, setView] = useState('shelf')
  const [q, setQ] = useState('')

  const visible = useMemo(() => {
    const needle = q.trim().toLowerCase()
    return lots.filter(
      (l) =>
        (!category || l.category === category) &&
        (view === 'all' || (view === 'shelf' ? isOnShelf(l) : !isOnShelf(l))) &&
        (!needle || l.item_name.toLowerCase().includes(needle)),
    )
  }, [lots, category, view, q])

  return (
    <>
      <KpiStrip summary={summary} />
      <section className="toolbar" aria-label="Filter stock">
        <div className="chips" role="group" aria-label="Category">
          <button className={`chip ${category === '' ? 'chip--on' : ''}`} onClick={() => setCategory('')}>
            Everything
          </button>
          {CATEGORIES.map((c) => (
            <button
              key={c.id}
              className={`chip ${category === c.id ? 'chip--on' : ''}`}
              onClick={() => setCategory(category === c.id ? '' : c.id)}
            >
              <Icon name={c.id} size={15} /> {c.label}
            </button>
          ))}
        </div>
        <div className="toolbar__right">
          <label className="search">
            <Icon name="search" size={17} />
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Search items"
              aria-label="Search items"
            />
          </label>
          <select value={view} onChange={(e) => setView(e.target.value)} aria-label="Lot status view">
            {VIEWS.map((v) => (
              <option key={v.id} value={v.id}>
                {v.label}
              </option>
            ))}
          </select>
        </div>
      </section>

      {visible.length === 0 ? (
        <div className="empty">
          <Icon name="shelf" size={44} />
          <h3>{lots.length === 0 ? 'The shelves are empty' : 'Nothing matches these filters'}</h3>
          <p>
            {lots.length === 0
              ? 'Log the first donation and PantryPulse starts counting down its expiry.'
              : 'Try another category or clear the search.'}
          </p>
          {lots.length === 0 && (
            <button className="btn btn--primary" onClick={onReceive}>
              <Icon name="plus" size={18} /> Receive stock
            </button>
          )}
        </div>
      ) : (
        <section className="lots" aria-label="Stock lots">
          {visible.map((lot) => (
            <LotCard key={lot.id} lot={lot} onDispatch={onDispatch} onEdit={onEdit} onDelete={onDelete} />
          ))}
        </section>
      )}
    </>
  )
}
