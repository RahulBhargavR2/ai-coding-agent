from uuid import uuid4

from app.models.enums import MessageRole


base_url = "/api/v1"


def get_auth_headers(client, user):
    """
    Authenticate through the real login endpoint and
    return the Authorization header.
    """

    password = "CorrectPassword123!"

    response = client.post(
        base_url + "/auth/login",
        json={
            "email": user.email,
            "password": password,
        },
    )

    assert response.status_code == 200

    access_token = response.json()["access_token"]

    return {
        "Authorization": f"Bearer {access_token}",
    }


def create_authenticated_user(user_factory):
    """
    Create a user with a known password so the login
    endpoint can be used to authenticate API requests.
    """

    password = "CorrectPassword123!"

    user = user_factory(
        email="chat-api@example.com",
        password=password,
    )

    return user


def test_create_chat_success(
    client,
    user_factory,
    workspace_factory,
    project_factory,
    repository_factory,
):
    password = "CorrectPassword123!"

    user = user_factory(
        email="chat-api@example.com",
        password=password,
    )

    workspace = workspace_factory(
        user_id=user.id,
    )

    project = project_factory(
        workspace_id=workspace.id,
    )

    repository = repository_factory(
        project_id=project.id,
    )

    headers = get_auth_headers(client, user)

    response = client.post(
        base_url + "/chats",
        headers=headers,
        json={
            "repository_id": str(repository.id),
            "title": "My Coding Chat",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["repository_id"] == str(repository.id)
    assert data["title"] == "My Coding Chat"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_chat_without_authentication(
    client,
    repository,
):
    response = client.post(
        base_url + "/chats",
        json={
            "repository_id": str(repository.id),
            "title": "My Coding Chat",
        },
    )

    assert response.status_code == 401


def test_get_chat_success(
    client,
    user_factory,
    workspace_factory,
    project_factory,
    repository_factory,
    chat_factory,
):
    password = "CorrectPassword123!"

    user = user_factory(
        email="chat-get@example.com",
        password=password,
    )

    workspace = workspace_factory(
        user_id=user.id,
    )

    project = project_factory(
        workspace_id=workspace.id,
    )

    repository = repository_factory(
        project_id=project.id,
    )

    chat = chat_factory(
        repository_id=repository.id,
        title="My Coding Chat",
    )

    headers = get_auth_headers(client, user)

    response = client.get(
        base_url + f"/chats/{chat.id}",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(chat.id)
    assert data["repository_id"] == str(repository.id)
    assert data["title"] == "My Coding Chat"


def test_get_chat_not_found(
    client,
    user_factory,
):
    user = create_authenticated_user(user_factory)

    headers = get_auth_headers(client, user)

    chat_id = uuid4()

    response = client.get(
        base_url + f"/chats/{chat_id}",
        headers=headers,
    )

    assert response.status_code == 404


def test_get_chat_without_authentication(
    client,
    chat,
):
    response = client.get(
        base_url + f"/chats/{chat.id}",
    )

    assert response.status_code == 401


def test_get_chat_forbidden_for_another_user(
    client,
    user_factory,
    chat,
):
    user = create_authenticated_user(user_factory)

    headers = get_auth_headers(client, user)

    response = client.get(
        base_url + f"/chats/{chat.id}",
        headers=headers,
    )

    assert response.status_code == 404


def test_list_messages_success(
    client,
    user_factory,
    workspace_factory,
    project_factory,
    repository_factory,
    chat_factory,
    chat_message_factory,
):
    password = "CorrectPassword123!"

    user = user_factory(
        email="messages@example.com",
        password=password,
    )

    workspace = workspace_factory(
        user_id=user.id,
    )

    project = project_factory(
        workspace_id=workspace.id,
    )

    repository = repository_factory(
        project_id=project.id,
    )

    chat = chat_factory(
        repository_id=repository.id,
        title="Messages Chat",
    )

    message_1 = chat_message_factory(
        chat_id=chat.id,
        content="First message",
        role=MessageRole.USER,
    )

    message_2 = chat_message_factory(
        chat_id=chat.id,
        content="Second message",
        role=MessageRole.ASSISTANT,
    )

    headers = get_auth_headers(client, user)

    response = client.get(
        base_url + f"/chats/{chat.id}/messages",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2

    assert data[0]["id"] == str(message_1.id)
    assert data[0]["chat_id"] == str(chat.id)
    assert data[0]["content"] == "First message"
    assert data[0]["role"] == MessageRole.USER.value

    assert data[1]["id"] == str(message_2.id)
    assert data[1]["chat_id"] == str(chat.id)
    assert data[1]["content"] == "Second message"
    assert data[1]["role"] == MessageRole.ASSISTANT.value


def test_list_messages_empty(
    client,
    user_factory,
    workspace_factory,
    project_factory,
    repository_factory,
    chat_factory,
):
    password = "CorrectPassword123!"

    user = user_factory(
        email="empty-messages@example.com",
        password=password,
    )

    workspace = workspace_factory(
        user_id=user.id,
    )

    project = project_factory(
        workspace_id=workspace.id,
    )

    repository = repository_factory(
        project_id=project.id,
    )

    chat = chat_factory(
        repository_id=repository.id,
    )

    headers = get_auth_headers(client, user)

    response = client.get(
        base_url + f"/chats/{chat.id}/messages",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json() == []


def test_list_messages_forbidden_for_another_user(
    client,
    user_factory,
    chat,
):
    user = create_authenticated_user(user_factory)

    headers = get_auth_headers(client, user)

    response = client.get(
        base_url + f"/chats/{chat.id}/messages",
        headers=headers,
    )

    assert response.status_code == 404


def test_list_messages_without_authentication(
    client,
    chat,
):
    response = client.get(
        base_url + f"/chats/{chat.id}/messages",
    )

    assert response.status_code == 401


def test_list_repository_chats_success(
    client,
    user_factory,
    workspace_factory,
    project_factory,
    repository_factory,
    chat_factory,
):
    user = create_authenticated_user(user_factory)

    workspace = workspace_factory(
        user_id=user.id,
    )

    project = project_factory(
        workspace_id=workspace.id,
    )

    repository = repository_factory(
        project_id=project.id,
    )

    chat_1 = chat_factory(
        repository_id=repository.id,
        title="Chat 1",
    )

    chat_2 = chat_factory(
        repository_id=repository.id,
        title="Chat 2",
    )

    headers = get_auth_headers(client, user)

    response = client.get(
        base_url + f"/chats/repository/{repository.id}",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2

    returned_ids = {item["id"] for item in data}

    assert str(chat_1.id) in returned_ids
    assert str(chat_2.id) in returned_ids


def test_list_repository_chats_empty(
    client,
    user,
    repository,
):
    headers = get_auth_headers(client, user)

    response = client.get(
        base_url + f"/chats/repository/{repository.id}",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json() == []


def test_list_repository_chats_without_authentication(
    client,
    repository,
):
    response = client.get(
        base_url + f"/chats/repository/{repository.id}",
    )

    assert response.status_code == 401
