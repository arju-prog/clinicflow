from datetime import UTC, datetime, timedelta

from tests.conftest import future_slot


def test_book_appointment(client, make_doctor, make_patient, book):
    doctor, patient = make_doctor(full_name="Dr. Meena Pillai"), make_patient(full_name="Arjun Rao")

    response = book(doctor["id"], patient["id"], reason="Persistent cough", duration_minutes=20)

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "SCHEDULED"
    assert body["doctor"]["full_name"] == "Dr. Meena Pillai"
    assert body["patient"]["full_name"] == "Arjun Rao"
    start = datetime.fromisoformat(body["scheduled_at"])
    assert datetime.fromisoformat(body["ends_at"]) - start == timedelta(minutes=20)


def test_naive_datetime_is_treated_as_utc(client, make_doctor, make_patient, book):
    doctor, patient = make_doctor(), make_patient()
    response = book(doctor["id"], patient["id"], scheduled_at="2030-01-15T09:00:00")
    assert datetime.fromisoformat(response.json()["scheduled_at"]).utcoffset() == timedelta(0)


def test_doctor_cannot_be_double_booked(client, make_doctor, make_patient, book):
    doctor = make_doctor()
    first, second = make_patient(full_name="First"), make_patient(full_name="Second")

    assert book(doctor["id"], first["id"], scheduled_at=future_slot(hour=10)).status_code == 201
    clash = book(doctor["id"], second["id"], scheduled_at=future_slot(hour=10, minute=15))

    assert clash.status_code == 409
    assert "already has appointment" in clash.json()["detail"]


def test_back_to_back_slots_are_allowed(client, make_doctor, make_patient, book):
    doctor = make_doctor()
    a, b = make_patient(full_name="A Patient"), make_patient(full_name="B Patient")

    assert book(doctor["id"], a["id"], scheduled_at=future_slot(hour=10), duration_minutes=30).status_code == 201
    assert book(doctor["id"], b["id"], scheduled_at=future_slot(hour=10, minute=30)).status_code == 201


def test_patient_cannot_be_in_two_places_at_once(client, make_doctor, make_patient, book):
    patient = make_patient()
    one, two = make_doctor(), make_doctor()

    assert book(one["id"], patient["id"]).status_code == 201
    assert book(two["id"], patient["id"]).status_code == 409


def test_cancelled_appointment_frees_the_slot(client, make_doctor, make_patient, book):
    doctor = make_doctor()
    a, b = make_patient(full_name="A Patient"), make_patient(full_name="B Patient")
    first = book(doctor["id"], a["id"]).json()

    client.put(f"/api/appointments/{first['id']}", json={"status": "CANCELLED"})

    assert book(doctor["id"], b["id"]).status_code == 201


def test_inactive_doctor_cannot_be_booked(client, make_doctor, make_patient, book):
    doctor, patient = make_doctor(is_active=False), make_patient()
    response = book(doctor["id"], patient["id"])
    assert response.status_code == 409
    assert "not currently accepting" in response.json()["detail"]


def test_booking_unknown_patient_returns_404(client, make_doctor, book):
    doctor = make_doctor()
    assert book(doctor["id"], 4242).status_code == 404


def test_duration_must_be_within_limits(client, make_doctor, make_patient, book):
    doctor, patient = make_doctor(), make_patient()
    assert book(doctor["id"], patient["id"], duration_minutes=5).status_code == 422
    assert book(doctor["id"], patient["id"], duration_minutes=600).status_code == 422


def test_update_status_and_notes(client, make_doctor, make_patient, book):
    doctor, patient = make_doctor(), make_patient()
    appointment = book(doctor["id"], patient["id"]).json()

    response = client.put(
        f"/api/appointments/{appointment['id']}",
        json={"status": "COMPLETED", "notes": "Prescribed rest and fluids"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "COMPLETED"
    assert response.json()["notes"] == "Prescribed rest and fluids"


def test_reschedule_into_taken_slot_is_rejected(client, make_doctor, make_patient, book):
    doctor = make_doctor()
    a, b = make_patient(full_name="A Patient"), make_patient(full_name="B Patient")
    book(doctor["id"], a["id"], scheduled_at=future_slot(hour=9))
    movable = book(doctor["id"], b["id"], scheduled_at=future_slot(hour=11)).json()

    response = client.put(f"/api/appointments/{movable['id']}", json={"scheduled_at": future_slot(hour=9)})

    assert response.status_code == 409


def test_rescheduling_within_own_slot_is_allowed(client, make_doctor, make_patient, book):
    doctor, patient = make_doctor(), make_patient()
    appointment = book(doctor["id"], patient["id"], scheduled_at=future_slot(hour=9)).json()

    response = client.put(
        f"/api/appointments/{appointment['id']}", json={"scheduled_at": future_slot(hour=9, minute=10)}
    )

    assert response.status_code == 200


def test_invalid_status_is_rejected(client, make_doctor, make_patient, book):
    doctor, patient = make_doctor(), make_patient()
    appointment = book(doctor["id"], patient["id"]).json()
    response = client.put(f"/api/appointments/{appointment['id']}", json={"status": "TELEPORTED"})
    assert response.status_code == 422


def test_filter_appointments(client, make_doctor, make_patient, book):
    cardio, derm = make_doctor(specialty="Cardiology"), make_doctor(specialty="Dermatology")
    patient = make_patient()
    book(cardio["id"], patient["id"], scheduled_at=future_slot(days=1))
    later = book(derm["id"], patient["id"], scheduled_at=future_slot(days=3)).json()
    client.put(f"/api/appointments/{later['id']}", json={"status": "CANCELLED"})

    by_doctor = client.get("/api/appointments", params={"doctor_id": cardio["id"]}).json()
    by_status = client.get("/api/appointments", params={"status": "CANCELLED"}).json()
    by_range = client.get(
        "/api/appointments", params={"start": future_slot(days=2, hour=0), "end": future_slot(days=5, hour=0)}
    ).json()

    assert [a["doctor_id"] for a in by_doctor] == [cardio["id"]]
    assert [a["id"] for a in by_status] == [later["id"]]
    assert [a["id"] for a in by_range] == [later["id"]]


def test_delete_appointment(client, make_doctor, make_patient, book):
    doctor, patient = make_doctor(), make_patient()
    appointment = book(doctor["id"], patient["id"]).json()

    assert client.delete(f"/api/appointments/{appointment['id']}").status_code == 204
    assert client.get(f"/api/appointments/{appointment['id']}").status_code == 404
    assert client.delete(f"/api/appointments/{appointment['id']}").status_code == 404


def test_stats(client, make_doctor, make_patient, book):
    doctor, patient = make_doctor(), make_patient()
    make_doctor(is_active=False)
    now = datetime.now(UTC)

    done = book(doctor["id"], patient["id"], scheduled_at=(now - timedelta(hours=3)).isoformat()).json()
    missed = book(doctor["id"], patient["id"], scheduled_at=(now - timedelta(hours=2)).isoformat()).json()
    book(doctor["id"], patient["id"], scheduled_at=(now + timedelta(days=2)).isoformat())
    client.put(f"/api/appointments/{done['id']}", json={"status": "COMPLETED"})
    client.put(f"/api/appointments/{missed['id']}", json={"status": "NO_SHOW"})

    stats = client.get(
        "/api/appointments/stats",
        params={
            "day_start": (now - timedelta(hours=12)).isoformat(),
            "day_end": (now + timedelta(hours=12)).isoformat(),
        },
    ).json()

    assert stats["total"] == 3
    assert stats["upcoming"] == 1
    assert stats["today"] == 1  # the no-show doesn't count as an active appointment
    assert stats["by_status"]["COMPLETED"] == 1
    assert stats["by_status"]["NO_SHOW"] == 1
    assert stats["active_doctors"] == 1
    assert stats["patients"] == 1
    assert stats["attendance_rate"] == 50.0
