import { useEffect, useState } from 'react';
import { api } from '../api.js';
import { ACTION_LABELS, NEXT_ACTIONS, STATUSES, STATUS_LABELS, dayBounds, formatDate, formatTime } from '../format.js';
import { EmptyState, StatusBadge } from './ui.jsx';

const RANGES = {
  today: { label: 'Today', days: 1 },
  week: { label: 'Next 7 days', days: 7 },
  all: { label: 'All time', days: null },
};

export default function AppointmentsView({ doctors, refreshKey, onStatusChange, onDelete, onBook, notify }) {
  const [status, setStatus] = useState('');
  const [doctorId, setDoctorId] = useState('');
  const [range, setRange] = useState('week');
  const [rows, setRows] = useState(null);

  useEffect(() => {
    const { days } = RANGES[range];
    const bounds = days ? dayBounds(new Date(), days) : {};
    let cancelled = false;
    api
      .listAppointments({ status, doctor_id: doctorId, start: bounds.start, end: bounds.end })
      .then((data) => !cancelled && setRows(data))
      .catch((err) => notify(err.message, 'error'));
    return () => {
      cancelled = true;
    };
  }, [status, doctorId, range, refreshKey, notify]);

  return (
    <section className="card">
      <header className="card-header wrap">
        <div className="chips" role="tablist" aria-label="Filter by status">
          <button className={`chip ${status === '' ? 'active' : ''}`} onClick={() => setStatus('')}>
            All
          </button>
          {STATUSES.map((s) => (
            <button key={s} className={`chip ${status === s ? 'active' : ''}`} onClick={() => setStatus(s)}>
              {STATUS_LABELS[s]}
            </button>
          ))}
        </div>
        <div className="filters">
          <select value={doctorId} onChange={(e) => setDoctorId(e.target.value)} aria-label="Filter by doctor">
            <option value="">All doctors</option>
            {doctors.map((d) => (
              <option key={d.id} value={d.id}>
                {d.full_name}
              </option>
            ))}
          </select>
          <select value={range} onChange={(e) => setRange(e.target.value)} aria-label="Date range">
            {Object.entries(RANGES).map(([key, r]) => (
              <option key={key} value={key}>
                {r.label}
              </option>
            ))}
          </select>
          <button className="button primary" onClick={onBook}>
            + Book appointment
          </button>
        </div>
      </header>

      {rows === null ? (
        <div className="skeleton-table" aria-busy="true" />
      ) : rows.length === 0 ? (
        <EmptyState title="No appointments match these filters" hint="Try a wider date range." />
      ) : (
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>When</th>
                <th>Patient</th>
                <th>Doctor</th>
                <th>Reason</th>
                <th>Status</th>
                <th aria-label="Actions" />
              </tr>
            </thead>
            <tbody>
              {rows.map((a) => (
                <tr key={a.id}>
                  <td data-label="When">
                    <strong>{formatTime(a.scheduled_at)}</strong>
                    <span className="muted block">
                      {formatDate(a.scheduled_at)} · {a.duration_minutes} min
                    </span>
                  </td>
                  <td data-label="Patient">
                    {a.patient.full_name}
                    <span className="muted block">{a.patient.phone}</span>
                  </td>
                  <td data-label="Doctor">
                    {a.doctor.full_name}
                    <span className="muted block">{a.doctor.specialty}</span>
                  </td>
                  <td data-label="Reason">{a.reason}</td>
                  <td data-label="Status">
                    <StatusBadge status={a.status} />
                  </td>
                  <td className="row-actions">
                    {NEXT_ACTIONS[a.status].map((next) => (
                      <button key={next} className="button small" onClick={() => onStatusChange(a, next)}>
                        {ACTION_LABELS[next]}
                      </button>
                    ))}
                    <button className="button small danger" onClick={() => onDelete(a)} aria-label="Delete">
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
