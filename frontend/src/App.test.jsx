import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import App from './App.jsx'

const LOTS = [
  {
    id: 1,
    item_name: 'Toned milk pouches',
    category: 'dairy',
    quantity: 54,
    unit: 'litres',
    storage: 'chilled',
    status: 'available',
    received_on: '2026-10-11',
    expires_on: '2026-10-14',
    notes: null,
    donor_id: 1,
    donor_name: 'Mahanadi Dairy Co-op',
    days_left: 2,
    freshness: 'critical',
  },
  {
    id: 2,
    item_name: 'Basmati rice',
    category: 'grains',
    quantity: 100,
    unit: 'kg',
    storage: 'ambient',
    status: 'available',
    received_on: '2026-10-01',
    expires_on: '2027-06-01',
    notes: null,
    donor_id: null,
    donor_name: null,
    days_left: 232,
    freshness: 'fresh',
  },
]

const SUMMARY = {
  active_lots: 2,
  expiring_soon: 1,
  expired_on_shelf: 0,
  dispatched_this_week: 30,
  partners_served: 2,
  by_category: {},
  by_storage: {},
  warning_days: 7,
}

function mockBackend(overrides = {}) {
  const routes = {
    '/api/lots': LOTS,
    '/api/lots/summary': SUMMARY,
    '/api/donors': [],
    '/api/dispatches': [],
    '/api/info': { service: 'PantryPulse API', environment: 'test', git_sha: 'abc1234def' },
    ...overrides,
  }
  return vi.spyOn(globalThis, 'fetch').mockImplementation((url) => {
    const body = routes[url]
    if (body instanceof Error) return Promise.reject(body)
    return Promise.resolve(new Response(JSON.stringify(body ?? {}), { status: body ? 200 : 404 }))
  })
}

beforeEach(() => vi.restoreAllMocks())
afterEach(() => vi.restoreAllMocks())

describe('App', () => {
  it('loads lots from the API and shows KPIs and build info', async () => {
    mockBackend()
    render(<App />)
    expect(await screen.findByText('Toned milk pouches')).toBeInTheDocument()
    expect(screen.getByText('Basmati rice')).toBeInTheDocument()
    expect(screen.getByText('Lots on the shelf')).toBeInTheDocument()
    expect(screen.getByText(/test · abc1234/)).toBeInTheDocument()
    expect(screen.getByText('2 days left · best before 14 Oct')).toBeInTheDocument()
  })

  it('filters by category chip', async () => {
    mockBackend()
    const user = userEvent.setup()
    render(<App />)
    await screen.findByText('Toned milk pouches')
    await user.click(
      within(screen.getByRole('group', { name: 'Category' })).getByRole('button', { name: /Grains/ }),
    )
    expect(screen.queryByText('Toned milk pouches')).not.toBeInTheDocument()
    expect(screen.getByText('Basmati rice')).toBeInTheDocument()
  })

  it('shows an error banner with retry when the API is down', async () => {
    mockBackend({ '/api/lots': new TypeError('Failed to fetch') })
    render(<App />)
    expect(await screen.findByRole('alert')).toHaveTextContent('Cannot reach the PantryPulse API')
    expect(screen.getByRole('button', { name: /Try again/ })).toBeInTheDocument()
  })

  it('opens the receive-stock drawer', async () => {
    mockBackend()
    const user = userEvent.setup()
    render(<App />)
    await screen.findByText('Toned milk pouches')
    await user.click(screen.getAllByRole('button', { name: /Receive stock/ })[0])
    expect(screen.getByRole('dialog', { name: 'Receive stock' })).toBeInTheDocument()
  })
})
