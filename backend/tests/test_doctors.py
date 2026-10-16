def test_create_and_get_doctor(client, make_doctor):
    doctor = make_doctor(full_name="Dr. Asha Verma", specialty="Cardiology")
    assert doctor["id"] > 0
    assert doctor["is_active"] is True

    fetched = client.get(f"/api/doctors/{doctor['id']}").json()
    assert fetched["full_name"] == "Dr. Asha Verma"
    assert fetched["specialty"] == "Cardiology"


def test_list_doctors_filters_by_active(client, make_doctor):
    make_doctor()
    inactive = make_doctor(is_active=False)

    all_doctors = client.get("/api/doctors").json()
    active_only = client.get("/api/doctors", params={"active": True}).json()

    assert len(all_doctors) == 2
    assert inactive["id"] not in [d["id"] for d in active_only]


def test_duplicate_email_is_rejected(client, make_doctor):
    make_doctor(email="same@clinic.test")
    response = client.post(
        "/api/doctors",
        json={"full_name": "Dr. Copy", "specialty": "ENT", "email": "same@clinic.test"},
    )
    assert response.status_code == 409


def test_invalid_email_fails_validation(client):
    response = client.post("/api/doctors", json={"full_name": "Dr. X", "specialty": "ENT", "email": "nope"})
    assert response.status_code == 422


def test_update_doctor(client, make_doctor):
    doctor = make_doctor()
    response = client.put(f"/api/doctors/{doctor['id']}", json={"room": "305", "is_active": False})
    assert response.status_code == 200
    assert response.json()["room"] == "305"
    assert response.json()["is_active"] is False


def test_get_unknown_doctor_returns_404(client):
    assert client.get("/api/doctors/9999").status_code == 404


def test_delete_doctor_without_history(client, make_doctor):
    doctor = make_doctor()
    assert client.delete(f"/api/doctors/{doctor['id']}").status_code == 204
    assert client.get(f"/api/doctors/{doctor['id']}").status_code == 404


def test_cannot_delete_doctor_with_appointments(client, make_doctor, make_patient, book):
    doctor, patient = make_doctor(), make_patient()
    assert book(doctor["id"], patient["id"]).status_code == 201

    response = client.delete(f"/api/doctors/{doctor['id']}")
    assert response.status_code == 409
    assert "deactivate" in response.json()["detail"]
