from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..metrics import APPOINTMENTS_BOOKED, STATUS_CHANGES
from ..models import INACTIVE_STATUSES, Appointment, AppointmentStatus, Doctor, Patient, as_utc
from ..schemas import AppointmentCreate, AppointmentOut, AppointmentUpdate, StatsOut, Status
from ..services import ensure_doctor_bookable, ensure_no_conflict, get_or_404

router = APIRouter(prefix="/api/appointments", tags=["appointments"])


def _today_bounds(start: datetime | None, end: datetime | None) -> tuple[datetime, datetime]:
    # The browser passes its own local-day bounds so "today" matches the clinic's timezone.
    if start and end:
        return as_utc(start), as_utc(end)
    midnight = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    return midnight, midnight + timedelta(days=1)


@router.get("", response_model=list[AppointmentOut])
def list_appointments(
    status_filter: Status | None = Query(default=None, alias="status"),
    doctor_id: int | None = None,
    patient_id: int | None = None,
    start: datetime | None = Query(default=None, description="Only appointments at or after this time"),
    end: datetime | None = Query(default=None, description="Only appointments before this time"),
    db: Session = Depends(get_db),
):
    stmt = select(Appointment).order_by(Appointment.scheduled_at)
    if status_filter:
        stmt = stmt.where(Appointment.status == status_filter)
    if doctor_id:
        stmt = stmt.where(Appointment.doctor_id == doctor_id)
    if patient_id:
        stmt = stmt.where(Appointment.patient_id == patient_id)
    if start:
        stmt = stmt.where(Appointment.scheduled_at >= as_utc(start))
    if end:
        stmt = stmt.where(Appointment.scheduled_at < as_utc(end))
    return list(db.scalars(stmt).unique())


# Declared before /{appointment_id} so "stats" is not parsed as an id.
@router.get("/stats", response_model=StatsOut)
def appointment_stats(
    day_start: datetime | None = None,
    day_end: datetime | None = None,
    db: Session = Depends(get_db),
):
    rows = db.execute(select(Appointment.status, func.count(Appointment.id)).group_by(Appointment.status)).all()
    by_status = {s.value: 0 for s in AppointmentStatus} | {s: c for s, c in rows}

    start, end = _today_bounds(day_start, day_end)
    today = db.scalar(
        select(func.count(Appointment.id)).where(
            Appointment.scheduled_at >= start,
            Appointment.scheduled_at < end,
            Appointment.status.not_in(INACTIVE_STATUSES),
        )
    )
    upcoming = db.scalar(
        select(func.count(Appointment.id)).where(
            Appointment.scheduled_at >= datetime.now(UTC),
            Appointment.status == AppointmentStatus.SCHEDULED.value,
        )
    )
    completed, no_show = by_status["COMPLETED"], by_status["NO_SHOW"]
    attended = completed + no_show

    return StatsOut(
        total=sum(by_status.values()),
        today=today or 0,
        upcoming=upcoming or 0,
        by_status=by_status,
        active_doctors=db.scalar(select(func.count(Doctor.id)).where(Doctor.is_active.is_(True))) or 0,
        patients=db.scalar(select(func.count(Patient.id))) or 0,
        attendance_rate=round(100 * completed / attended, 1) if attended else 0.0,
    )


@router.get("/{appointment_id}", response_model=AppointmentOut)
def get_appointment(appointment_id: int, db: Session = Depends(get_db)):
    return get_or_404(db, Appointment, appointment_id, "Appointment")


@router.post("", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED)
def book_appointment(payload: AppointmentCreate, db: Session = Depends(get_db)):
    doctor = get_or_404(db, Doctor, payload.doctor_id, "Doctor")
    patient = get_or_404(db, Patient, payload.patient_id, "Patient")
    ensure_doctor_bookable(doctor)
    ensure_no_conflict(
        db, doctor=doctor, patient=patient, start=payload.scheduled_at, duration_minutes=payload.duration_minutes
    )

    appointment = Appointment(**payload.model_dump())
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    APPOINTMENTS_BOOKED.labels(specialty=doctor.specialty).inc()
    return appointment


@router.put("/{appointment_id}", response_model=AppointmentOut)
def update_appointment(appointment_id: int, payload: AppointmentUpdate, db: Session = Depends(get_db)):
    appointment = get_or_404(db, Appointment, appointment_id, "Appointment")
    changes = payload.model_dump(exclude_unset=True)

    doctor = appointment.doctor
    if "doctor_id" in changes and changes["doctor_id"] != appointment.doctor_id:
        doctor = get_or_404(db, Doctor, changes["doctor_id"], "Doctor")
        ensure_doctor_bookable(doctor)

    new_status = changes.get("status", appointment.status)
    slot_changed = any(k in changes for k in ("doctor_id", "scheduled_at", "duration_minutes"))
    reactivated = appointment.status in INACTIVE_STATUSES and new_status not in INACTIVE_STATUSES
    if new_status not in INACTIVE_STATUSES and (slot_changed or reactivated):
        ensure_no_conflict(
            db,
            doctor=doctor,
            patient=appointment.patient,
            start=changes.get("scheduled_at", appointment.scheduled_at),
            duration_minutes=changes.get("duration_minutes", appointment.duration_minutes),
            exclude_id=appointment.id,
        )

    if new_status != appointment.status:
        STATUS_CHANGES.labels(status=new_status).inc()
    for key, value in changes.items():
        setattr(appointment, key, value)
    db.commit()
    db.refresh(appointment)
    return appointment


@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_appointment(appointment_id: int, db: Session = Depends(get_db)):
    appointment = get_or_404(db, Appointment, appointment_id, "Appointment")
    db.delete(appointment)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
