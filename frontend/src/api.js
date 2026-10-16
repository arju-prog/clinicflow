// All calls are relative ("/api/..."), so the browser never needs the backend's hostname.
// Nginx (Docker Compose) or the Kubernetes Ingress routes /api to FastAPI.

export class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

function describeValidation(detail) {
  // FastAPI 422 bodies: [{loc: ["body", "phone"], msg: "..."}]
  return detail
    .map((d) => `${d.loc?.slice(-1)[0] ?? 'field'}: ${d.msg}`)
    .join('; ');
}

async function request(path, { method = 'GET', body, params } = {}) {
  const query = params
    ? '?' +
      new URLSearchParams(
        Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== ''),
      ).toString()
    : '';

  const response = await fetch(`/api${path}${query}`, {
    method,
    headers: body ? { 'Content-Type': 'application/json' } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (response.status === 204) return null;

  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = data?.detail;
    const message = Array.isArray(detail)
      ? describeValidation(detail)
      : detail || `Request failed (${response.status})`;
    throw new ApiError(response.status, message);
  }
  return data;
}

export const api = {
  health: () => request('/health'),

  stats: (dayStart, dayEnd) =>
    request('/appointments/stats', { params: { day_start: dayStart, day_end: dayEnd } }),

  listAppointments: (params) => request('/appointments', { params }),
  bookAppointment: (payload) => request('/appointments', { method: 'POST', body: payload }),
  updateAppointment: (id, payload) => request(`/appointments/${id}`, { method: 'PUT', body: payload }),
  deleteAppointment: (id) => request(`/appointments/${id}`, { method: 'DELETE' }),

  listDoctors: (params) => request('/doctors', { params }),
  createDoctor: (payload) => request('/doctors', { method: 'POST', body: payload }),
  updateDoctor: (id, payload) => request(`/doctors/${id}`, { method: 'PUT', body: payload }),
  deleteDoctor: (id) => request(`/doctors/${id}`, { method: 'DELETE' }),

  listPatients: (q) => request('/patients', { params: { q } }),
  createPatient: (payload) => request('/patients', { method: 'POST', body: payload }),
  updatePatient: (id, payload) => request(`/patients/${id}`, { method: 'PUT', body: payload }),
  deletePatient: (id) => request(`/patients/${id}`, { method: 'DELETE' }),
};
