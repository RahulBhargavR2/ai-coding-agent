from sqlalchemy import select

from app.models.refresh_token import RefreshToken

base_url = "/api/v1"

def test_logout_success(
    client,
    db_session,
    user_factory,
):
    # Arrange
    password = "CorrectPassword123!"

    user = user_factory(
        email="logout@example.com",
        password=password,
    )

    login_response = client.post(
        base_url+"/auth/login",
        json={
            "email": user.email,
            "password": password,
        },
    )

    assert login_response.status_code == 200

    refresh_token = login_response.json()["refresh_token"]

    # Act
    response = client.post(
        base_url+"/auth/logout",
        json={
            "refresh_token": refresh_token,
        },
    )

    # Assert
    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "Logged out successfully."

    # Verify the refresh token was revoked.
    stmt = select(RefreshToken).where(
        RefreshToken.user_id == user.id,
    )

    stored_token = db_session.scalar(stmt)

    assert stored_token is not None
    assert stored_token.is_revoked is True


def test_revoked_token_cannot_refresh(
    client,
    user_factory,
):
    # Arrange
    password = "CorrectPassword123!"

    user = user_factory(
        email="logout-refresh@example.com",
        password=password,
    )

    login_response = client.post(
        base_url+"/auth/login",
        json={
            "email": user.email,
            "password": password,
        },
    )

    assert login_response.status_code == 200

    refresh_token = login_response.json()["refresh_token"]

    # Act 1 — Logout
    logout_response = client.post(
        base_url+"/auth/logout",
        json={
            "refresh_token": refresh_token,
        },
    )

    assert logout_response.status_code == 200

    # Act 2 — Try to use the revoked token
    refresh_response = client.post(
        base_url+"/auth/refresh",
        json={
            "refresh_token": refresh_token,
        },
    )

    # Assert
    assert refresh_response.status_code == 401

    data = refresh_response.json()

    assert data["detail"] == "Invalid or expired refresh token."

    assert "access_token" not in data
    assert "refresh_token" not in data
