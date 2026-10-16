import { useEffect, useState } from 'react';
import { api } from '../api.js';
import { age } from '../format.js';
import { Avatar, EmptyState } from './ui.jsx';

export function DoctorsView({ doctors, onAdd, onToggleActive, onDelete }) {
  if (!doctors.length) {
    return <EmptyState title="No doctors yet" action={<button className="button primary" onClick={onAdd}>+ Add doctor</button>} />;
  }
  return (
    <>
      <div className="section-actions">
        <button className="button primary" onClick={onAdd}>
          + Add doctor
        </button>
      </div>
      <div className="doctor-grid">
        {doctors.map((d) => (
          <article key={d.id} className={`card doctor-card ${d.is_active ? '' : 'inactive'}`}>
            <div className="doctor-head">
              <Avatar name={d.full_name} tone="indigo" />
              <div>
                <h3>{d.full_name}</h3>
                <p className="muted">{d.specialty}</p>
              </div>
            </div>
            <dl className="meta">
              <div>
                <dt>Room</dt>
                <dd>{d.room || '—'}</dd>
              </div>
              <div>
                <dt>Email</dt>
                <dd>{d.email}</dd>
              </div>
              <div>
                <dt>Status</dt>
                <dd className={d.is_active ? 'text-green' : 'muted'}>{d.is_active ? 'Accepting patients' : 'Inactive'}</dd>
              </div>
            </dl>
            <footer className="card-footer">
              <button className="button small" onClick={() => onToggleActive(d)}>
                {d.is_active ? 'Deactivate' : 'Activate'}
              </button>
              <button className="button small danger" onClick={() => onDelete(d)}>
                Delete
              </button>
            </footer>
          </article>
        ))}
      </div>
    </>
  );
}

export function PatientsView({ refreshKey, onAdd, onDelete, notify }) {
  const [query, setQuery] = useState('');
  const [patients, setPatients] = useState(null);

  useEffect(() => {
    let cancelled = false;
    const timer = setTimeout(() => {
      api
        .listPatients(query)
        .then((data) => !cancelled && setPatients(data))
        .catch((err) => notify(err.message, 'error'));
    }, 200); // debounce typing
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [query, refreshKey, notify]);

  return (
    <section className="card">
      <header className="card-header wrap">
        <input
          className="search"
          type="search"
          placeholder="Search patients by name or phone…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          aria-label="Search patients"
        />
        <button className="button primary" onClick={onAdd}>
          + Register patient
        </button>
      </header>
      {patients === null ? (
        <div className="skeleton-table" aria-busy="true" />
      ) : patients.length === 0 ? (
        <EmptyState title="No patients found" hint={query ? 'Try another search.' : 'Register the first patient.'} />
      ) : (
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Patient</th>
                <th>Age</th>
                <th>Phone</th>
                <th>Notes</th>
                <th aria-label="Actions" />
              </tr>
            </thead>
            <tbody>
              {patients.map((p) => (
                <tr key={p.id}>
                  <td data-label="Patient">
                    <div className="person">
                      <Avatar name={p.full_name} tone="rose" />
                      <div>
                        {p.full_name}
                        <span className="muted block">{p.email || p.gender.toLowerCase()}</span>
                      </div>
                    </div>
                  </td>
                  <td data-label="Age">{age(p.date_of_birth)}</td>
                  <td data-label="Phone">{p.phone}</td>
                  <td data-label="Notes" className="muted">
                    {p.notes || '—'}
                  </td>
                  <td className="row-actions">
                    <button className="button small danger" onClick={() => onDelete(p)}>
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
