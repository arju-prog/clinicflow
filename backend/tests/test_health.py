def test_health_reports_up(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "UP"


def test_health_is_also_reachable_under_api_prefix(client):
    # The Ingress only forwards /api/* to the backend, so this is what external probes hit.
    assert client.get("/api/health").json()["status"] == "UP"


def test_ready_checks_database(client):
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "READY", "database": "ok"}


def test_root_describes_service(client):
    body = client.get("/").json()
    assert body["service"] == "ClinicFlow API"
    assert body["docs"] == "/docs"


def test_metrics_exposes_prometheus_format(client):
    client.get("/api/doctors")  # generate at least one instrumented request
    response = client.get("/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "http_requests_total" in response.text
    assert "clinicflow_appointments_booked_total" in response.text


def test_openapi_lists_all_resources(client):
    paths = client.get("/openapi.json").json()["paths"]
    for path in ("/api/doctors", "/api/patients", "/api/appointments", "/api/appointments/stats"):
        assert path in paths
