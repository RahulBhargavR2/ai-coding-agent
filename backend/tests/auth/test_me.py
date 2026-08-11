from app.services.auth.jwt_service import JWTService
from datetime import UTC, datetime, timedelta

base_url = "/api/v1"

def test_me_success(
    client,
    user_factory,
):
    password = "CorrectPassword123!"

    user = user_factory(
        email="me@example.com",
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

    access_token = login_response.json()["access_token"]

    response = client.get(
        base_url+"/auth/me",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(user.id)
    assert data["name"] == user.name
    assert data["email"] == user.email
    assert data["is_active"] is True


def test_me_without_token(client):
    response = client.get(base_url+"/auth/me")

    assert response.status_code == 401

    data = response.json()

    assert data["detail"] == "Authentication credentials were not provided."


def test_me_with_invalid_token(client):
    response = client.get(
        base_url+"/auth/me",
        headers={
            "Authorization": "Bearer invalid-access-token",
        },
    )

    assert response.status_code == 401

    data = response.json()

    assert data["detail"] == "Invalid or expired token."


def test_me_with_expired_token(
    client,
    user_factory,
):
    # Arrange
    user = user_factory(
        email="expired-access@example.com",
    )

    jwt_service = JWTService()

    expired_token = jwt_service.create_access_token(
        subject=str(user.id),
        expires_delta=timedelta(seconds=-1),
    )

    # Act
    response = client.get(
        base_url+"/auth/me",
        headers={
            "Authorization": f"Bearer {expired_token}",
        },
    )

    # Assert
    assert response.status_code == 401

    data = response.json()

    assert data["detail"] == "Invalid or expired token."
