import { describe, expect, it } from 'vitest'
import { formatQty, freshnessLabel, fuseFill, initials, isOnShelf } from './format.js'

describe('freshnessLabel', () => {
  it('describes past, present and future expiry', () => {
    expect(freshnessLabel(-4)).toBe('Expired 4 days ago')
    expect(freshnessLabel(-1)).toBe('Expired yesterday')
    expect(freshnessLabel(0)).toBe('Use today')
    expect(freshnessLabel(1)).toBe('1 day left')
    expect(freshnessLabel(9)).toBe('9 days left')
  })
})

describe('fuseFill', () => {
  it('clamps to the 0..1 range over a 30 day window', () => {
    expect(fuseFill(-2)).toBe(0)
    expect(fuseFill(15)).toBe(0.5)
    expect(fuseFill(400)).toBe(1)
  })
})

describe('helpers', () => {
  it('formats quantities without trailing zeros', () => {
    expect(formatQty(40)).toBe('40')
    expect(formatQty(12.5)).toBe('12.5')
    expect(formatQty(2.25)).toBe('2.25')
  })

  it('builds donor initials', () => {
    expect(initials('Kalinga Organic Farms')).toBe('KO')
  })

  it('treats available and on-hold lots as on the shelf', () => {
    expect(isOnShelf({ status: 'on_hold' })).toBe(true)
    expect(isOnShelf({ status: 'depleted' })).toBe(false)
  })
})
