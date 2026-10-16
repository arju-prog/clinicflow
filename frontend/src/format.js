// Pure helpers (no React) so they can be unit-tested with Vitest.

export const STATUSES = ['SCHEDULED', 'CHECKED_IN', 'COMPLETED', 'CANCELLED', 'NO_SHOW'];

export const STATUS_LABELS = {
  SCHEDULED: 'Scheduled',
  CHECKED_IN: 'Checked in',
  COMPLETED: 'Completed',
  CANCELLED: 'Cancelled',
  NO_SHOW: 'No-show',
};

// Which buttons a receptionist sees for an appointment in a given state.
export const NEXT_ACTIONS = {
  SCHEDULED: ['CHECKED_IN', 'CANCELLED', 'NO_SHOW'],
  CHECKED_IN: ['COMPLETED', 'CANCELLED'],
  COMPLETED: [],
  CANCELLED: ['SCHEDULED'],
  NO_SHOW: ['SCHEDULED'],
};

export const ACTION_LABELS = {
  SCHEDULED: 'Restore',
  CHECKED_IN: 'Check in',
  COMPLETED: 'Complete',
  CANCELLED: 'Cancel',
  NO_SHOW: 'No-show',
};

/** Local-day bounds as ISO strings, so "today" means today in the clinic's timezone. */
export function dayBounds(date = new Date(), days = 1) {
  const start = new Date(date);
  start.setHours(0, 0, 0, 0);
  const end = new Date(start);
  end.setDate(end.getDate() + days);
  return { start: start.toISOString(), end: end.toISOString() };
}

export function formatTime(iso) {
  return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

export function formatDate(iso) {
  return new Date(iso).toLocaleDateString([], { weekday: 'short', day: 'numeric', month: 'short' });
}

export function age(dateOfBirth, today = new Date()) {
  const dob = new Date(dateOfBirth);
  let years = today.getFullYear() - dob.getFullYear();
  const beforeBirthday =
    today.getMonth() < dob.getMonth() ||
    (today.getMonth() === dob.getMonth() && today.getDate() < dob.getDate());
  if (beforeBirthday) years -= 1;
  return years;
}

export function initials(name) {
  return name
    .replace(/^Dr\.?\s+/i, '')
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0].toUpperCase())
    .join('');
}

/** Value for <input type="datetime-local"> rounded up to the next quarter hour. */
export function nextQuarterHourLocal(now = new Date()) {
  const d = new Date(now);
  d.setSeconds(0, 0);
  d.setMinutes(Math.ceil((d.getMinutes() + 1) / 15) * 15);
  const pad = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}
