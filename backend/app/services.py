from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .metrics import BOOKING_CONFLICTS
from .models import INACTIVE_STATUSES, Appointment, Doctor, Patient, as_utc

# Longest allowed appointment; bounds how far back we look for overlapping slots.
MAX_DURATION = timedelta(minutes=240)


def get_or_404(db: Session, model: type, obj_id: int, label: str):
    obj = db.get(model, obj_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{label} {obj_id} not found")
    return obj


def ensure_doctor_bookable(doctor: Doctor) -> None:
    if not doctor.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{doctor.full_name} is not currently accepting appointments",
        )


def _overlapping(db: Session, column, value: int, start: datetime, end: datetime, exclude_id: int | None):
    # Narrow in SQL, then do the exact interval check in Python so it behaves the same
    # on PostgreSQL and on the SQLite database used by the tests.
    stmt = select(Appointment).where(
        column == value,
        Appointment.status.not_in(INACTIVE_STATUSES),
        Appointment.scheduled_at < end,
        Appointment.scheduled_at > start - MAX_DURATION,
    )
    for appt in db.scalars(stmt).unique():
        if appt.id != exclude_id and appt.ends_at > start:
            return appt
    return None


def ensure_no_conflict(
    db: Session,
    *,
    doctor: Doctor,
    patient: Patient,
    start: datetime,
    duration_minutes: int,
    exclude_id: int | None = None,
) -> None:
    start = as_utc(start)
    end = start + timedelta(minutes=duration_minutes)

    clash = _overlapping(db, Appointment.doctor_id, doctor.id, start, end, exclude_id)
    if clash:
        BOOKING_CONFLICTS.labels(kind="doctor").inc()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{doctor.full_name} already has appointment #{clash.id} at "
            f"{as_utc(clash.scheduled_at):%Y-%m-%d %H:%M} UTC",
        )

    clash = _overlapping(db, Appointment.patient_id, patient.id, start, end, exclude_id)
    if clash:
        BOOKING_CONFLICTS.labels(kind="patient").inc()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{patient.full_name} already has appointment #{clash.id} at that time",
        )
