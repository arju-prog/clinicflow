from datetime import date, timedelta


def test_create_patient(client, make_patient):
    patient = make_patient(full_name="Ravi Kumar")
    assert patient["full_name"] == "Ravi Kumar"
    assert patient["gender"] == "FEMALE"


def test_search_patients_by_name_and_phone(client, make_patient):
    make_patient(full_name="Ravi Kumar", phone="+91 90000 00001")
    make_patient(full_name="Sunita Das", phone="+91 90000 00002")

    by_name = client.get("/api/patients", params={"q": "ravi"}).json()
    by_phone = client.get("/api/patients", params={"q": "00002"}).json()

    assert [p["full_name"] for p in by_name] == ["Ravi Kumar"]
    assert [p["full_name"] for p in by_phone] == ["Sunita Das"]


def test_date_of_birth_cannot_be_in_future(client):
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    response = client.post(
        "/api/patients",
        json={"full_name": "Time Traveller", "date_of_birth": tomorrow, "phone": "+91 90000 00003"},
    )
    assert response.status_code == 422


def test_invalid_phone_is_rejected(client):
    response = client.post(
        "/api/patients", json={"full_name": "No Phone", "date_of_birth": "2000-01-01", "phone": "abc"}
    )
    assert response.status_code == 422


def test_update_patient(client, make_patient):
    patient = make_patient()
    response = client.put(f"/api/patients/{patient['id']}", json={"notes": "Allergic to penicillin"})
    assert response.status_code == 200
    assert response.json()["notes"] == "Allergic to penicillin"


def test_deleting_patient_removes_their_appointments(client, make_doctor, make_patient, book):
    doctor, patient = make_doctor(), make_patient()
    appointment = book(doctor["id"], patient["id"]).json()

    assert client.delete(f"/api/patients/{patient['id']}").status_code == 204
    assert client.get(f"/api/appointments/{appointment['id']}").status_code == 404
