from sqlalchemy import select, inspect
from datetime import UTC, datetime, timedelta

from app.models.refresh_token import RefreshToken

base_url = "/api/v1"

def test_refresh_success(
    client,
    db_session,
    token_service,
    user_factory,
):
    # Arrange
    password = "CorrectPassword123!"

    user = user_factory(
        email="refresh@example.com",
        password=password,
    )

    login_payload = {
        "email": user.email,
        "password": password,
    }

    login_response = client.post(
        base_url+"/auth/login",
        json=login_payload,
    )

    print(login_response)

    assert login_response.status_code == 200

    login_data = login_response.json()
    old_refresh_token = login_data["refresh_token"]

    # Verify the original refresh token exists.
    stmt = select(RefreshToken).where(
        RefreshToken.user_id == user.id,
    )

    old_token_model = db_session.scalar(stmt)

    assert old_token_model is not None
    assert old_token_model.is_revoked is False

    assert token_service.verify_token(
        old_refresh_token,
        old_token_model.token_hash,
    )

    # Act
    refresh_response = client.post(
        base_url+"/auth/refresh",
        json={
            "refresh_token": old_refresh_token,
        },
    )

    # Assert response
    assert refresh_response.status_code == 200

    data = refresh_response.json()

    assert "access_token" in data
    assert data["access_token"]

    assert "refresh_token" in data
    assert data["refresh_token"]

    assert data["refresh_token"] != old_refresh_token

    assert data["token_type"] == "bearer"

    response_user = data["user"]

    assert response_user["id"] == str(user.id)
    assert response_user["name"] == user.name
    assert response_user["email"] == user.email

    assert "hashed_password" not in response_user

    new_refresh_token = data["refresh_token"]

    # Verify old token was revoked.
    db_session.refresh(old_token_model)

    assert old_token_model.is_revoked is True

    # Verify a new refresh token was created.
    stmt = select(RefreshToken).where(
        RefreshToken.user_id == user.id,
        RefreshToken.is_revoked.is_(False),
    )

    new_token_model = db_session.scalar(stmt)

    assert new_token_model is not None
    assert new_token_model.user_id == user.id
    assert new_token_model.is_revoked is False

    # Verify the new token matches the stored hash.
    assert token_service.verify_token(
        new_refresh_token,
        new_token_model.token_hash,
    )


def test_refresh_invalid_token(client):
    payload = {
        "refresh_token": "this-is-not-a-valid-refresh-token",
    }

    response = client.post(
        base_url+"/auth/refresh",
        json=payload,
    )

    assert response.status_code == 401

    data = response.json()

    assert data["detail"] == "Invalid or expired refresh token."

    assert "access_token" not in data
    assert "refresh_token" not in data


def test_refresh_revoked_token(
    client,
    db_session,
    user_factory,
):
    # Arrange
    password = "CorrectPassword123!"

    user = user_factory(
        email="revoked@example.com",
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

    # Find the stored refresh token.
    stmt = select(RefreshToken).where(
        RefreshToken.user_id == user.id,
    )

    stored_token = db_session.scalar(stmt)

    assert stored_token is not None

    # Revoke the token before attempting to refresh.
    stored_token.is_revoked = True
    db_session.commit()

    # Act
    response = client.post(
        base_url+"/auth/refresh",
        json={
            "refresh_token": refresh_token,
        },
    )

    # Assert
    assert response.status_code == 401

    data = response.json()

    assert data["detail"] == "Invalid or expired refresh token."

    assert "access_token" not in data
    assert "refresh_token" not in data


def test_refresh_expired_token(
    client,
    db_session,
    user_factory,
):
    # Arrange
    password = "CorrectPassword123!"

    user = user_factory(
        email="expired@example.com",
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

    # Find the stored refresh token.
    stmt = select(RefreshToken).where(
        RefreshToken.user_id == user.id,
    )

    stored_token = db_session.scalar(stmt)

    assert stored_token is not None

    # Expire the token.
    stored_token.expires_at = datetime.now(UTC) - timedelta(days=1)

    db_session.commit()

    # Act
    response = client.post(
        base_url+"/auth/refresh",
        json={
            "refresh_token": refresh_token,
        },
    )

    # Assert
    assert response.status_code == 401

    data = response.json()

    assert data["detail"] == "Invalid or expired refresh token."

    assert "access_token" not in data
    assert "refresh_token" not in data
