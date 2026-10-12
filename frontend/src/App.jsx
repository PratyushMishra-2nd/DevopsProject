import { useCallback, useEffect, useRef, useState } from 'react'
import Icon, { Logo } from './components/Icon.jsx'
import { ConfirmDialog, Drawer, Toasts } from './components/Overlays.jsx'
import { DispatchForm, DonorForm, LotForm } from './components/Forms.jsx'
import ShelfView from './views/ShelfView.jsx'
import RadarView from './views/RadarView.jsx'
import DonorsView from './views/DonorsView.jsx'
import DispatchLogView from './views/DispatchLogView.jsx'
import { api } from './lib/api.js'
import { formatQty } from './lib/format.js'

const TABS = [
  { id: 'shelf', label: 'Shelf', icon: 'shelf' },
  { id: 'radar', label: 'Expiry radar', icon: 'radar' },
  { id: 'donors', label: 'Donors', icon: 'handshake' },
  { id: 'log', label: 'Dispatch log', icon: 'ledger' },
]

function LoadingShelf() {
  return (
    <div className="lots" aria-busy="true" aria-label="Loading stock">
      {Array.from({ length: 6 }, (_, i) => (
        <div key={i} className="lot lot--skeleton">
          <span />
          <span />
          <span />
        </div>
      ))}
    </div>
  )
}

export default function App() {
  const [tab, setTab] = useState('shelf')
  const [data, setData] = useState({ lots: [], summary: null, donors: [], dispatches: [] })
  const [status, setStatus] = useState('loading') // loading | ready | error
  const [loadError, setLoadError] = useState('')
  const [build, setBuild] = useState(null)
  const [panel, setPanel] = useState(null) // { type, item }
  const [confirm, setConfirm] = useState(null)
  const [confirmBusy, setConfirmBusy] = useState(false)
  const [toasts, setToasts] = useState([])
  const toastId = useRef(0)
  const loaded = useRef(false)

  const toast = useCallback((message, kind = 'success') => {
    const id = ++toastId.current
    setToasts((t) => [...t, { id, message, kind }])
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 4500)
  }, [])

  const refresh = useCallback(async () => {
    try {
      const [lots, summary, donors, dispatches] = await Promise.all([
        api.lots(),
        api.summary(),
        api.donors(),
        api.dispatches(),
      ])
      setData({ lots, summary, donors, dispatches })
      loaded.current = true
      setStatus('ready')
      setLoadError('')
    } catch (err) {
      // After a successful first load keep showing data and surface the error as a toast.
      if (loaded.current) {
        toast(err.message, 'error')
      } else {
        setLoadError(err.message)
        setStatus('error')
      }
    }
  }, [toast])

  useEffect(() => {
    // Fetch-on-mount: refresh() only sets state after the network round trip resolves.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    refresh()
    api
      .info()
      .then(setBuild)
      .catch(() => setBuild(null))
  }, [refresh])

  const close = () => setPanel(null)

  const run = async (action, message) => {
    await action()
    close()
    toast(message)
    await refresh()
  }

  const askDelete = (title, message, action, done) =>
    setConfirm({
      title,
      message,
      onConfirm: async () => {
        setConfirmBusy(true)
        try {
          await action()
          toast(done)
          await refresh()
        } catch (err) {
          toast(err.message, 'error')
        } finally {
          setConfirmBusy(false)
          setConfirm(null)
        }
      },
    })

  const handlers = {
    onReceive: () => setPanel({ type: 'lot' }),
    onEdit: (lot) => setPanel({ type: 'lot', item: lot }),
    onDispatch: (lot) => setPanel({ type: 'dispatch', item: lot }),
    onDelete: (lot) =>
      askDelete(
        `Delete “${lot.item_name}”?`,
        'This removes the lot entirely. Lots that already have dispatches must be marked discarded instead.',
        () => api.deleteLot(lot.id),
        'Lot deleted',
      ),
  }

  let panelContent = null
  if (panel?.type === 'lot') {
    const lot = panel.item
    panelContent = (
      <Drawer
        title={lot ? 'Edit stock lot' : 'Receive stock'}
        kicker={lot ? `Lot #${lot.id}` : 'New donation'}
        onClose={close}
      >
        <LotForm
          lot={lot}
          donors={data.donors}
          onCancel={close}
          onSubmit={(body) =>
            lot
              ? run(() => api.updateLot(lot.id, body), 'Lot updated')
              : run(() => api.createLot(body), `${body.item_name} added to the shelf`)
          }
        />
      </Drawer>
    )
  } else if (panel?.type === 'dispatch') {
    panelContent = (
      <Drawer title="Dispatch to a partner" kicker="Outgoing food" onClose={close}>
        <DispatchForm
          lot={panel.item}
          onCancel={close}
          onSubmit={(body) =>
            run(
              () => api.createDispatch(body),
              `${formatQty(body.quantity)} ${panel.item.unit} dispatched to ${body.partner}`,
            )
          }
        />
      </Drawer>
    )
  } else if (panel?.type === 'donor') {
    const donor = panel.item
    panelContent = (
      <Drawer title={donor ? 'Edit donor' : 'Add donor'} kicker="Donor directory" onClose={close}>
        <DonorForm
          donor={donor}
          onCancel={close}
          onSubmit={(body) =>
            donor
              ? run(() => api.updateDonor(donor.id, body), 'Donor updated')
              : run(() => api.createDonor(body), `${body.name} added`)
          }
        />
      </Drawer>
    )
  }

  return (
    <div className="app">
      <header className="masthead">
        <div className="masthead__brand">
          <Logo />
          <div>
            <h1>PantryPulse</h1>
            <p>Community food bank stock &amp; expiry tracker</p>
          </div>
        </div>
        <div className="masthead__actions">
          {build && (
            <span className="build-chip" title={`${build.environment} build`}>
              <span className="dot" /> {build.environment} · {String(build.git_sha).slice(0, 7)}
            </span>
          )}
          <button className="btn btn--primary" onClick={handlers.onReceive}>
            <Icon name="plus" size={18} /> Receive stock
          </button>
        </div>
      </header>

      <nav className="tabs" aria-label="Sections">
        {TABS.map((t) => (
          <button
            key={t.id}
            className={`tab ${tab === t.id ? 'tab--on' : ''}`}
            onClick={() => setTab(t.id)}
            aria-current={tab === t.id ? 'page' : undefined}
          >
            <Icon name={t.icon} size={18} />
            {t.label}
            {t.id === 'radar' && data.summary?.expiring_soon > 0 && (
              <span className="tab__badge">{data.summary.expiring_soon}</span>
            )}
          </button>
        ))}
      </nav>

      <main className="main">
        {status === 'loading' && <LoadingShelf />}
        {status === 'error' && (
          <div className="banner banner--error" role="alert">
            <Icon name="alert" size={22} />
            <div>
              <strong>We couldn’t load the pantry.</strong>
              <p>{loadError}</p>
            </div>
            <button className="btn btn--ghost" onClick={refresh}>
              <Icon name="refresh" size={16} /> Try again
            </button>
          </div>
        )}
        {status === 'ready' && tab === 'shelf' && (
          <ShelfView lots={data.lots} summary={data.summary} {...handlers} />
        )}
        {status === 'ready' && tab === 'radar' && <RadarView lots={data.lots} onEdit={handlers.onEdit} />}
        {status === 'ready' && tab === 'donors' && (
          <DonorsView
            donors={data.donors}
            onAdd={() => setPanel({ type: 'donor' })}
            onEdit={(d) => setPanel({ type: 'donor', item: d })}
            onDelete={(d) =>
              askDelete(
                `Remove ${d.name}?`,
                'Their past lots stay on record as anonymous donations.',
                () => api.deleteDonor(d.id),
                'Donor removed',
              )
            }
          />
        )}
        {status === 'ready' && tab === 'log' && (
          <DispatchLogView
            dispatches={data.dispatches}
            onVoid={(d) =>
              askDelete(
                'Void this dispatch?',
                `${formatQty(d.quantity)} ${d.unit} of ${d.item_name} goes back on the shelf.`,
                () => api.voidDispatch(d.id),
                'Dispatch voided, stock restored',
              )
            }
          />
        )}
      </main>

      <footer className="colophon">
        PantryPulse · built by Pratyush Mishra · FastAPI · React · PostgreSQL · Kubernetes
      </footer>

      {panelContent}
      {confirm && (
        <ConfirmDialog
          title={confirm.title}
          message={confirm.message}
          confirmLabel="Yes, do it"
          busy={confirmBusy}
          onConfirm={confirm.onConfirm}
          onCancel={() => setConfirm(null)}
        />
      )}
      <Toasts toasts={toasts} onDismiss={(id) => setToasts((t) => t.filter((x) => x.id !== id))} />
    </div>
  )
}
