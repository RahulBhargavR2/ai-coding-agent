from app.models.user import User
from sqlalchemy import select

base_url = "/api/v1"
def test_register_success(client, db_session, password_service):
    """
    Registering a valid user should create a new account.
    """

    payload = {
        "name": "Rahul",
        "email": "rahul@example.com",
        "password": "Password123!",
    }

    response = client.post(
        base_url+"/auth/register",
        json=payload,
    )

    data = response.json()

    assert response.status_code == 201

    assert "message" in data
    assert data['message'] == "User registered successfully."

    user = data['user']

    expected_keys = {
        "id",
        "name",
        "email",
        "role",
        "is_active",
        "is_verified",
        "created_at",
        "updated_at",
    }

    assert expected_keys.issubset(user.keys())

    assert "hashed_password" not in user

    stmt = select(User).where(User.email == payload['email'])
    db_user = db_session.scalar(stmt)

    assert db_user is not None

    assert db_user.email == payload['email']

    assert db_user.name == payload['name']

    assert db_user.is_active is True

    assert password_service.verify_password(
        payload['password'],
        db_user.hashed_password,
    )

    assert db_user.name == user['name']
    assert db_user.email == user['email']

    assert "refresh_tokens" not in user



def test_register_fails_when_email_already_exists(
    client,
    db_session,
    user_factory,
):
    # Arrange
    existing_user = user_factory(
        email="rahul@example.com",
    )

    payload = {
        "name": "Rahul",
        "email": existing_user.email,
        "password": "Password123!",
    }

    # Act
    response = client.post(
        base_url + "/auth/register",
        json=payload,
    )

    # Assert
    assert response.status_code == 409

    data = response.json()
    assert data["detail"] == "A user with this email already exists."

    stmt = select(User).where(User.email == payload["email"])
    users = db_session.scalars(stmt).all()

    assert len(users) == 1, "Duplicate user should not be created"
    assert users[0].email == payload["email"]
