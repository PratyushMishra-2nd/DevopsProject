// Hand-drawn line icons (24px grid, currentColor) so the app needs no icon font.
const PATHS = {
  produce:
    'M12 21c-4.5 0-7-3.4-7-7.5C5 9 8 6.5 12 6.5S19 9 19 13.5 16.5 21 12 21Zm0-14.5V3m0 3.5c1-1.8 2.8-2.7 4.5-2.5',
  dairy: 'M8 3h8M9 3v3l-2.5 4v10.5a.5.5 0 0 0 .5.5h10a.5.5 0 0 0 .5-.5V10L15 6V3M6.5 13h11',
  bakery: 'M4 13c0-4 3.6-7 8-7s8 3 8 7v5H4v-5Zm4-3v8m4-9v9m4-8v8',
  grains:
    'M12 21V9m0 4c-2.5 0-4-1.5-4-4 2.5 0 4 1.5 4 4Zm0 0c2.5 0 4-1.5 4-4-2.5 0-4 1.5-4 4Zm0-4c-2 0-3-1.3-3-3.2C11 5.8 12 7 12 9Zm0 0c2 0 3-1.3 3-3.2C13 5.8 12 7 12 9Z',
  canned:
    'M6 6c0-1.1 2.7-2 6-2s6 .9 6 2v12c0 1.1-2.7 2-6 2s-6-.9-6-2V6Zm0 0c0 1.1 2.7 2 6 2s6-.9 6-2M6 11h12',
  protein: 'M12 3c3.5 0 6 4.5 6 9.5S15.5 21 12 21s-6-3.5-6-8.5S8.5 3 12 3Z',
  beverages: 'M7 3h10l-1.5 17a1 1 0 0 1-1 1h-5a1 1 0 0 1-1-1L7 3Zm.6 6h8.8',
  ambient:
    'M12 4v2m0 12v2M4 12h2m12 0h2M6.3 6.3l1.4 1.4m8.6 8.6 1.4 1.4m0-11.4-1.4 1.4m-8.6 8.6-1.4 1.4M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8Z',
  chilled: 'M12 3v18M4.2 7.5l15.6 9M4.2 16.5l15.6-9M9.5 4.5 12 7l2.5-2.5m-5 15L12 17l2.5 2.5',
  frozen:
    'M12 2.5v19M3.8 7.2l16.4 9.6M3.8 16.8l16.4-9.6M12 6l-2-2m2 2 2-2m-2 14-2 2m2-2 2 2M5.5 9.5 3 10m2.5-.5L5 7m13.5 2.5L21 10m-2.5-.5.5-2.5',
  plus: 'M12 5v14M5 12h14',
  truck:
    'M3 6h11v9H3V6Zm11 3h4l3 3v3h-7V9ZM7 18.5a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3Zm10 0a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3Z',
  edit: 'M4 20h4L19 9l-4-4L4 16v4Zm9-13 4 4',
  trash: 'M5 7h14M10 7V4h4v3m-7 0 1 13h8l1-13',
  close: 'M6 6l12 12M18 6 6 18',
  search: 'M11 18a7 7 0 1 0 0-14 7 7 0 0 0 0 14Zm5-2 4 4',
  undo: 'M9 7 4 12l5 5M4 12h11a5 5 0 0 1 0 10h-2',
  shelf: 'M4 4v16M20 4v16M4 9h16M4 15h16M7 6.5h3M13 12h4M8 18h5',
  radar: 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18Zm0-4a5 5 0 1 0 0-10 5 5 0 0 0 0 10Zm0-5 6-6',
  handshake: 'M3 11l4-4 5 3 5-3 4 4-6 6a2 2 0 0 1-3 0l-3-3m-6 0 3 3',
  ledger: 'M6 3h11a1 1 0 0 1 1 1v16a1 1 0 0 1-1 1H6a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Zm3 5h6M9 12h6m-6 4h3',
  alert: 'M12 9v4m0 3.5v.5M10.3 4.3 2.6 18a2 2 0 0 0 1.7 3h15.4a2 2 0 0 0 1.7-3L13.7 4.3a2 2 0 0 0-3.4 0Z',
  check: 'M5 12.5 10 17l9-10',
  refresh: 'M20 11a8 8 0 0 0-14.6-4.5M4 4v3h3M4 13a8 8 0 0 0 14.6 4.5M20 20v-3h-3',
}

export default function Icon({ name, size = 20, className = '', title }) {
  return (
    <svg
      className={`icon ${className}`}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden={title ? undefined : true}
      role={title ? 'img' : undefined}
    >
      {title && <title>{title}</title>}
      <path d={PATHS[name] ?? PATHS.alert} />
    </svg>
  )
}

export function Logo() {
  return (
    <svg className="logo-mark" viewBox="0 0 40 40" aria-hidden="true">
      <rect width="40" height="40" rx="11" fill="var(--forest)" />
      <path
        d="M7 23h6l3-8 5 14 4-10 2 4h6"
        fill="none"
        stroke="var(--paper)"
        strokeWidth="2.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="33" cy="12" r="3.2" fill="var(--saffron)" />
    </svg>
  )
}
