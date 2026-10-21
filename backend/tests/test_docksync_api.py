import os
import uuid

import pytest
import requests


BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://portaria-agenda.preview.emergentagent.com").rstrip("/")
EMAIL = "admin@docksync.local"
PASSWORD = "DockSync123!"


@pytest.fixture
def client():
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


def test_public_list_and_filters(client):
    response = client.get(f"{BASE_URL}/api/appointments", params={"start": "2026-10-21"})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list) and len(data) >= 2
    assert all("id" in item and "carrier_name" in item for item in data)

    carrier = client.get(f"{BASE_URL}/api/appointments", params={"carrier": "Rota Sul"})
    assert carrier.status_code == 200
    assert all("Rota Sul" in item["carrier_name"] for item in carrier.json())


def test_auth_cookie_session_and_logout(client):
    bad = client.post(f"{BASE_URL}/api/auth/login", json={"email": EMAIL, "password": "wrong"})
    assert bad.status_code == 401
    login = client.post(f"{BASE_URL}/api/auth/login", json={"email": EMAIL, "password": PASSWORD})
    assert login.status_code == 200
    assert login.cookies.get("access_token")
    assert "HttpOnly" in login.headers.get("set-cookie", "")
    me = client.get(f"{BASE_URL}/api/auth/me")
    assert me.status_code == 200 and me.json()["email"] == EMAIL
    logout = client.post(f"{BASE_URL}/api/auth/logout")
    assert logout.status_code == 200
    assert client.get(f"{BASE_URL}/api/auth/me").status_code == 401


def test_protected_crud_persists_and_deletes(client):
    login = client.post(f"{BASE_URL}/api/auth/login", json={"email": EMAIL, "password": PASSWORD})
    assert login.status_code == 200
    payload = {"carrier_name": f"TEST Carrier {uuid.uuid4().hex[:6]}", "supplier_name": "TEST Supplier", "invoice_number": "TEST-NF", "appointment_date": "2026-10-23", "appointment_time": "11:15", "volume_count": 3, "dock_door": "C-01", "status": "Agendado"}
    created = client.post(f"{BASE_URL}/api/appointments", json=payload)
    assert created.status_code == 200
    appointment_id = created.json()["id"]
    updated = {**payload, "supplier_name": "TEST Updated Supplier"}
    assert client.put(f"{BASE_URL}/api/appointments/{appointment_id}", json=updated).status_code == 200
    listed = client.get(f"{BASE_URL}/api/appointments", params={"supplier": "TEST Updated Supplier"})
    assert any(item["id"] == appointment_id for item in listed.json())
    assert client.delete(f"{BASE_URL}/api/appointments/{appointment_id}").status_code == 200
    assert not any(item["id"] == appointment_id for item in client.get(f"{BASE_URL}/api/appointments").json())