import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError, api, describeError } from './api.js'

afterEach(() => vi.restoreAllMocks())

const json = (status, body) => Promise.resolve(new Response(JSON.stringify(body), { status }))

describe('api client', () => {
  it('sends JSON to relative /api URLs', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(() => json(201, { id: 7 }))
    await api.createDonor({ name: 'Mahanadi Dairy Co-op' })
    const [url, opts] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/donors')
    expect(opts.method).toBe('POST')
    expect(JSON.parse(opts.body)).toEqual({ name: 'Mahanadi Dairy Co-op' })
  })

  it('drops empty query params', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(() => json(200, []))
    await api.lots({ category: 'dairy', q: '' })
    expect(fetchMock.mock.calls[0][0]).toBe('/api/lots?category=dairy')
  })

  it('turns FastAPI error details into readable messages', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(() =>
      json(422, { detail: 'Only 40 kg left in this lot' }),
    )
    await expect(api.createDispatch({})).rejects.toMatchObject({
      status: 422,
      message: 'Only 40 kg left in this lot',
    })
  })

  it('reports network failures as status 0', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(() => Promise.reject(new TypeError('Failed to fetch')))
    const err = await api.lots().catch((e) => e)
    expect(err).toBeInstanceOf(ApiError)
    expect(err.status).toBe(0)
  })

  it('returns null for 204 responses', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(() =>
      Promise.resolve(new Response(null, { status: 204 })),
    )
    expect(await api.deleteLot(3)).toBeNull()
  })
})

describe('describeError', () => {
  it('joins validation errors with field names', () => {
    const msg = describeError({ detail: [{ loc: ['body', 'expires_on'], msg: 'Field required' }] }, 422)
    expect(msg).toBe('expires on: Field required')
  })
})
