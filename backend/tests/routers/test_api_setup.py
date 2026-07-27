def test_admin_login(
    client,
    admin_headers,
):
    """
    Verifies that the API testing infrastructure works.

    This test confirms that:
    - TestClient is configured correctly.
    - The test database override is working.
    - The admin user fixture is created.
    - JWT authentication succeeds.
    - Authorization headers are accepted.
    """

    response = client.get(
        "/",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True

    assert (
        body["message"]
        == "Welcome to the Inventory Control API"
    )