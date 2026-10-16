import { NEXT_ACTIONS, ACTION_LABELS, STATUSES, STATUS_LABELS, formatTime } from '../format.js';
import { Avatar, EmptyState, StatusBadge } from './ui.jsx';

function Kpi({ label, value, hint, tone }) {
  return (
    <article className={`kpi kpi-${tone}`}>
      <span className="kpi-label">{label}</span>
      <strong className="kpi-value">{value}</strong>
      <span className="kpi-hint">{hint}</span>
    </article>
  );
}

function StatusBreakdown({ byStatus, total }) {
  return (
    <section className="card">
      <header className="card-header">
        <h3>Status breakdown</h3>
        <span className="muted">{total} total</span>
      </header>
      <div className="stacked-bar" role="img" aria-label="Appointments by status">
        {STATUSES.map((s) =>
          byStatus[s] ? (
            <span
              key={s}
              className={`bar-seg seg-${s.toLowerCase()}`}
              style={{ flexGrow: byStatus[s] }}
              title={`${STATUS_LABELS[s]}: ${byStatus[s]}`}
            />
          ) : null,
        )}
      </div>
      <ul className="legend">
        {STATUSES.map((s) => (
          <li key={s}>
            <span className={`dot seg-${s.toLowerCase()}`} />
            {STATUS_LABELS[s]}
            <strong>{byStatus[s] ?? 0}</strong>
          </li>
        ))}
      </ul>
    </section>
  );
}

function DoctorLoad({ doctors, today }) {
  const load = doctors
    .filter((d) => d.is_active)
    .map((d) => ({ ...d, count: today.filter((a) => a.doctor_id === d.id && a.status !== 'CANCELLED').length }))
    .sort((a, b) => b.count - a.count);
  const max = Math.max(1, ...load.map((d) => d.count));

  return (
    <section className="card">
      <header className="card-header">
        <h3>Doctor workload today</h3>
      </header>
      <ul className="load-list">
        {load.map((d) => (
          <li key={d.id}>
            <Avatar name={d.full_name} tone="indigo" />
            <div className="load-main">
              <div className="load-row">
                <span>{d.full_name}</span>
                <span className="muted">{d.count} appt</span>
              </div>
              <div className="meter">
                <span style={{ width: `${(d.count / max) * 100}%` }} />
              </div>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}

export default function Dashboard({ stats, today, doctors, onStatusChange, onBook }) {
  const queue = today.filter((a) => a.status !== 'CANCELLED');

  return (
    <>
      <section className="kpi-grid">
        <Kpi label="Today's appointments" value={stats.today} hint="active bookings today" tone="teal" />
        <Kpi label="Upcoming" value={stats.upcoming} hint="scheduled from now on" tone="indigo" />
        <Kpi label="Active doctors" value={stats.active_doctors} hint="accepting bookings" tone="amber" />
        <Kpi label="Registered patients" value={stats.patients} hint="in the clinic register" tone="rose" />
        <Kpi label="Attendance rate" value={`${stats.attendance_rate}%`} hint="completed vs no-show" tone="green" />
      </section>

      <div className="dashboard-grid">
        <section className="card schedule">
          <header className="card-header">
            <h3>Today's schedule</h3>
            <button className="button primary small" onClick={onBook}>
              + Book
            </button>
          </header>
          {queue.length === 0 ? (
            <EmptyState title="No appointments today" hint="Book one to see it appear here." />
          ) : (
            <ol className="timeline">
              {queue.map((a) => (
                <li key={a.id} className={`timeline-item status-${a.status.toLowerCase()}`}>
                  <time className="timeline-time">{formatTime(a.scheduled_at)}</time>
                  <div className="timeline-body">
                    <div className="timeline-title">
                      <strong>{a.patient.full_name}</strong>
                      <StatusBadge status={a.status} />
                    </div>
                    <p className="muted">
                      {a.reason} · {a.doctor.full_name}
                      {a.doctor.room && ` · Room ${a.doctor.room}`}
                    </p>
                  </div>
                  <div className="row-actions">
                    {NEXT_ACTIONS[a.status]
                      .filter((s) => s === 'CHECKED_IN' || s === 'COMPLETED')
                      .map((next) => (
                        <button key={next} className="button small" onClick={() => onStatusChange(a, next)}>
                          {ACTION_LABELS[next]}
                        </button>
                      ))}
                  </div>
                </li>
              ))}
            </ol>
          )}
        </section>

        <div className="side-stack">
          <StatusBreakdown byStatus={stats.by_status} total={stats.total} />
          <DoctorLoad doctors={doctors} today={today} />
        </div>
      </div>
    </>
  );
}
