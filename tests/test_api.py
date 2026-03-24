"""
Core API Tests - Run with: pytest tests/ -v
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.database import Base, get_db
from main import app

# Use in-memory SQLite for tests
TEST_DB_URL = "sqlite:///./test_ca_copilot.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
Base.metadata.create_all(bind=engine)
client = TestClient(app)


@pytest.fixture
def auth_headers():
    """Create a test user and return auth headers."""
    # Signup
    resp = client.post("/api/v1/auth/signup", json={
        "email": "test@cacopilot.in",
        "full_name": "Test CA",
        "password": "testpass123",
        "firm_name": "Test Firm",
        "role": "ca_admin"
    })
    if resp.status_code not in (200, 201, 400):  # 400 = already exists
        pytest.fail(f"Signup failed: {resp.json()}")

    # Login
    resp = client.post("/api/v1/auth/login", json={
        "email": "test@cacopilot.in",
        "password": "testpass123"
    })
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_health():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


def test_signup():
    import time
    email = f"new_{int(time.time())}@test.com"
    resp = client.post("/api/v1/auth/signup", json={
        "email": email,
        "full_name": "New User",
        "password": "password123",
        "role": "ca_admin"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["email"] == email


def test_login_invalid():
    resp = client.post("/api/v1/auth/login", json={
        "email": "nobody@test.com",
        "password": "wrong"
    })
    assert resp.status_code == 401


def test_create_and_list_clients(auth_headers):
    # Create
    resp = client.post("/api/v1/clients", json={
        "company_name": "Test Company Pvt Ltd",
        "pan": "AABCT9999Z",
        "gstin": "27AABCT9999Z1Z5",
        "state": "Maharashtra",
        "business_type": "Private Limited",
    }, headers=auth_headers)
    assert resp.status_code == 201
    client_id = resp.json()["id"]

    # List
    resp = client.get("/api/v1/clients", headers=auth_headers)
    assert resp.status_code == 200
    names = [c["company_name"] for c in resp.json()]
    assert "Test Company Pvt Ltd" in names

    # Get by ID
    resp = client.get(f"/api/v1/clients/{client_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["company_name"] == "Test Company Pvt Ltd"


def test_create_invoice(auth_headers):
    # Create client first
    resp = client.post("/api/v1/clients", json={
        "company_name": "Invoice Test Co",
        "business_type": "LLP",
    }, headers=auth_headers)
    assert resp.status_code == 201
    client_id = resp.json()["id"]

    # Create invoice
    resp = client.post(f"/api/v1/invoices/client/{client_id}", json={
        "client_id": client_id,
        "invoice_type": "purchase",
        "invoice_number": "TEST-001",
        "vendor_name": "Test Vendor",
        "vendor_gstin": "27AABCV1234D1Z5",
        "taxable_amount": 100000,
        "cgst_rate": 9,
        "cgst_amount": 9000,
        "sgst_rate": 9,
        "sgst_amount": 9000,
        "total_tax": 18000,
        "total_amount": 118000,
    }, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["invoice_number"] == "TEST-001"
    assert data["total_amount"] == 118000


def test_dashboard_stats(auth_headers):
    resp = client.get("/api/v1/analytics/dashboard", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "total_clients" in data
    assert "total_invoices" in data


def test_compliance_alerts(auth_headers):
    resp = client.get("/api/v1/compliance/alerts/all?days_ahead=30", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_unauthorized_access():
    resp = client.get("/api/v1/clients")
    assert resp.status_code == 403  # No auth header


# Cleanup
def pytest_sessionfinish():
    import os
    if os.path.exists("./test_ca_copilot.db"):
        os.remove("./test_ca_copilot.db")
