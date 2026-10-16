"""Demo data so a fresh environment shows a populated dashboard.

Runs on startup when SEED_DEMO_DATA=true and the database has no doctors yet.
Also runnable by hand:  python -m app.seed
"""

import logging
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from .db import SessionLocal
from .models import Appointment, Doctor, Patient

log = logging.getLogger(__name__)

DOCTORS = [
    ("Dr. Ananya Rao", "General Medicine", "ananya.rao@clinicflow.dev", "101"),
    ("Dr. Vikram Mehta", "Cardiology", "vikram.mehta@clinicflow.dev", "204"),
    ("Dr. Sara Thomas", "Pediatrics", "sara.thomas@clinicflow.dev", "112"),
    ("Dr. Imran Qureshi", "Dermatology", "imran.qureshi@clinicflow.dev", "309"),
]

PATIENTS = [
    ("Rohan Kapoor", date(1988, 4, 12), "MALE", "+91 98100 11223"),
    ("Meera Iyer", date(1995, 9, 3), "FEMALE", "+91 98200 33445"),
    ("Aarav Singh", date(2017, 1, 22), "MALE", "+91 98300 55667"),
    ("Fatima Sheikh", date(1972, 11, 30), "FEMALE", "+91 98400 77889"),
    ("Kabir Malhotra", date(2001, 6, 15), "MALE", "+91 98500 99001"),
    ("Priya Nair", date(1990, 2, 8), "FEMALE", "+91 98600 12121"),
]

# (patient index, doctor index, day offset, hour, minute, reason, status)
APPOINTMENTS = [
    (0, 0, 0, 9, 0, "Annual health check-up", "COMPLETED"),
    (3, 1, 0, 9, 30, "Follow-up: blood pressure", "COMPLETED"),
    (2, 2, 0, 10, 0, "Vaccination - booster", "CHECKED_IN"),
    (1, 3, 0, 11, 0, "Skin rash consultation", "SCHEDULED"),
    (4, 0, 0, 12, 0, "Fever and sore throat", "SCHEDULED"),
    (5, 1, 0, 14, 30, "ECG review", "SCHEDULED"),
    (0, 3, -1, 16, 0, "Acne treatment review", "NO_SHOW"),
    (3, 0, -1, 10, 0, "Diabetes medication review", "COMPLETED"),
    (1, 0, 1, 9, 30, "Migraine consultation", "SCHEDULED"),
    (2, 2, 1, 11, 0, "Growth & nutrition check", "SCHEDULED"),
    (5, 1, 2, 15, 0, "Stress test", "SCHEDULED"),
    (4, 3, 3, 13, 0, "Mole check", "CANCELLED"),
]


def seed_if_empty() -> bool:
    with SessionLocal() as db:
        if db.scalar(select(func.count(Doctor.id))):
            return False

        doctors = [
            Doctor(full_name=n, specialty=s, email=e, room=r, phone="+91 80 4000 1000") for n, s, e, r in DOCTORS
        ]
        patients = [Patient(full_name=n, date_of_birth=d, gender=g, phone=p) for n, d, g, p in PATIENTS]
        db.add_all(doctors + patients)

        today = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        for p, d, offset, hour, minute, reason, status in APPOINTMENTS:
            db.add(
                Appointment(
                    patient=patients[p],
                    doctor=doctors[d],
                    scheduled_at=today + timedelta(days=offset, hours=hour, minutes=minute),
                    reason=reason,
                    status=status,
                )
            )
        try:
            db.commit()
        except IntegrityError:
            # Another replica seeded at the same moment; their data wins.
            db.rollback()
            return False
    log.info(
        "Seeded demo data: %d doctors, %d patients, %d appointments", len(DOCTORS), len(PATIENTS), len(APPOINTMENTS)
    )
    return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("seeded" if seed_if_empty() else "database already has data; nothing to do")
