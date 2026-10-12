import { useState } from 'react'
import { CATEGORIES, DONOR_KINDS, LOT_STATUSES, STORAGE, UNITS, formatQty, todayIso } from '../lib/format.js'

function Field({ label, hint, children, wide }) {
  return (
    <label className={`field ${wide ? 'field--wide' : ''}`}>
      <span className="field__label">{label}</span>
      {children}
      {hint && <span className="field__hint">{hint}</span>}
    </label>
  )
}

function FormError({ message }) {
  if (!message) return null
  return (
    <p className="form-error" role="alert">
      {message}
    </p>
  )
}

function useSubmit(onSubmit) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const submit = async (e, payload) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      await onSubmit(payload)
    } catch (err) {
      setError(err.message)
      setBusy(false)
    }
  }
  return { busy, error, submit }
}

export function LotForm({ lot, donors, onSubmit, onCancel }) {
  const editing = Boolean(lot)
  const [form, setForm] = useState(() => ({
    item_name: lot?.item_name ?? '',
    category: lot?.category ?? 'produce',
    quantity: lot?.quantity ?? '',
    unit: lot?.unit ?? 'kg',
    storage: lot?.storage ?? 'ambient',
    status: lot?.status ?? 'available',
    received_on: lot?.received_on ?? todayIso(),
    expires_on: lot?.expires_on ?? todayIso(7),
    donor_id: lot?.donor_id ?? '',
    notes: lot?.notes ?? '',
  }))
  const { busy, error, submit } = useSubmit(onSubmit)
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))

  const payload = () => {
    const body = {
      ...form,
      quantity: form.quantity === '' ? null : Number(form.quantity),
      donor_id: form.donor_id === '' ? null : Number(form.donor_id),
      notes: form.notes.trim() || null,
    }
    if (!editing) delete body.status
    return body
  }

  return (
    <form className="form" onSubmit={(e) => submit(e, payload())}>
      <Field label="Item" wide>
        <input
          value={form.item_name}
          onChange={set('item_name')}
          placeholder="e.g. Toned milk pouches"
          required
          minLength={2}
          maxLength={120}
        />
      </Field>
      <Field label="Category">
        <select value={form.category} onChange={set('category')}>
          {CATEGORIES.map((c) => (
            <option key={c.id} value={c.id}>
              {c.label}
            </option>
          ))}
        </select>
      </Field>
      <Field label="Storage zone">
        <select value={form.storage} onChange={set('storage')}>
          {STORAGE.map((s) => (
            <option key={s.id} value={s.id}>
              {s.label}
            </option>
          ))}
        </select>
      </Field>
      <Field label="Quantity">
        <input
          type="number"
          inputMode="decimal"
          min={editing ? 0 : 0.01}
          step="any"
          value={form.quantity}
          onChange={set('quantity')}
          required
        />
      </Field>
      <Field label="Unit">
        <select value={form.unit} onChange={set('unit')}>
          {UNITS.map((u) => (
            <option key={u}>{u}</option>
          ))}
        </select>
      </Field>
      <Field label="Received on">
        <input type="date" value={form.received_on} onChange={set('received_on')} required />
      </Field>
      <Field label="Best before" hint="Drives the expiry radar">
        <input type="date" value={form.expires_on} onChange={set('expires_on')} required />
      </Field>
      <Field label="Donor" wide>
        <select value={form.donor_id} onChange={set('donor_id')}>
          <option value="">Anonymous / walk-in</option>
          {donors.map((d) => (
            <option key={d.id} value={d.id}>
              {d.name}
            </option>
          ))}
        </select>
      </Field>
      {editing && (
        <Field label="Status" wide>
          <select value={form.status} onChange={set('status')}>
            {LOT_STATUSES.map((s) => (
              <option key={s.id} value={s.id}>
                {s.label}
              </option>
            ))}
          </select>
        </Field>
      )}
      <Field label="Notes" wide>
        <textarea rows={3} value={form.notes} onChange={set('notes')} maxLength={500} />
      </Field>
      <FormError message={error} />
      <div className="form__actions">
        <button type="button" className="btn btn--ghost" onClick={onCancel}>
          Cancel
        </button>
        <button type="submit" className="btn btn--primary" disabled={busy}>
          {busy ? 'Saving…' : editing ? 'Save changes' : 'Receive stock'}
        </button>
      </div>
    </form>
  )
}

export function DispatchForm({ lot, onSubmit, onCancel }) {
  const [form, setForm] = useState({ partner: '', quantity: '', dispatched_on: todayIso() })
  const { busy, error, submit } = useSubmit(onSubmit)
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))
  return (
    <form
      className="form"
      onSubmit={(e) =>
        submit(e, {
          lot_id: lot.id,
          partner: form.partner,
          quantity: Number(form.quantity),
          dispatched_on: form.dispatched_on,
        })
      }
    >
      <div className="dispatch-lot field--wide">
        <span className="kicker">From lot #{lot.id}</span>
        <strong>{lot.item_name}</strong>
        <span>
          {formatQty(lot.quantity)} {lot.unit} on the shelf
        </span>
      </div>
      <Field label="Partner organisation" wide>
        <input
          value={form.partner}
          onChange={set('partner')}
          placeholder="e.g. Asha Night Shelter"
          required
          minLength={2}
          list="partner-suggestions"
        />
        <datalist id="partner-suggestions">
          <option value="Asha Night Shelter" />
          <option value="Sunrise Primary School Kitchen" />
          <option value="Old Town Community Kitchen" />
        </datalist>
      </Field>
      <Field label={`Quantity (${lot.unit})`}>
        <input
          type="number"
          inputMode="decimal"
          min="0.01"
          step="any"
          max={lot.quantity}
          value={form.quantity}
          onChange={set('quantity')}
          required
        />
      </Field>
      <Field label="Date">
        <input type="date" value={form.dispatched_on} onChange={set('dispatched_on')} required />
      </Field>
      <FormError message={error} />
      <div className="form__actions">
        <button type="button" className="btn btn--ghost" onClick={onCancel}>
          Cancel
        </button>
        <button type="submit" className="btn btn--primary" disabled={busy}>
          {busy ? 'Recording…' : 'Record dispatch'}
        </button>
      </div>
    </form>
  )
}

export function DonorForm({ donor, onSubmit, onCancel }) {
  const [form, setForm] = useState({
    name: donor?.name ?? '',
    kind: donor?.kind ?? 'grocer',
    city: donor?.city ?? '',
    contact_email: donor?.contact_email ?? '',
  })
  const { busy, error, submit } = useSubmit(onSubmit)
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))
  return (
    <form
      className="form"
      onSubmit={(e) => submit(e, { ...form, contact_email: form.contact_email.trim() || null })}
    >
      <Field label="Donor name" wide>
        <input value={form.name} onChange={set('name')} required minLength={2} maxLength={120} />
      </Field>
      <Field label="Type">
        <select value={form.kind} onChange={set('kind')}>
          {DONOR_KINDS.map((k) => (
            <option key={k.id} value={k.id}>
              {k.label}
            </option>
          ))}
        </select>
      </Field>
      <Field label="City">
        <input value={form.city} onChange={set('city')} required minLength={2} maxLength={80} />
      </Field>
      <Field label="Contact email" hint="Optional" wide>
        <input type="email" value={form.contact_email} onChange={set('contact_email')} />
      </Field>
      <FormError message={error} />
      <div className="form__actions">
        <button type="button" className="btn btn--ghost" onClick={onCancel}>
          Cancel
        </button>
        <button type="submit" className="btn btn--primary" disabled={busy}>
          {busy ? 'Saving…' : donor ? 'Save donor' : 'Add donor'}
        </button>
      </div>
    </form>
  )
}
