def test_login_returns_bearer_token(
    client,
    user_factory,
):
    user = user_factory(
        username="login_user",
        password="secret123",
        role="admin",
    )

    response = client.post(
        "/api/v1/token",
        data={
            "username": user.username,
            "password": "secret123",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["token_type"] == "bearer"
    assert body["access_token"]