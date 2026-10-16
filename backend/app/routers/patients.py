from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Patient
from ..schemas import PatientCreate, PatientOut, PatientUpdate
from ..services import get_or_404

router = APIRouter(prefix="/api/patients", tags=["patients"])


@router.get("", response_model=list[PatientOut])
def list_patients(
    q: str | None = Query(default=None, description="Search by name or phone"),
    db: Session = Depends(get_db),
):
    stmt = select(Patient).order_by(Patient.full_name)
    if q:
        pattern = f"%{q.strip()}%"
        stmt = stmt.where(or_(Patient.full_name.ilike(pattern), Patient.phone.ilike(pattern)))
    return list(db.scalars(stmt))


@router.get("/{patient_id}", response_model=PatientOut)
def get_patient(patient_id: int, db: Session = Depends(get_db)):
    return get_or_404(db, Patient, patient_id, "Patient")


@router.post("", response_model=PatientOut, status_code=status.HTTP_201_CREATED)
def create_patient(payload: PatientCreate, db: Session = Depends(get_db)):
    patient = Patient(**payload.model_dump())
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


@router.put("/{patient_id}", response_model=PatientOut)
def update_patient(patient_id: int, payload: PatientUpdate, db: Session = Depends(get_db)):
    patient = get_or_404(db, Patient, patient_id, "Patient")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(patient, key, value)
    db.commit()
    db.refresh(patient)
    return patient


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_patient(patient_id: int, db: Session = Depends(get_db)):
    """Deleting a patient also removes their appointment history (ORM cascade)."""
    patient = get_or_404(db, Patient, patient_id, "Patient")
    db.delete(patient)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
