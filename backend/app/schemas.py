from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .models import as_utc

Status = Literal["SCHEDULED", "CHECKED_IN", "COMPLETED", "CANCELLED", "NO_SHOW"]
Gender = Literal["FEMALE", "MALE", "OTHER", "UNDISCLOSED"]

EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
PHONE_PATTERN = r"^\+?[0-9 ()-]{7,20}$"


def _dob_not_in_future(value: date | None) -> date | None:
    if value is not None and value > date.today():
        raise ValueError("date_of_birth cannot be in the future")
    return value


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------- Doctors ----------


class DoctorCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    specialty: str = Field(min_length=2, max_length=80)
    email: str = Field(pattern=EMAIL_PATTERN, max_length=160)
    phone: str = Field(default="", max_length=30)
    room: str = Field(default="", max_length=20)
    is_active: bool = True


class DoctorUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    specialty: str | None = Field(default=None, min_length=2, max_length=80)
    email: str | None = Field(default=None, pattern=EMAIL_PATTERN, max_length=160)
    phone: str | None = Field(default=None, max_length=30)
    room: str | None = Field(default=None, max_length=20)
    is_active: bool | None = None


class DoctorOut(DoctorCreate, ORMModel):
    id: int
    created_at: datetime


class DoctorSummary(ORMModel):
    id: int
    full_name: str
    specialty: str
    room: str


# ---------- Patients ----------


class PatientCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    date_of_birth: date
    gender: Gender = "UNDISCLOSED"
    phone: str = Field(pattern=PHONE_PATTERN)
    email: str | None = Field(default=None, pattern=EMAIL_PATTERN, max_length=160)
    notes: str = Field(default="", max_length=2000)

    _dob = field_validator("date_of_birth")(_dob_not_in_future)


class PatientUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    date_of_birth: date | None = None
    gender: Gender | None = None
    phone: str | None = Field(default=None, pattern=PHONE_PATTERN)
    email: str | None = Field(default=None, pattern=EMAIL_PATTERN, max_length=160)
    notes: str | None = Field(default=None, max_length=2000)

    _dob = field_validator("date_of_birth")(_dob_not_in_future)


class PatientOut(PatientCreate, ORMModel):
    id: int
    created_at: datetime


class PatientSummary(ORMModel):
    id: int
    full_name: str
    phone: str


# ---------- Appointments ----------


def _to_utc(value: datetime | None) -> datetime | None:
    return as_utc(value) if value is not None else None


class AppointmentCreate(BaseModel):
    patient_id: int
    doctor_id: int
    scheduled_at: datetime
    duration_minutes: int = Field(default=30, ge=10, le=240)
    reason: str = Field(min_length=3, max_length=255)
    notes: str = Field(default="", max_length=2000)

    _utc = field_validator("scheduled_at")(_to_utc)


class AppointmentUpdate(BaseModel):
    doctor_id: int | None = None
    scheduled_at: datetime | None = None
    duration_minutes: int | None = Field(default=None, ge=10, le=240)
    reason: str | None = Field(default=None, min_length=3, max_length=255)
    notes: str | None = Field(default=None, max_length=2000)
    status: Status | None = None

    _utc = field_validator("scheduled_at")(_to_utc)


class AppointmentOut(ORMModel):
    id: int
    patient_id: int
    doctor_id: int
    scheduled_at: datetime
    ends_at: datetime
    duration_minutes: int
    reason: str
    notes: str
    status: Status
    created_at: datetime
    updated_at: datetime
    doctor: DoctorSummary
    patient: PatientSummary

    _utc = field_validator("scheduled_at", "ends_at", "created_at", "updated_at")(_to_utc)


class StatsOut(BaseModel):
    total: int
    today: int
    upcoming: int
    by_status: dict[str, int]
    active_doctors: int
    patients: int
    attendance_rate: float = Field(description="Completed / (completed + no-show), as a percentage")
