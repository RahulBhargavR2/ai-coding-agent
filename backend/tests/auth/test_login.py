from app.models.refresh_token import RefreshToken
from sqlalchemy import select
from datetime import UTC, datetime

base_url = "/api/v1"

def test_login_success(client, db_session, token_service,user_factory):
    password = 'Correctpassword123'
    existing_user = user_factory(
        email='test@example.com',
        password=password
    )

    payload = {
        "email":existing_user.email,
        "password":password
    }

    response = client.post(
        base_url+"/auth/login",
        json=payload
    )

    data = response.json()
    

    assert response.status_code == 200

    assert "access_token" in data
    assert isinstance(data['access_token'],str)
    assert data['access_token'] is not None

    assert "refresh_token" in data
    assert isinstance(data["refresh_token"], str)
    assert data["refresh_token"] is not None

    assert data['token_type'] == 'bearer'


    response_user = data["user"]

    assert response_user["email"] == existing_user.email
    assert response_user["name"] == existing_user.name
    assert "hashed_password" not in response_user

    stmt = select(RefreshToken).where(RefreshToken.user_id == existing_user.id)
    db_refresh_token = db_session.scalar(stmt)

    assert db_refresh_token 

    assert token_service.verify_token(
        data['refresh_token'],
        db_refresh_token.token_hash
    )

    assert db_refresh_token.user_id == existing_user.id

    assert db_refresh_token.is_revoked is False

    assert db_refresh_token.expires_at > datetime.now(UTC)


def test_login_invalid_password(client,db_session,user_factory):
    existing_user = user_factory(
        email="test@example.com", password="Correctpassword123"
    )

    payload = {"email": existing_user.email, "password": "Wrongpassword123"}

    response = client.post(base_url+"/auth/login", json=payload)

    data = response.json()

    assert response.status_code == 401

    assert "access_token" not in data
    assert "refresh_token" not in data

    assert data["detail"] == "Invalid email or password."

    stmt = select(RefreshToken).where(RefreshToken.user_id == existing_user.id)
    db_refresh_token = db_session.scalar(stmt)

    assert db_refresh_token is None


def test_login_invalid_email(client):

    payload = {
        "email":"unknown@example.com",
        "password":"unknownpassword"
    }

    response = client.post(base_url+"/auth/login",json=payload)

    data = response.json()

    assert response.status_code == 401

    assert data['detail'] == "Invalid email or password"
