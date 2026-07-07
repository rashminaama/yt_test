from unittest.mock import MagicMock, patch

import pytest
from werkzeug.security import generate_password_hash

from config import config as app_config
from dashboard.app import app as flask_app


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(app_config, "DASHBOARD_USERNAME", "testuser")
    monkeypatch.setattr(
        app_config, "DASHBOARD_PASSWORD_HASH", generate_password_hash("testpass")
    )
    flask_app.config.update(TESTING=True, SECRET_KEY="test-secret")
    with flask_app.test_client() as test_client:
        yield test_client


def test_login_page_renders(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Login" in response.data


def test_login_rejects_bad_credentials(client):
    response = client.post("/login", data={"username": "testuser", "password": "wrong"})
    assert response.status_code == 200
    assert b"Invalid username or password" in response.data


def test_login_accepts_valid_credentials(client):
    response = client.post(
        "/login", data={"username": "testuser", "password": "testpass"}
    )
    assert response.status_code == 302
    assert response.headers["Location"] == "/"


def test_index_requires_login(client):
    response = client.get("/")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_index_shows_videos_when_logged_in(client):
    with client.session_transaction() as session:
        session["logged_in"] = True

    video_row = {
        "title": "Test Video",
        "url": "https://www.youtube.com/watch?v=abc123",
        "channel_title": "Test Channel",
        "category_name": "Music",
        "view_count": 12345,
        "last_seen_at": "2026-07-07T09:00:00Z",
    }
    with patch("dashboard.app.storage.get_connection") as mock_get_connection, patch(
        "dashboard.app.storage.get_recent_videos", return_value=[video_row]
    ):
        mock_get_connection.return_value = MagicMock()
        response = client.get("/")

    assert response.status_code == 200
    assert b"Test Video" in response.data


def test_send_now_requires_login(client):
    response = client.post("/send-now")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_send_now_flashes_success(client):
    with client.session_transaction() as session:
        session["logged_in"] = True

    with patch(
        "dashboard.app.pipeline.run_pipeline",
        return_value={"status": "ok", "video_count": 20},
    ):
        response = client.post("/send-now", follow_redirects=True)

    assert response.status_code == 200
    assert b"20 trending videos" in response.data


def test_send_now_flashes_error_on_failure(client):
    with client.session_transaction() as session:
        session["logged_in"] = True

    with patch(
        "dashboard.app.pipeline.run_pipeline", side_effect=RuntimeError("smtp down")
    ):
        response = client.post("/send-now", follow_redirects=True)

    assert response.status_code == 200
    assert b"smtp down" in response.data
