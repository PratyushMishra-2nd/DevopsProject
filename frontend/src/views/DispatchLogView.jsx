import Icon from '../components/Icon.jsx'
import { formatQty, shortDate } from '../lib/format.js'

export default function DispatchLogView({ dispatches, onVoid }) {
  const partners = new Set(dispatches.map((d) => d.partner)).size
  return (
    <section aria-label="Dispatch log">
      <header className="section-head">
        <div>
          <h2>Dispatch log</h2>
          <p>
            {dispatches.length} dispatch{dispatches.length === 1 ? '' : 'es'} to {partners} partner
            organisation
            {partners === 1 ? '' : 's'}. Void an entry to put the food back on the shelf.
          </p>
        </div>
      </header>
      {dispatches.length === 0 ? (
        <div className="empty">
          <Icon name="ledger" size={44} />
          <h3>No food has gone out yet</h3>
          <p>Use “Dispatch” on a lot in the Shelf view to record a hand-over.</p>
        </div>
      ) : (
        <div className="ledger-wrap">
          <table className="ledger">
            <thead>
              <tr>
                <th scope="col">Date</th>
                <th scope="col">Partner</th>
                <th scope="col">Item</th>
                <th scope="col" className="r">
                  Quantity
                </th>
                <th scope="col">
                  <span className="sr-only">Actions</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {dispatches.map((d) => (
                <tr key={d.id}>
                  <td data-label="Date">{shortDate(d.dispatched_on)}</td>
                  <td data-label="Partner">{d.partner}</td>
                  <td data-label="Item">
                    {d.item_name} <span className="muted">#{d.lot_id}</span>
                  </td>
                  <td data-label="Quantity" className="r num">
                    {formatQty(d.quantity)} {d.unit}
                  </td>
                  <td className="r">
                    <button className="btn btn--ghost btn--sm" onClick={() => onVoid(d)}>
                      <Icon name="undo" size={15} /> Void
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}
