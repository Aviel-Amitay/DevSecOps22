import os
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

# app.main creates the database tables when it is imported. Use SQLite during
# tests so importing the application never requires a running PostgreSQL server.
os.environ["DATABASE_URL"] = "sqlite://"

from app.database import get_db  # noqa: E402
from app.main import app  # noqa: E402

client = TestClient(app)


@pytest.fixture
def mock_db():
    db = MagicMock()
    app.dependency_overrides[get_db] = lambda: db
    yield db
    app.dependency_overrides.clear()


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_create_job_with_valid_data_returns_201(mock_db):
    mock_db.refresh.side_effect = lambda job: setattr(
        job, "created_at", datetime.now(timezone.utc)
    )

    response = client.post(
        "/jobs/",
        json={
            "title": "DevOps Engineer",
            "description": "Build and maintain secure CI/CD pipelines.",
            "company": "Example Ltd",
            "location": "Remote",
            "salary_range": "$80,000-$100,000",
        },
    )

    assert response.status_code == 201
    assert response.json()["title"] == "DevOps Engineer"
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()


def test_create_job_with_missing_fields_returns_422(mock_db):
    response = client.post(
        "/jobs/",
        json={"title": "Incomplete Job"},
    )

    assert response.status_code == 422
    mock_db.add.assert_not_called()
    mock_db.commit.assert_not_called()


def test_get_nonexistent_job_returns_404(mock_db):
    mock_db.query.return_value.filter.return_value.first.return_value = None

    response = client.get("/jobs/does-not-exist")

    assert response.status_code == 404
    assert response.json() == {"detail": "Job 'does-not-exist' not found"}
