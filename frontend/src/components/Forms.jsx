import { useState } from 'react';
import { nextQuarterHourLocal } from '../format.js';
import { Field } from './ui.jsx';

function useForm(initial) {
  const [values, setValues] = useState(initial);
  const bind = (name) => ({
    name,
    value: values[name],
    onChange: (e) =>
      setValues((v) => ({ ...v, [name]: e.target.type === 'checkbox' ? e.target.checked : e.target.value })),
  });
  return [values, bind];
}

function FormActions({ busy, submitLabel, onCancel }) {
  return (
    <footer className="modal-footer">
      <button type="button" className="button ghost" onClick={onCancel}>
        Cancel
      </button>
      <button type="submit" className="button primary" disabled={busy}>
        {busy ? 'Saving…' : submitLabel}
      </button>
    </footer>
  );
}

export function BookingForm({ doctors, patients, onSubmit, onCancel, busy }) {
  const activeDoctors = doctors.filter((d) => d.is_active);
  const [values, bind] = useForm({
    patient_id: patients[0]?.id ?? '',
    doctor_id: activeDoctors[0]?.id ?? '',
    scheduled_at: nextQuarterHourLocal(),
    duration_minutes: 30,
    reason: '',
    notes: '',
  });

  const submit = (e) => {
    e.preventDefault();
    onSubmit({
      ...values,
      patient_id: Number(values.patient_id),
      doctor_id: Number(values.doctor_id),
      duration_minutes: Number(values.duration_minutes),
      // datetime-local is wall-clock time; convert to an absolute UTC instant for the API.
      scheduled_at: new Date(values.scheduled_at).toISOString(),
    });
  };

  if (!patients.length || !activeDoctors.length) {
    return (
      <div className="modal-body">
        <p>You need at least one patient and one active doctor before booking an appointment.</p>
      </div>
    );
  }

  return (
    <form onSubmit={submit}>
      <div className="modal-body form-grid">
        <Field label="Patient">
          <select {...bind('patient_id')} required>
            {patients.map((p) => (
              <option key={p.id} value={p.id}>
                {p.full_name} · {p.phone}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Doctor">
          <select {...bind('doctor_id')} required>
            {activeDoctors.map((d) => (
              <option key={d.id} value={d.id}>
                {d.full_name} · {d.specialty}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Date & time">
          <input type="datetime-local" step="900" {...bind('scheduled_at')} required />
        </Field>
        <Field label="Duration">
          <select {...bind('duration_minutes')}>
            {[15, 20, 30, 45, 60, 90].map((m) => (
              <option key={m} value={m}>
                {m} minutes
              </option>
            ))}
          </select>
        </Field>
        <Field label="Reason for visit" wide>
          <input {...bind('reason')} placeholder="e.g. Follow-up: blood pressure" minLength={3} required />
        </Field>
        <Field label="Notes (optional)" wide>
          <textarea rows={2} {...bind('notes')} />
        </Field>
      </div>
      <FormActions busy={busy} submitLabel="Book appointment" onCancel={onCancel} />
    </form>
  );
}

export function DoctorForm({ onSubmit, onCancel, busy }) {
  const [values, bind] = useForm({ full_name: 'Dr. ', specialty: '', email: '', phone: '', room: '' });
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit(values);
      }}
    >
      <div className="modal-body form-grid">
        <Field label="Full name" wide>
          <input {...bind('full_name')} required minLength={2} />
        </Field>
        <Field label="Specialty">
          <input {...bind('specialty')} list="specialties" required />
          <datalist id="specialties">
            {['General Medicine', 'Cardiology', 'Pediatrics', 'Dermatology', 'Orthopedics', 'ENT', 'Gynecology'].map(
              (s) => (
                <option key={s} value={s} />
              ),
            )}
          </datalist>
        </Field>
        <Field label="Room">
          <input {...bind('room')} placeholder="e.g. 204" />
        </Field>
        <Field label="Email">
          <input type="email" {...bind('email')} required />
        </Field>
        <Field label="Phone">
          <input type="tel" {...bind('phone')} />
        </Field>
      </div>
      <FormActions busy={busy} submitLabel="Add doctor" onCancel={onCancel} />
    </form>
  );
}

export function PatientForm({ onSubmit, onCancel, busy }) {
  const [values, bind] = useForm({
    full_name: '',
    date_of_birth: '',
    gender: 'UNDISCLOSED',
    phone: '',
    email: '',
    notes: '',
  });
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit({ ...values, email: values.email || null });
      }}
    >
      <div className="modal-body form-grid">
        <Field label="Full name" wide>
          <input {...bind('full_name')} required minLength={2} />
        </Field>
        <Field label="Date of birth">
          <input type="date" {...bind('date_of_birth')} max={new Date().toISOString().slice(0, 10)} required />
        </Field>
        <Field label="Gender">
          <select {...bind('gender')}>
            <option value="FEMALE">Female</option>
            <option value="MALE">Male</option>
            <option value="OTHER">Other</option>
            <option value="UNDISCLOSED">Prefer not to say</option>
          </select>
        </Field>
        <Field label="Phone">
          <input type="tel" {...bind('phone')} placeholder="+91 98xxx xxxxx" required />
        </Field>
        <Field label="Email (optional)">
          <input type="email" {...bind('email')} />
        </Field>
        <Field label="Medical notes (optional)" wide>
          <textarea rows={2} {...bind('notes')} placeholder="Allergies, chronic conditions…" />
        </Field>
      </div>
      <FormActions busy={busy} submitLabel="Register patient" onCancel={onCancel} />
    </form>
  );
}
