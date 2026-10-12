// Thin fetch wrapper. All calls go to relative /api URLs: Vite's dev proxy,
// Nginx in Docker and the Kubernetes Ingress all route /api to FastAPI.

export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

export function describeError(data, status) {
  const detail = data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail.length) {
    return detail
      .map((e) => {
        const field = Array.isArray(e.loc) ? e.loc[e.loc.length - 1] : 'field'
        return `${String(field).replace(/_/g, ' ')}: ${e.msg}`
      })
      .join(' · ')
  }
  return `Request failed (HTTP ${status})`
}

function query(params = {}) {
  const qs = new URLSearchParams(
    Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== ''),
  ).toString()
  return qs ? `?${qs}` : ''
}

export async function request(path, { method = 'GET', body } = {}) {
  let res
  try {
    res = await fetch(`/api${path}`, {
      method,
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    })
  } catch {
    throw new ApiError('Cannot reach the PantryPulse API. Is the backend running?', 0)
  }
  if (res.status === 204) return null
  const data = await res.json().catch(() => null)
  if (!res.ok) throw new ApiError(describeError(data, res.status), res.status)
  return data
}

export const api = {
  info: () => request('/info'),
  lots: (params) => request(`/lots${query(params)}`),
  summary: () => request('/lots/summary'),
  createLot: (body) => request('/lots', { method: 'POST', body }),
  updateLot: (id, body) => request(`/lots/${id}`, { method: 'PUT', body }),
  deleteLot: (id) => request(`/lots/${id}`, { method: 'DELETE' }),
  donors: () => request('/donors'),
  createDonor: (body) => request('/donors', { method: 'POST', body }),
  updateDonor: (id, body) => request(`/donors/${id}`, { method: 'PUT', body }),
  deleteDonor: (id) => request(`/donors/${id}`, { method: 'DELETE' }),
  dispatches: () => request('/dispatches'),
  createDispatch: (body) => request('/dispatches', { method: 'POST', body }),
  voidDispatch: (id) => request(`/dispatches/${id}`, { method: 'DELETE' }),
}
