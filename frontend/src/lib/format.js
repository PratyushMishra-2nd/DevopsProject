export const CATEGORIES = [
  { id: 'produce', label: 'Produce' },
  { id: 'dairy', label: 'Dairy' },
  { id: 'bakery', label: 'Bakery' },
  { id: 'grains', label: 'Grains' },
  { id: 'canned', label: 'Canned' },
  { id: 'protein', label: 'Protein' },
  { id: 'beverages', label: 'Beverages' },
]

export const STORAGE = [
  { id: 'ambient', label: 'Ambient' },
  { id: 'chilled', label: 'Chilled' },
  { id: 'frozen', label: 'Frozen' },
]

export const UNITS = ['kg', 'litres', 'units', 'crates']

export const LOT_STATUSES = [
  { id: 'available', label: 'Available' },
  { id: 'on_hold', label: 'On hold' },
  { id: 'depleted', label: 'Depleted' },
  { id: 'discarded', label: 'Discarded' },
]

export const DONOR_KINDS = [
  { id: 'grocer', label: 'Grocer' },
  { id: 'farm', label: 'Farm' },
  { id: 'restaurant', label: 'Restaurant' },
  { id: 'manufacturer', label: 'Manufacturer' },
  { id: 'household', label: 'Household' },
]

export const labelFor = (list, id) => list.find((x) => x.id === id)?.label ?? id

export function freshnessLabel(daysLeft) {
  if (daysLeft < -1) return `Expired ${-daysLeft} days ago`
  if (daysLeft === -1) return 'Expired yesterday'
  if (daysLeft === 0) return 'Use today'
  if (daysLeft === 1) return '1 day left'
  return `${daysLeft} days left`
}

// Share of a 30-day window still remaining, for the freshness fuse bar.
export function fuseFill(daysLeft, window = 30) {
  if (daysLeft <= 0) return 0
  return Math.min(1, daysLeft / window)
}

export function formatQty(n) {
  return Number.isInteger(n) ? String(n) : n.toFixed(n < 10 ? 2 : 1).replace(/\.?0+$/, '')
}

const dateFmt = new Intl.DateTimeFormat('en-IN', { day: 'numeric', month: 'short' })
export function shortDate(iso) {
  if (!iso) return ''
  const [y, m, d] = iso.split('-').map(Number)
  return dateFmt.format(new Date(y, m - 1, d))
}

export function todayIso(offsetDays = 0) {
  const d = new Date()
  d.setDate(d.getDate() + offsetDays)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

export function initials(name) {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0].toUpperCase())
    .join('')
}

export const isOnShelf = (lot) => lot.status === 'available' || lot.status === 'on_hold'
