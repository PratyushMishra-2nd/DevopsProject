import Icon from '../components/Icon.jsx'
import { formatQty, freshnessLabel, isOnShelf, shortDate } from '../lib/format.js'

// Horizontal expiry timeline: every on-shelf lot is a bar ending on its
// best-before day, so the pantry team can see what must move first.
const WINDOW = 30
const TICKS = [0, 3, 7, 14, 30]

function position(daysLeft) {
  // Expired lots sit in a narrow band left of "today".
  const clamped = Math.max(-3, Math.min(WINDOW, daysLeft))
  return ((clamped + 3) / (WINDOW + 3)) * 100
}

export default function RadarView({ lots, onEdit }) {
  const rows = lots.filter(isOnShelf).sort((a, b) => a.days_left - b.days_left)
  const beyond = rows.filter((l) => l.days_left > WINDOW).length

  if (rows.length === 0) {
    return (
      <div className="empty">
        <Icon name="radar" size={44} />
        <h3>Nothing on the radar</h3>
        <p>On-shelf lots appear here, ordered by how soon they expire.</p>
      </div>
    )
  }

  return (
    <section className="radar" aria-label="Expiry radar">
      <header className="radar__intro">
        <h2>Expiry radar</h2>
        <p>
          Next {WINDOW} days. Move the red and saffron lots first.
          {beyond > 0 && ` ${beyond} long-life lot${beyond > 1 ? 's' : ''} sit beyond the window.`}
        </p>
      </header>
      <div className="radar__scale" aria-hidden="true">
        <span className="radar__expired-zone" style={{ width: `${position(0)}%` }}>
          expired
        </span>
        {TICKS.map((t) => (
          <span key={t} className="radar__tick" style={{ left: `${position(t)}%` }}>
            {t === 0 ? 'today' : `+${t}d`}
          </span>
        ))}
      </div>
      <ol className="radar__rows">
        {rows.map((lot) => (
          <li key={lot.id} className={`radar__row radar__row--${lot.freshness}`}>
            <button className="radar__label" onClick={() => onEdit(lot)} title="Edit lot">
              <strong>{lot.item_name}</strong>
              <span>
                {formatQty(lot.quantity)} {lot.unit} · {shortDate(lot.expires_on)}
              </span>
            </button>
            <div className="radar__lane">
              <div className="radar__bar" style={{ width: `${position(lot.days_left)}%` }}>
                <span>{freshnessLabel(lot.days_left)}</span>
              </div>
            </div>
          </li>
        ))}
      </ol>
    </section>
  )
}
