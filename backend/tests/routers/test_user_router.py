from app.models.core import User
from app.security import verify_password


# ==================================================
# CREATE USER
# ==================================================

def test_create_user_success(
    client,
    admin_headers,
):
    """
    Admin can create a new employee user.
    """

    payload = {
        "username": "john_doe",
        "password": "password123",
        "role": "employee",
    }

    response = client.post(
        "/api/v1/users/",
        json=payload,
        headers=admin_headers,
    )

    assert response.status_code == 201

    body = response.json()

    assert body["success"] is True
    assert body["message"] == "User created successfully"

    data = body["data"]

    assert data["username"] == payload["username"]
    assert data["role"] == payload["role"]

    assert "id" in data
    assert "created_at" in data

    # Password must NEVER be returned
    assert "password" not in data
    assert "password_hash" not in data


def test_create_admin_user_success(
    client,
    admin_headers,
):
    """
    Admin can create another administrator.
    """

    payload = {
        "username": "new_admin",
        "password": "adminpassword123",
        "role": "admin",
    }

    response = client.post(
        "/api/v1/users/",
        json=payload,
        headers=admin_headers,
    )

    assert response.status_code == 201

    body = response.json()

    assert body["success"] is True
    assert body["message"] == "User created successfully"

    data = body["data"]

    assert data["username"] == "new_admin"
    assert data["role"] == "admin"


def test_create_user_password_is_hashed(
    client,
    db,
    admin_headers,
):
    """
    Stored password must be hashed.
    """

    payload = {
        "username": "hash_test",
        "password": "supersecret123",
        "role": "employee",
    }

    response = client.post(
        "/api/v1/users/",
        json=payload,
        headers=admin_headers,
    )

    assert response.status_code == 201

    user = (
        db.query(User)
        .filter(User.username == "hash_test")
        .first()
    )

    assert user is not None

    # Stored password should not equal plain password
    assert user.password_hash != payload["password"]

    # Hash should validate correctly
    assert verify_password(
        payload["password"],
        user.password_hash,
    )


def test_create_user_saved_in_database(
    client,
    db,
    admin_headers,
):
    """
    User should exist in the database after creation.
    """

    payload = {
        "username": "database_user",
        "password": "password123",
        "role": "employee",
    }

    response = client.post(
        "/api/v1/users/",
        json=payload,
        headers=admin_headers,
    )

    assert response.status_code == 201

    user = (
        db.query(User)
        .filter(User.username == payload["username"])
        .first()
    )

    assert user is not None
    assert user.username == payload["username"]
    assert user.role == payload["role"]


def test_create_user_duplicate_username(
    client,
    admin_headers,
    user_factory,
):
    """
    An administrator cannot create two users with the same username.
    """

    user_factory(username="duplicate_user")

    payload = {
        "username": "duplicate_user",
        "password": "password123",
        "role": "employee",
    }

    response = client.post(
        "/api/v1/users/",
        json=payload,
        headers=admin_headers,
    )

    assert response.status_code == 400

    body = response.json()

    # print(body)
    
    assert body["message"] == "Username is already taken."
    

def test_create_user_requires_authentication(client):
    """
    Creating users requires authentication.
    """

    payload = {
        "username": "new_user",
        "password": "password123",
        "role": "employee",
    }

    response = client.post(
        "/api/v1/users/",
        json=payload,
    )

    assert response.status_code == 401


def test_create_user_invalid_token(client):
    """
    Requests with an invalid token must be rejected.
    """

    payload = {
        "username": "new_user",
        "password": "password123",
        "role": "employee",
    }

    response = client.post(
        "/api/v1/users/",
        json=payload,
        headers={
            "Authorization": "Bearer invalid_token"
        },
    )

    assert response.status_code == 401


def test_create_user_employee_forbidden(
    client,
    employee_headers,
):
    """
    Employees cannot create user accounts.
    """

    payload = {
        "username": "new_user",
        "password": "password123",
        "role": "employee",
    }

    response = client.post(
        "/api/v1/users/",
        json=payload,
        headers=employee_headers,
    )

    assert response.status_code == 403


def test_create_user_username_too_short(
    client,
    admin_headers,
):
    """
    Username must satisfy schema validation.
    """

    payload = {
        "username": "ab",
        "password": "password123",
        "role": "employee",
    }

    response = client.post(
        "/api/v1/users/",
        json=payload,
        headers=admin_headers,
    )

    assert response.status_code == 422


def test_create_user_password_too_short(
    client,
    admin_headers,
):
    """
    Password must contain at least 8 characters.
    """

    payload = {
        "username": "valid_user",
        "password": "1234567",
        "role": "employee",
    }

    response = client.post(
        "/api/v1/users/",
        json=payload,
        headers=admin_headers,
    )

    assert response.status_code == 422


def test_create_user_invalid_role(
    client,
    admin_headers,
):
    """
    Invalid user roles must be rejected.
    """

    payload = {
        "username": "valid_user",
        "password": "password123",
        "role": "manager",
    }

    response = client.post(
        "/api/v1/users/",
        json=payload,
        headers=admin_headers,
    )

    assert response.status_code == 422


# ==================================================
# GET USER
# ==================================================

def test_get_users_success(
    client,
    admin_headers,
    user_factory,
):
    """
    Administrators can retrieve
    the list of users.
    """

    user_factory(
        username="alice",
        role="employee",
    )

    user_factory(
        username="bob",
        role="employee",
    )

    response = client.get(
        "/api/v1/users/",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True

    assert "data" in body
    assert "pagination" in body

    assert len(body["data"]) >= 2

    pagination = body["pagination"]

    assert pagination["page"] == 1
    assert pagination["page_size"] == 100
    assert pagination["total_items"] >= 2


def test_get_users_requires_authentication(client):
    """
    Authentication is required
    to list users.
    """

    response = client.get("/api/v1/users/")

    assert response.status_code == 401


def test_get_users_requires_authentication(client):
    """
    Authentication is required
    to list users.
    """

    response = client.get("/api/v1/users/")

    assert response.status_code == 401


def test_get_users_invalid_token(client):
    """
    Invalid JWT tokens
    are rejected.
    """

    response = client.get(
        "/api/v1/users/",
        headers={
            "Authorization": "Bearer invalid_token"
        },
    )

    assert response.status_code == 401


def test_get_users_employee_forbidden(
    client,
    employee_headers,
):
    """
    Employees cannot
    list users.
    """

    response = client.get(
        "/api/v1/users/",
        headers=employee_headers,
    )

    assert response.status_code == 403


def test_get_users_returns_paginated_response(
    client,
    admin_headers,
    user_factory,
):
    """
    The endpoint returns the standard
    paginated response format.
    """

    user_factory(username="user1")
    user_factory(username="user2")
    user_factory(username="user3")

    response = client.get(
        "/api/v1/users/",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    pagination = body["pagination"]

    assert "page" in pagination
    assert "page_size" in pagination
    assert "total_items" in pagination
    assert "total_pages" in pagination
    assert "has_next" in pagination
    assert "has_previous" in pagination


def test_get_users_pagination(
    client,
    admin_headers,
    user_factory,
):
    """
    Pagination parameters should
    limit the returned users.
    """

    for i in range(5):
        user_factory(
            username=f"user_{i}",
        )

    response = client.get(
        "/api/v1/users/?skip=1&limit=2",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body["data"]) == 2

    pagination = body["pagination"]

    assert pagination["page_size"] == 2
    assert pagination["total_items"] >= 5
    assert pagination["total_pages"] >= 3


def test_get_users_sort_username_ascending(
    client,
    admin_headers,
    user_factory,
):
    """
    Users can be sorted by username
    in ascending order.
    """

    user_factory(username="charlie")
    user_factory(username="alice")
    user_factory(username="bob")

    response = client.get(
        "/api/v1/users/?sort=username&order=asc",
        headers=admin_headers,
    )

    assert response.status_code == 200

    usernames = [
        user["username"]
        for user in response.json()["data"]
    ]

    assert usernames == sorted(usernames)


def test_get_users_sort_username_descending(
    client,
    admin_headers,
    user_factory,
):
    """
    Users can be sorted by username
    in descending order.
    """

    user_factory(username="charlie")
    user_factory(username="alice")
    user_factory(username="bob")

    response = client.get(
        "/api/v1/users/?sort=username&order=desc",
        headers=admin_headers,
    )

    assert response.status_code == 200

    usernames = [
        user["username"]
        for user in response.json()["data"]
    ]

    assert usernames == sorted(
        usernames,
        reverse=True,
    )


def test_get_users_sort_created_at_ascending(
    client,
    admin_headers,
    user_factory,
):
    """
    Users can be sorted by creation
    date in ascending order.
    """

    user_factory(username="first")
    user_factory(username="second")
    user_factory(username="third")

    response = client.get(
        "/api/v1/users/?sort=created_at&order=asc",
        headers=admin_headers,
    )

    assert response.status_code == 200

    created_at = [
        user["created_at"]
        for user in response.json()["data"]
    ]

    assert created_at == sorted(created_at)


def test_get_users_sort_created_at_descending(
    client,
    admin_headers,
    user_factory,
):
    """
    Users can be sorted by creation
    date in descending order.
    """

    user_factory(username="first")
    user_factory(username="second")
    user_factory(username="third")

    response = client.get(
        "/api/v1/users/?sort=created_at&order=desc",
        headers=admin_headers,
    )

    assert response.status_code == 200

    created_at = [
        user["created_at"]
        for user in response.json()["data"]
    ]

    assert created_at == sorted(
        created_at,
        reverse=True,
    )


def test_get_users_invalid_sort_field(
    client,
    admin_headers,
):
    """
    Invalid sort fields should
    return HTTP 400.
    """

    response = client.get(
        "/api/v1/users/?sort=invalid_field",
        headers=admin_headers,
    )

    assert response.status_code == 400

    body = response.json()

    assert body["success"] is False
    assert "Invalid sort field" in body["message"]


# ==================================================
# GET CURRENT USER
# ==================================================

def test_get_current_authenticated_admin(
    client,
    admin_headers,
):
    """
    An authenticated administrator
    should retrieve their own profile.
    """

    response = client.get(
        "/api/v1/users/me",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True

    user = body["data"]

    assert user["username"] == "admin_test"
    assert user["role"] == "admin"
    assert "id" in user
    assert "created_at" in user
    

def test_get_current_authenticated_employee(
    client,
    employee_headers,
):
    """
    An authenticated employee
    should retrieve their own profile.
    """

    response = client.get(
        "/api/v1/users/me",
        headers=employee_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True

    user = body["data"]

    assert user["username"] == "employee_test"
    assert user["role"] == "employee"


def test_get_current_user_requires_authentication(
    client,
):
    """
    Authentication is required.
    """

    response = client.get("/api/v1/users/me")

    assert response.status_code == 401

    body = response.json()

    assert body["success"] is False
    assert body["message"] == "Not authenticated"


def test_get_current_user_invalid_token(
    client,
):
    """
    Invalid JWT tokens should
    be rejected.
    """

    response = client.get(
        "/api/v1/users/me",
        headers={
            "Authorization": "Bearer invalid_token"
        },
    )

    assert response.status_code == 401

    body = response.json()

    assert body["success"] is False
    

# ==================================================
# GET USER BY ID
# ==================================================

def test_get_user_by_id_success(
    client,
    admin_headers,
    user_factory,
):
    """
    An administrator can retrieve
    a user by ID.
    """

    user = user_factory(
        username="john_doe",
        role="employee",
    )

    response = client.get(
        f"/api/v1/users/{user.id}",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True

    data = body["data"]

    assert data["id"] == user.id
    assert data["username"] == "john_doe"
    assert data["role"] == "employee"
    

def test_get_user_by_id_not_found(
    client,
    admin_headers,
):
    """
    Requesting a non-existing user
    should return HTTP 404.
    """

    response = client.get(
        "/api/v1/users/999999",
        headers=admin_headers,
    )

    assert response.status_code == 404

    body = response.json()

    assert body["success"] is False
    assert body["message"] == "User not found."


def test_get_user_by_id_invalid_id_zero(
    client,
    admin_headers,
):
    """
    User IDs must be greater than zero.
    """

    response = client.get(
        "/api/v1/users/0",
        headers=admin_headers,
    )

    assert response.status_code == 422


def test_get_user_by_id_requires_authentication(
    client,
):
    """
    Authentication is required.
    """

    response = client.get("/api/v1/users/1")

    assert response.status_code == 401


def test_get_user_by_id_invalid_token(
    client,
):
    """
    Invalid JWT tokens should
    be rejected.
    """

    response = client.get(
        "/api/v1/users/1",
        headers={
            "Authorization": "Bearer invalid_token"
        },
    )

    assert response.status_code == 401


def test_get_user_by_id_employee_forbidden(
    client,
    employee_headers,
    user_factory,
):
    """
    Employees cannot retrieve
    arbitrary users.
    """

    user = user_factory()

    response = client.get(
        f"/api/v1/users/{user.id}",
        headers=employee_headers,
    )

    assert response.status_code == 403


# ==================================================
# SEARCH USER
# ==================================================

def test_search_users_by_username(
    client,
    admin_headers,
    user_factory,
):
    """
    Search should return an exact
    username match.
    """

    user_factory(username="johnsmith")
    user_factory(username="alice")

    response = client.get(
        "/api/v1/users/search/?q=johnsmith",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert len(body["data"]) == 1
    assert body["data"][0]["username"] == "johnsmith"


def test_search_users_partial_username(
    client,
    admin_headers,
    user_factory,
):
    """
    Partial username matches
    should be returned.
    """

    user_factory(username="john")
    user_factory(username="johnny")
    user_factory(username="alice")

    response = client.get(
        "/api/v1/users/search/?q=john",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    usernames = [
        user["username"]
        for user in body["data"]
    ]

    assert "john" in usernames
    assert "johnny" in usernames


def test_search_users_no_matches(
    client,
    admin_headers,
    user_factory,
):
    """
    Searching for a username that
    does not exist should return
    an empty list.
    """

    user_factory(username="alice")

    response = client.get(
        "/api/v1/users/search/?q=does_not_exist",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["data"] == []

    pagination = body["pagination"]

    assert pagination["total_items"] == 0


def test_search_users_pagination(
    client,
    admin_headers,
    user_factory,
):
    """
    Search results should support
    pagination.
    """

    for i in range(5):
        user_factory(
            username=f"john{i}",
        )

    response = client.get(
        "/api/v1/users/search/?q=john&skip=1&limit=2",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body["data"]) == 2

    pagination = body["pagination"]

    assert pagination["page_size"] == 2
    assert pagination["total_items"] >= 5


def test_search_users_requires_authentication(
    client,
):
    """
    Authentication is required.
    """

    response = client.get(
        "/api/v1/users/search/?q=john"
    )

    assert response.status_code == 401


def test_search_users_invalid_token(
    client,
):
    """
    Invalid JWT tokens should
    be rejected.
    """

    response = client.get(
        "/api/v1/users/search/?q=john",
        headers={
            "Authorization": "Bearer invalid_token"
        },
    )

    assert response.status_code == 401


def test_search_users_employee_forbidden(
    client,
    employee_headers,
):
    """
    Employees cannot search
    users.
    """

    response = client.get(
        "/api/v1/users/search/?q=john",
        headers=employee_headers,
    )

    assert response.status_code == 403


def test_search_users_empty_query(
    client,
    admin_headers,
):
    """
    Empty search queries should
    fail validation.
    """

    response = client.get(
        "/api/v1/users/search/?q=",
        headers=admin_headers,
    )

    assert response.status_code == 422


def test_search_users_query_too_long(
    client,
    admin_headers,
):
    """
    Search queries longer than
    100 characters should fail
    validation.
    """

    query = "a" * 101

    response = client.get(
        f"/api/v1/users/search/?q={query}",
        headers=admin_headers,
    )

    assert response.status_code == 422


# ==================================================
# UPDATE USER
# ==================================================

def test_update_user_success(
    client,
    admin_headers,
    user_factory,
):
    user = user_factory(
        username="old_username",
        role="employee",
    )

    payload = {
        "username": "new_username",
        "role": "admin",
    }

    response = client.put(
        f"/api/v1/users/{user.id}",
        json=payload,
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    # assert body["success"] is False
    assert body["message"] == "User updated successfully"

    data = body["data"]

    assert data["id"] == user.id
    assert data["username"] == "new_username"
    assert data["role"] == "admin"


def test_update_user_username_only(
    client,
    admin_headers,
    user_factory,
):
    user = user_factory(
        username="employee01",
        role="employee",
    )

    payload = {
        "username": "employee02",
        "role": "employee",
    }

    response = client.put(
        f"/api/v1/users/{user.id}",
        json=payload,
        headers=admin_headers,
    )

    assert response.status_code == 200

    data = response.json()["data"]

    assert data["username"] == "employee02"
    assert data["role"] == "employee"


def test_update_user_role_only(
    client,
    admin_headers,
    user_factory,
):
    user = user_factory(
        username="employee01",
        role="employee",
    )

    payload = {
        "username": "employee01",
        "role": "admin",
    }

    response = client.put(
        f"/api/v1/users/{user.id}",
        json=payload,
        headers=admin_headers,
    )

    assert response.status_code == 200

    data = response.json()["data"]

    assert data["username"] == "employee01"
    assert data["role"] == "admin"


def test_update_user_requires_authentication(
    client,
    user_factory,
):
    user = user_factory()

    payload = {
        "username": "updated",
        "role": "employee",
    }

    response = client.put(
        f"/api/v1/users/{user.id}",
        json=payload,
    )

    assert response.status_code == 401

    body = response.json()

    # print(body)
    
    assert body["success"] is False
    assert body["message"] == "Not authenticated"


def test_update_user_invalid_token(
    client,
    user_factory,
):
    user = user_factory()

    payload = {
        "username": "updated",
        "role": "employee",
    }

    response = client.put(
        f"/api/v1/users/{user.id}",
        json=payload,
        headers={
            "Authorization": "Bearer invalid_token"
        },
    )

    assert response.status_code == 401

    body = response.json()

    print(body)
    
    assert body["success"] is False
    assert body["message"] == "Could not validate credentials."


def test_update_user_employee_forbidden(
    client,
    employee_headers,
    user_factory,
):
    user = user_factory()

    payload = {
        "username": "updated",
        "role": "employee",
    }

    response = client.put(
        f"/api/v1/users/{user.id}",
        json=payload,
        headers=employee_headers,
    )

    assert response.status_code == 403

    body = response.json()
    
    # print(body)

    assert body["success"] is False
    assert body["message"] == (
        "Administrator privileges required."
    )


# ==================================================
# UPDATE USER - ERROR HANDLING
# ==================================================

def test_update_user_not_found(
    client,
    admin_headers,
):
    response = client.put(
        "/api/v1/users/999999",
        headers=admin_headers,
        json={
            "username": "updated_user",
            "role": "employee",
        },
    )

    assert response.status_code == 404

    body = response.json()

    assert body["success"] is False
    assert body["message"] == "User not found."


def test_update_user_duplicate_username(
    client,
    admin_headers,
    user_factory,
):
    user1 = user_factory(username="john")
    user2 = user_factory(username="mary")

    response = client.put(
        f"/api/v1/users/{user2.id}",
        headers=admin_headers,
        json={
            "username": "john",
            "role": "employee",
        },
    )

    assert response.status_code == 400

    body = response.json()

    assert body["success"] is False
    assert body["message"] == "Username already exists."


def test_update_user_invalid_id_zero(
    client,
    admin_headers,
):
    response = client.put(
        "/api/v1/users/0",
        headers=admin_headers,
        json={
            "username": "updated",
            "role": "employee",
        },
    )

    assert response.status_code == 422


def test_update_user_username_too_short(
    client,
    admin_headers,
    employee_user,
):
    response = client.put(
        f"/api/v1/users/{employee_user.id}",
        headers=admin_headers,
        json={
            "username": "ab",
            "role": "employee",
        },
    )

    assert response.status_code == 422


def test_update_user_invalid_role(
    client,
    admin_headers,
    employee_user,
):
    response = client.put(
        f"/api/v1/users/{employee_user.id}",
        headers=admin_headers,
        json={
            "username": "valid_username",
            "role": "manager",
        },
    )

    assert response.status_code == 422


# ==================================================
# CHANGE PASSWORD
# ==================================================

def test_change_user_password_success(
    client,
    admin_headers,
    employee_user,
):
    response = client.put(
        f"/api/v1/users/{employee_user.id}/password",
        headers=admin_headers,
        json={
            "password": "newpassword123",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["message"] == "Password updated successfully"


def test_change_user_password_hash_changes(
    client,
    admin_headers,
    employee_user,
    db,
):
    old_hash = employee_user.password_hash

    response = client.put(
        f"/api/v1/users/{employee_user.id}/password",
        headers=admin_headers,
        json={
            "password": "brandnewpassword123",
        },
    )

    assert response.status_code == 200

    db.refresh(employee_user)

    assert employee_user.password_hash != old_hash


def test_change_user_password_not_plaintext(
    client,
    admin_headers,
    employee_user,
    db,
):
    new_password = "supersecret123"

    response = client.put(
        f"/api/v1/users/{employee_user.id}/password",
        headers=admin_headers,
        json={
            "password": new_password,
        },
    )

    assert response.status_code == 200

    db.refresh(employee_user)

    assert employee_user.password_hash != new_password

    assert verify_password(
        new_password,
        employee_user.password_hash,
    )


def test_change_user_password_requires_authentication(
    client,
    employee_user,
):
    response = client.put(
        f"/api/v1/users/{employee_user.id}/password",
        json={
            "password": "newpassword123",
        },
    )

    assert response.status_code == 401

    body = response.json()

    assert body["success"] is False
    assert body["message"] == "Not authenticated"


def test_change_user_password_invalid_token(
    client,
    employee_user,
):
    response = client.put(
        f"/api/v1/users/{employee_user.id}/password",
        headers={
            "Authorization": "Bearer invalidtoken"
        },
        json={
            "password": "newpassword123",
        },
    )

    assert response.status_code == 401

    body = response.json()

    assert body["success"] is False
    assert body["message"] == "Could not validate credentials."


def test_change_user_password_employee_forbidden(
    client,
    employee_headers,
    admin_user,
):
    response = client.put(
        f"/api/v1/users/{admin_user.id}/password",
        headers=employee_headers,
        json={
            "password": "newpassword123",
        },
    )

    assert response.status_code == 403

    body = response.json()

    assert body["success"] is False
    assert body["message"] == (
        "Administrator privileges required."
    )


# ==================================================
# CHANGE PASSWORD - ERROR HANDLING
# ==================================================

def test_change_user_password_not_found(
    client,
    admin_headers,
):
    response = client.put(
        "/api/v1/users/999999/password",
        headers=admin_headers,
        json={
            "password": "newpassword123",
        },
    )

    assert response.status_code == 404

    body = response.json()

    # print(body)
    
    assert response.status_code == 404
    assert body["success"] is False
    assert body["message"] == "User not found."


def test_change_user_password_too_short(
    client,
    admin_headers,
    employee_user,
):
    response = client.put(
        f"/api/v1/users/{employee_user.id}/password",
        headers=admin_headers,
        json={
            "password": "123",
        },
    )

    assert response.status_code == 422


def test_change_user_password_invalid_id_zero(
    client,
    admin_headers,
):
    response = client.put(
        "/api/v1/users/0/password",
        headers=admin_headers,
        json={
            "password": "newpassword123",
        },
    )

    assert response.status_code == 422


# ==================================================
# DELETE USER
# ==================================================

def test_delete_user_success(
    client,
    admin_headers,
    user_factory,
    db,
):
    user = user_factory()

    response = client.delete(
        f"/api/v1/users/{user.id}",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["message"] == "User deleted successfully"

    deleted = db.get(type(user), user.id)
    assert deleted is None


def test_delete_user_requires_authentication(
    client,
    user_factory,
):
    user = user_factory()

    response = client.delete(
        f"/api/v1/users/{user.id}",
    )

    assert response.status_code == 401

    body = response.json()

    assert body["success"] is False
    assert body["message"] == "Not authenticated"


def test_delete_user_invalid_token(
    client,
    user_factory,
):
    user = user_factory()

    response = client.delete(
        f"/api/v1/users/{user.id}",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401

    body = response.json()

    assert body["success"] is False
    assert body["message"] == "Could not validate credentials."


def test_delete_user_employee_forbidden(
    client,
    employee_headers,
    user_factory,
):
    user = user_factory()

    response = client.delete(
        f"/api/v1/users/{user.id}",
        headers=employee_headers,
    )

    assert response.status_code == 403

    body = response.json()

    assert body["success"] is False
    assert body["message"] == "Administrator privileges required."


def test_delete_user_not_found(
    client,
    admin_headers,
):
    response = client.delete(
        "/api/v1/users/999999",
        headers=admin_headers,
    )

    assert response.status_code == 404

    body = response.json()

    assert body["success"] is False
    assert body["message"] == "User not found."


def test_delete_user_invalid_id_zero(
    client,
    admin_headers,
):
    response = client.delete(
        "/api/v1/users/0",
        headers=admin_headers,
    )

    assert response.status_code == 422


def test_delete_user_with_sales(
    client,
    admin_headers,
    user_factory,
    sale_factory,
):
    user = user_factory()

    sale_factory(user=user)

    response = client.delete(
        f"/api/v1/users/{user.id}",
        headers=admin_headers,
    )

    assert response.status_code == 400

    body = response.json()

    assert body["success"] is False
    assert body["message"] == (
        "Cannot delete a user with registered sales."
    )


def test_delete_user_with_batches(
    client,
    admin_headers,
    user_factory,
    inventory_batch_factory,
):
    user = user_factory()

    inventory_batch_factory(
        created_by_user=user,
    )

    response = client.delete(
        f"/api/v1/users/{user.id}",
        headers=admin_headers,
    )

    assert response.status_code == 400

    body = response.json()

    assert body["success"] is False
    assert body["message"] == (
        "Cannot delete a user that created inventory batches."
    )


def test_delete_user_with_losses(
    client,
    admin_headers,
    user_factory,
    inventory_batch_factory,
    loss_log_factory,
):
    user = user_factory()

    batch = inventory_batch_factory()

    loss_log_factory(
        batch=batch,
        user=user,
    )

    response = client.delete(
        f"/api/v1/users/{user.id}",
        headers=admin_headers,
    )

    assert response.status_code == 400

    body = response.json()

    assert body["success"] is False
    assert body["message"] == (
        "Cannot delete a user with registered losses."
    )


def test_delete_user_with_transactions(
    client,
    admin_headers,
    user_factory,
    inventory_transaction_factory,
):
    user = user_factory()

    inventory_transaction_factory(
        user=user,
    )

    response = client.delete(
        f"/api/v1/users/{user.id}",
        headers=admin_headers,
    )

    assert response.status_code == 400

    body = response.json()

    assert body["success"] is False
    assert body["message"] == (
        "Cannot delete a user with inventory transactions."
    )