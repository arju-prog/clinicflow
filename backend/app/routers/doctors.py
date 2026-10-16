from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Appointment, Doctor
from ..schemas import DoctorCreate, DoctorOut, DoctorUpdate
from ..services import get_or_404

router = APIRouter(prefix="/api/doctors", tags=["doctors"])


def _email_taken(db: Session, email: str, exclude_id: int | None = None) -> bool:
    existing = db.scalar(select(Doctor).where(Doctor.email == email))
    return existing is not None and existing.id != exclude_id


def _commit(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="A doctor with this email already exists"
        ) from None


@router.get("", response_model=list[DoctorOut])
def list_doctors(active: bool | None = None, db: Session = Depends(get_db)):
    stmt = select(Doctor).order_by(Doctor.full_name)
    if active is not None:
        stmt = stmt.where(Doctor.is_active == active)
    return list(db.scalars(stmt))


@router.get("/{doctor_id}", response_model=DoctorOut)
def get_doctor(doctor_id: int, db: Session = Depends(get_db)):
    return get_or_404(db, Doctor, doctor_id, "Doctor")


@router.post("", response_model=DoctorOut, status_code=status.HTTP_201_CREATED)
def create_doctor(payload: DoctorCreate, db: Session = Depends(get_db)):
    if _email_taken(db, payload.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A doctor with this email already exists")
    doctor = Doctor(**payload.model_dump())
    db.add(doctor)
    _commit(db)
    db.refresh(doctor)
    return doctor


@router.put("/{doctor_id}", response_model=DoctorOut)
def update_doctor(doctor_id: int, payload: DoctorUpdate, db: Session = Depends(get_db)):
    doctor = get_or_404(db, Doctor, doctor_id, "Doctor")
    changes = payload.model_dump(exclude_unset=True)
    if "email" in changes and _email_taken(db, changes["email"], exclude_id=doctor_id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A doctor with this email already exists")
    for key, value in changes.items():
        setattr(doctor, key, value)
    _commit(db)
    db.refresh(doctor)
    return doctor


@router.delete("/{doctor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_doctor(doctor_id: int, db: Session = Depends(get_db)):
    doctor = get_or_404(db, Doctor, doctor_id, "Doctor")
    if db.scalar(select(Appointment.id).where(Appointment.doctor_id == doctor_id).limit(1)) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Doctor has appointment history; deactivate them instead of deleting",
        )
    db.delete(doctor)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
