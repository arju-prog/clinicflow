"""Business metrics exposed on /metrics next to the default HTTP metrics.

HTTP request count/latency are added automatically by prometheus-fastapi-instrumentator;
these counters answer clinic-level questions in Grafana ("how many bookings per minute?",
"how often do receptionists hit a double-booking?").
"""

from prometheus_client import Counter

APPOINTMENTS_BOOKED = Counter(
    "clinicflow_appointments_booked_total",
    "Appointments successfully booked",
    ["specialty"],
)

BOOKING_CONFLICTS = Counter(
    "clinicflow_booking_conflicts_total",
    "Booking attempts rejected because the doctor or patient was already booked",
    ["kind"],
)

STATUS_CHANGES = Counter(
    "clinicflow_appointment_status_changes_total",
    "Appointment status transitions",
    ["status"],
)
