import { useCallback, useEffect, useState } from 'react';
import { api } from './api.js';
import { STATUS_LABELS, dayBounds } from './format.js';
import AppointmentsView from './components/AppointmentsView.jsx';
import Dashboard from './components/Dashboard.jsx';
import { BookingForm, DoctorForm, PatientForm } from './components/Forms.jsx';
import { DoctorsView, PatientsView } from './components/PeopleViews.jsx';
import { Modal, Toasts } from './components/ui.jsx';

const FRONTEND_VERSION = import.meta.env.VITE_APP_VERSION || 'dev';

const VIEWS = {
  dashboard: { label: 'Dashboard', icon: '▦', subtitle: 'Overview of today at the clinic' },
  appointments: { label: 'Appointments', icon: '◷', subtitle: 'Book, check in and manage visits' },
  doctors: { label: 'Doctors', icon: '✚', subtitle: 'Clinicians and their availability' },
  patients: { label: 'Patients', icon: '☺', subtitle: 'Patient register' },
};

const PIPELINE = ['Commit', 'Pytest', 'Build', 'Trivy', 'GHCR', 'Helm', 'EKS'];

export default function App() {
  const [view, setView] = useState('dashboard');
  const [stats, setStats] = useState(null);
  const [today, setToday] = useState([]);
  const [doctors, setDoctors] = useState([]);
  const [patients, setPatients] = useState([]);
  const [backend, setBackend] = useState({ state: 'checking' });
  const [modal, setModal] = useState(null);
  const [busy, setBusy] = useState(false);
  const [toasts, setToasts] = useState([]);
  const [refreshKey, setRefreshKey] = useState(0);

  const notify = useCallback((message, kind = 'success') => {
    const id = crypto.randomUUID?.() ?? String(Date.now() + Math.random());
    setToasts((t) => [...t, { id, message, kind }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 4500);
  }, []);

  const load = useCallback(async () => {
    const { start, end } = dayBounds();
    try {
      const [s, t, d, p, h] = await Promise.all([
        api.stats(start, end),
        api.listAppointments({ start, end }),
        api.listDoctors(),
        api.listPatients(),
        api.health(),
      ]);
      setStats(s);
      setToday(t);
      setDoctors(d);
      setPatients(p);
      setBackend({ state: 'up', version: h.version });
    } catch (err) {
      setBackend({ state: 'down', error: err.message });
    }
  }, []);

  useEffect(() => {
    load();
    const timer = setInterval(load, 30_000);
    return () => clearInterval(timer);
  }, [load]);

  // Run a mutation, show feedback, then refresh every view.
  const run = async (action, successMessage) => {
    setBusy(true);
    try {
      await action();
      notify(successMessage);
      setModal(null);
      setRefreshKey((k) => k + 1);
      await load();
    } catch (err) {
      notify(err.message, 'error');
    } finally {
      setBusy(false);
    }
  };

  const changeStatus = (appt, status) =>
    run(() => api.updateAppointment(appt.id, { status }), `${appt.patient.full_name}: ${STATUS_LABELS[status]}`);

  const deleteAppointment = (appt) =>
    window.confirm(`Delete appointment for ${appt.patient.full_name}?`) &&
    run(() => api.deleteAppointment(appt.id), 'Appointment deleted');

  const meta = VIEWS[view];

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">✚</span>
          <div>
            <strong>ClinicFlow</strong>
            <span>Sunrise Family Clinic</span>
          </div>
        </div>
        <nav className="nav" aria-label="Main">
          {Object.entries(VIEWS).map(([key, v]) => (
            <button
              key={key}
              className={`nav-item ${view === key ? 'active' : ''}`}
              onClick={() => setView(key)}
              aria-current={view === key ? 'page' : undefined}
            >
              <span className="nav-icon" aria-hidden="true">
                {v.icon}
              </span>
              {v.label}
            </button>
          ))}
        </nav>
        <div className="pipeline" aria-label="Delivery pipeline">
          <span className="pipeline-title">Delivery pipeline</span>
          <ol>
            {PIPELINE.map((stage) => (
              <li key={stage}>{stage}</li>
            ))}
          </ol>
        </div>
        <footer className="build-info">
          <span>UI {FRONTEND_VERSION.slice(0, 7)}</span>
          <span>API {(backend.version || '—').slice(0, 7)}</span>
        </footer>
      </aside>

      <main className="main">
        <header className="topbar">
          <div>
            <h1>{meta.label}</h1>
            <p className="muted">{meta.subtitle}</p>
          </div>
          <div className="topbar-right">
            <span className={`health health-${backend.state}`} title={backend.error || 'Backend health'}>
              <span className="health-dot" />
              {backend.state === 'up' ? 'API online' : backend.state === 'down' ? 'API unreachable' : 'Connecting…'}
            </span>
            <time className="today">
              {new Date().toLocaleDateString([], { weekday: 'long', day: 'numeric', month: 'long' })}
            </time>
          </div>
        </header>

        {backend.state === 'down' && (
          <div className="banner error">
            Cannot reach the ClinicFlow API ({backend.error}). Check that the backend container/pod is running and
            that <code>/api</code> is routed to it.
            <button className="button small" onClick={load}>
              Retry
            </button>
          </div>
        )}

        {!stats && backend.state !== 'down' ? (
          <div className="loading">Loading clinic data…</div>
        ) : stats ? (
          <>
            {view === 'dashboard' && (
              <Dashboard
                stats={stats}
                today={today}
                doctors={doctors}
                onStatusChange={changeStatus}
                onBook={() => setModal('book')}
              />
            )}
            {view === 'appointments' && (
              <AppointmentsView
                doctors={doctors}
                refreshKey={refreshKey}
                onStatusChange={changeStatus}
                onDelete={deleteAppointment}
                onBook={() => setModal('book')}
                notify={notify}
              />
            )}
            {view === 'doctors' && (
              <DoctorsView
                doctors={doctors}
                onAdd={() => setModal('doctor')}
                onToggleActive={(d) =>
                  run(
                    () => api.updateDoctor(d.id, { is_active: !d.is_active }),
                    `${d.full_name} ${d.is_active ? 'deactivated' : 'activated'}`,
                  )
                }
                onDelete={(d) =>
                  window.confirm(`Delete ${d.full_name}?`) && run(() => api.deleteDoctor(d.id), 'Doctor removed')
                }
              />
            )}
            {view === 'patients' && (
              <PatientsView
                refreshKey={refreshKey}
                notify={notify}
                onAdd={() => setModal('patient')}
                onDelete={(p) =>
                  window.confirm(`Delete ${p.full_name} and all of their appointments?`) &&
                  run(() => api.deletePatient(p.id), 'Patient removed')
                }
              />
            )}
          </>
        ) : null}
      </main>

      {modal === 'book' && (
        <Modal title="Book appointment" onClose={() => setModal(null)}>
          <BookingForm
            doctors={doctors}
            patients={patients}
            busy={busy}
            onCancel={() => setModal(null)}
            onSubmit={(payload) => run(() => api.bookAppointment(payload), 'Appointment booked')}
          />
        </Modal>
      )}
      {modal === 'doctor' && (
        <Modal title="Add doctor" onClose={() => setModal(null)}>
          <DoctorForm
            busy={busy}
            onCancel={() => setModal(null)}
            onSubmit={(payload) => run(() => api.createDoctor(payload), 'Doctor added')}
          />
        </Modal>
      )}
      {modal === 'patient' && (
        <Modal title="Register patient" onClose={() => setModal(null)}>
          <PatientForm
            busy={busy}
            onCancel={() => setModal(null)}
            onSubmit={(payload) => run(() => api.createPatient(payload), 'Patient registered')}
          />
        </Modal>
      )}

      <Toasts toasts={toasts} onDismiss={(id) => setToasts((t) => t.filter((x) => x.id !== id))} />
    </div>
  );
}
