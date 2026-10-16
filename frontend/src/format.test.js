import { describe, expect, it } from 'vitest';
import { NEXT_ACTIONS, STATUSES, age, dayBounds, initials, nextQuarterHourLocal } from './format.js';

describe('format helpers', () => {
  it('computes age, respecting birthdays later in the year', () => {
    const today = new Date(2026, 9, 16); // 16 Oct 2026
    expect(age('1990-10-16', today)).toBe(36);
    expect(age('1990-12-01', today)).toBe(35);
  });

  it('builds initials without the Dr. prefix', () => {
    expect(initials('Dr. Ananya Rao')).toBe('AR');
    expect(initials('Meera Iyer')).toBe('MI');
  });

  it('returns a one-day window that starts at local midnight', () => {
    const { start, end } = dayBounds(new Date(2026, 9, 16, 15, 30));
    expect(new Date(end) - new Date(start)).toBe(24 * 60 * 60 * 1000);
    expect(new Date(start).getHours()).toBe(0);
  });

  it('rounds the default booking time up to the next quarter hour', () => {
    expect(nextQuarterHourLocal(new Date(2026, 9, 16, 9, 7))).toBe('2026-10-16T09:15');
    expect(nextQuarterHourLocal(new Date(2026, 9, 16, 9, 45))).toBe('2026-10-16T10:00');
  });

  it('defines next actions for every status', () => {
    for (const status of STATUSES) expect(NEXT_ACTIONS[status]).toBeDefined();
  });
});
