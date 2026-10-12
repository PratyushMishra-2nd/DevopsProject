import Icon from '../components/Icon.jsx'
import { DONOR_KINDS, initials, labelFor } from '../lib/format.js'

export default function DonorsView({ donors, onAdd, onEdit, onDelete }) {
  return (
    <section aria-label="Donors">
      <header className="section-head">
        <div>
          <h2>Donors</h2>
          <p>The grocers, farms and neighbours who keep the shelves full.</p>
        </div>
        <button className="btn btn--primary" onClick={onAdd}>
          <Icon name="plus" size={18} /> Add donor
        </button>
      </header>
      {donors.length === 0 ? (
        <div className="empty">
          <Icon name="handshake" size={44} />
          <h3>No donors yet</h3>
          <p>Add a donor so incoming stock can be traced back to them.</p>
        </div>
      ) : (
        <ul className="donors">
          {donors.map((d) => (
            <li key={d.id} className={`donor donor--${d.kind}`}>
              <span className="donor__mono" aria-hidden="true">
                {initials(d.name)}
              </span>
              <div className="donor__body">
                <h3>{d.name}</h3>
                <p>
                  {labelFor(DONOR_KINDS, d.kind)} · {d.city}
                </p>
                {d.contact_email && <a href={`mailto:${d.contact_email}`}>{d.contact_email}</a>}
              </div>
              <div className="donor__count">
                <span className="num">{d.lot_count}</span>
                <span>lot{d.lot_count === 1 ? '' : 's'}</span>
              </div>
              <div className="donor__actions">
                <button className="icon-btn" onClick={() => onEdit(d)} aria-label={`Edit ${d.name}`}>
                  <Icon name="edit" size={18} />
                </button>
                <button
                  className="icon-btn icon-btn--danger"
                  onClick={() => onDelete(d)}
                  aria-label={`Delete ${d.name}`}
                >
                  <Icon name="trash" size={18} />
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
