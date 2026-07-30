import pytest

from app.models.core import Category


# ==================================================
# CREATE CATEGORY
# ==================================================

def test_create_category_success(
    client,
    admin_headers,
    db,
):
    """
    Admin can create a new category.
    """

    payload = {
        "name": "Beverages",
        "description": "Soft drinks and juices",
    }

    response = client.post(
        "/api/v1/categories/",
        json=payload,
        headers=admin_headers,
    )

    assert response.status_code == 201

    body = response.json()

    assert body["message"] == "Category created successfully"

    assert body["data"]["name"] == payload["name"]
    assert body["data"]["description"] == payload["description"]

    category = (
        db.query(Category)
        .filter(Category.name == payload["name"])
        .first()
    )

    assert category is not None


def test_create_category_duplicate_name(
    client,
    admin_headers,
    category_factory,
):
    """
    Cannot create two categories with the same name.
    """

    category_factory(
        name="Beverages",
    )

    response = client.post(
        "/api/v1/categories/",
        json={
            "name": "Beverages",
            "description": "Duplicate",
        },
        headers=admin_headers,
    )

    assert response.status_code == 400
    
    # print(response.json())
    
    body = response.json()

    assert body["success"] is False
    
    assert body["message"] == (
        "A category with this name already exists."
    )


def test_create_category_requires_authentication(
    client,
):
    """
    Authentication is required.
    """

    response = client.post(
        "/api/v1/categories/",
        json={
            "name": "Beverages",
            "description": "Soft drinks",
        },
    )

    assert response.status_code == 401
    

def test_create_category_invalid_token(
    client,
):
    """
    Invalid JWT token.
    """

    response = client.post(
        "/api/v1/categories/",
        json={
            "name": "Beverages",
            "description": "Soft drinks",
        },
        headers={
            "Authorization": "Bearer invalid_token"
        },
    )

    assert response.status_code == 401


def test_create_category_employee_forbidden(
    client,
    employee_headers,
):
    """
    Employees cannot create categories.
    """

    response = client.post(
        "/api/v1/categories/",
        json={
            "name": "Beverages",
            "description": "Soft drinks",
        },
        headers=employee_headers,
    )

    assert response.status_code == 403


def test_create_category_validation_error(
    client,
    admin_headers,
):
    """
    Category name must satisfy schema validation.
    """

    response = client.post(
        "/api/v1/categories/",
        json={
            "name": "A",
            "description": "Invalid",
        },
        headers=admin_headers,
    )

    assert response.status_code == 422    


def test_create_category_without_description(
    client,
    admin_headers,
):
    """
    Description is optional.
    """

    response = client.post(
        "/api/v1/categories/",
        json={
            "name": "Bakery",
        },
        headers=admin_headers,
    )

    assert response.status_code == 201

    body = response.json()

    assert body["data"]["name"] == "Bakery"
    assert body["data"]["description"] is None
    

def test_create_category_persists_database(
    client,
    admin_headers,
    db,
):
    """
    Newly created category is persisted.
    """

    response = client.post(
        "/api/v1/categories/",
        json={
            "name": "Frozen Foods",
            "description": "Frozen products",
        },
        headers=admin_headers,
    )

    assert response.status_code == 201

    saved = (
        db.query(Category)
        .filter(Category.name == "Frozen Foods")
        .first()
    )

    assert saved is not None
    assert saved.description == "Frozen products"

    
# ==================================================
# GET ALL CATEGORIES
# ==================================================

def test_get_categories_success(
    client,
    admin_headers,
    category_factory,
):
    """
    Retrieve categories successfully.
    """

    category_factory(name="Beverages")
    category_factory(name="Snacks")

    response = client.get(
        "/api/v1/categories/",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()
    
    print(body)

    assert len(body["data"]) == 2
    assert body["pagination"]["total_items"] == 2
    assert body["pagination"]["total_pages"] == 1
    assert body["pagination"]["page"] == 1
    

def test_get_categories_employee_success(
    client,
    employee_headers,
    category_factory,
):
    """
    Employees can retrieve categories.
    """

    category_factory(name="Beverages")

    response = client.get(
        "/api/v1/categories/",
        headers=employee_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body["data"]) == 1


def test_get_categories_empty_database(
    client,
    admin_headers,
):
    """
    Empty category list.
    """

    response = client.get(
        "/api/v1/categories/",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["data"] == []
    assert body["pagination"]["total_items"] == 0
    assert body["pagination"]["total_pages"] == 0


def test_get_categories_pagination(
    client,
    admin_headers,
    category_factory,
):
    """
    Pagination works correctly.
    """

    for i in range(5):
        category_factory(name=f"Category {i}")

    response = client.get(
        "/api/v1/categories/?skip=1&limit=2",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body["data"]) == 2
    assert body["pagination"]["total_items"] == 5


def test_get_categories_sort_ascending(
    client,
    admin_headers,
    category_factory,
):
    """
    Categories sorted ascending.
    """

    category_factory(name="Zebra")
    category_factory(name="Apple")

    response = client.get(
        "/api/v1/categories/?sort=name&order=asc",
        headers=admin_headers,
    )

    body = response.json()

    names = [
        category["name"]
        for category in body["data"]
    ]

    assert names == sorted(names)


def test_get_categories_sort_descending(
    client,
    admin_headers,
    category_factory,
):
    """
    Categories sorted descending.
    """

    category_factory(name="Apple")
    category_factory(name="Zebra")

    response = client.get(
        "/api/v1/categories/?sort=name&order=desc",
        headers=admin_headers,
    )

    body = response.json()

    names = [
        category["name"]
        for category in body["data"]
    ]

    assert names == sorted(
        names,
        reverse=True,
    )


def test_get_categories_requires_authentication(
    client,
):
    """
    Authentication is required.
    """

    response = client.get(
        "/api/v1/categories/",
    )

    assert response.status_code == 401    


def test_get_categories_invalid_sort(
    client,
    admin_headers,
):
    response = client.get(
        "/api/v1/categories/?sort=invalid_field",
        headers=admin_headers,
    )

    assert response.status_code == 400

    body = response.json()

    assert body["success"] is False

    assert body["message"] == (
        "Invalid sort field. Allowed values: name"
    )
    
    
# ==================================================
# GET CATEGORY
# ==================================================

def test_get_category_success(
    client,
    admin_headers,
    category,
):
    response = client.get(
        f"/api/v1/categories/{category.id}",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    # print(body)
    
    assert body["success"] is True

    data = body["data"]

    assert data["id"] == category.id
    assert data["name"] == category.name
    assert data["description"] == category.description


def test_get_category_employee_success(
    client,
    employee_headers,
    category,
):
    response = client.get(
        f"/api/v1/categories/{category.id}",
        headers=employee_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["data"]["id"] == category.id


def test_get_category_not_found(
    client,
    admin_headers,
):
    response = client.get(
        "/api/v1/categories/9999",
        headers=admin_headers,
    )

    assert response.status_code == 404

    body = response.json()

    assert body["success"] is False
    assert body["message"] == "Category not found."


def test_get_category_requires_authentication(
    client,
    category,
):
    response = client.get(
        f"/api/v1/categories/{category.id}",
    )

    assert response.status_code == 401


def test_get_category_invalid_token(
    client,
    category,
):
    response = client.get(
        f"/api/v1/categories/{category.id}",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401


def test_get_category_invalid_id_validation(
    client,
    admin_headers,
):
    response = client.get(
        "/api/v1/categories/0",
        headers=admin_headers,
    )

    assert response.status_code == 422


# ==================================================
# UPDATE CATEGORY
# ==================================================

def test_update_category_success(
    client,
    admin_headers,
    category_factory,
):
    category = category_factory(
        name="Old Name",
        description="Old Description",
    )

    response = client.put(
        f"/api/v1/categories/{category.id}",
        headers=admin_headers,
        json={
            "name": "New Name",
            "description": "New Description",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["message"] == "Category updated successfully"

    assert body["data"]["id"] == category.id
    assert body["data"]["name"] == "New Name"
    assert body["data"]["description"] == "New Description"
    

def test_update_category_persists_database(
    client,
    admin_headers,
    category_factory,
    db,
):
    category = category_factory(
        name="Original",
        description="Original Description",
    )

    client.put(
        f"/api/v1/categories/{category.id}",
        headers=admin_headers,
        json={
            "name": "Updated",
            "description": "Updated Description",
        },
    )

    db.refresh(category)

    assert category.name == "Updated"
    assert category.description == "Updated Description"


def test_update_category_not_found(
    client,
    admin_headers,
):
    response = client.put(
        "/api/v1/categories/9999",
        headers=admin_headers,
        json={
            "name": "Updated",
            "description": "Updated",
        },
    )

    assert response.status_code == 404

    body = response.json()

    assert body["success"] is False
    assert body["message"] == "Category not found."


def test_update_category_duplicate_name(
    client,
    admin_headers,
    category_factory,
):
    category_factory(name="Beverages")

    snacks = category_factory(name="Snacks")

    response = client.put(
        f"/api/v1/categories/{snacks.id}",
        headers=admin_headers,
        json={
            "name": "Beverages",
            "description": "Updated",
        },
    )

    assert response.status_code == 400

    body = response.json()

    assert body["success"] is False
    assert body["message"] == (
        "A category with this name already exists."
    )


def test_update_category_requires_authentication(
    client,
    category,
):
    response = client.put(
        f"/api/v1/categories/{category.id}",
        json={
            "name": "Updated",
            "description": "Updated",
        },
    )

    assert response.status_code == 401


def test_update_category_employee_forbidden(
    client,
    employee_headers,
    category,
):
    response = client.put(
        f"/api/v1/categories/{category.id}",
        headers=employee_headers,
        json={
            "name": "Updated Name",
            "description": "Updated Description",
        },
    )

    assert response.status_code == 403

    body = response.json()

    assert body["success"] is False
    
    
def test_update_category_invalid_token(
    client,
    category,
):
    response = client.put(
        f"/api/v1/categories/{category.id}",
        headers={
            "Authorization": "Bearer invalid_token"
        },
        json={
            "name": "Updated Name",
            "description": "Updated Description",
        },
    )

    assert response.status_code == 401

    body = response.json()

    assert body["success"] is False


def test_update_category_invalid_id_validation(
    client,
    admin_headers,
):
    response = client.put(
        "/api/v1/categories/0",
        headers=admin_headers,
        json={
            "name": "Updated Name",
            "description": "Updated Description",
        },
    )

    assert response.status_code == 422


def test_update_category_validation_error(
    client,
    admin_headers,
    category,
):
    response = client.put(
        f"/api/v1/categories/{category.id}",
        headers=admin_headers,
        json={
            "name": "A",
            "description": "Description",
        },
    )

    assert response.status_code == 422
    

def test_update_category_without_description(
    client,
    admin_headers,
    category,
):
    response = client.put(
        f"/api/v1/categories/{category.id}",
        headers=admin_headers,
        json={
            "name": "Updated Name",
            "description": None,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["data"]["name"] == "Updated Name"
    assert body["data"]["description"] is None


# ==================================================
# DELETE CATEGORY
# ==================================================

def test_delete_category_success(
    client,
    admin_headers,
    category,
):
    response = client.delete(
        f"/api/v1/categories/{category.id}",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["message"] == "Category deleted successfully"
    

def test_delete_category_removes_from_database(
    client,
    admin_headers,
    category,
    db,
):
    category_id = category.id

    response = client.delete(
        f"/api/v1/categories/{category_id}",
        headers=admin_headers,
    )

    assert response.status_code == 200

    deleted = (
        db.query(Category)
        .filter(Category.id == category_id)
        .first()
    )

    assert deleted is None


def test_delete_category_not_found(
    client,
    admin_headers,
):
    response = client.delete(
        "/api/v1/categories/9999",
        headers=admin_headers,
    )

    assert response.status_code == 404

    body = response.json()

    assert body["success"] is False
    assert body["message"] == "Category not found."


def test_delete_category_requires_authentication(
    client,
    category,
):
    response = client.delete(
        f"/api/v1/categories/{category.id}",
    )

    assert response.status_code == 401


def test_delete_category_employee_forbidden(
    client,
    employee_headers,
    category,
):
    response = client.delete(
        f"/api/v1/categories/{category.id}",
        headers=employee_headers,
    )

    assert response.status_code == 403

    body = response.json()

    assert body["success"] is False


def test_delete_category_invalid_token(
    client,
    category,
):
    response = client.delete(
        f"/api/v1/categories/{category.id}",
        headers={
            "Authorization": "Bearer invalid_token"
        },
    )

    assert response.status_code == 401

    body = response.json()

    assert body["success"] is False


def test_delete_category_invalid_id_validation(
    client,
    admin_headers,
):
    response = client.delete(
        "/api/v1/categories/0",
        headers=admin_headers,
    )

    assert response.status_code == 422
    

def test_deleted_category_cannot_be_retrieved(
    client,
    admin_headers,
    category,
):
    client.delete(
        f"/api/v1/categories/{category.id}",
        headers=admin_headers,
    )

    response = client.get(
        f"/api/v1/categories/{category.id}",
        headers=admin_headers,
    )

    assert response.status_code == 404

    body = response.json()

    assert body["success"] is False
    assert body["message"] == "Category not found."


def test_delete_category_twice(
    client,
    admin_headers,
    category,
):
    first = client.delete(
        f"/api/v1/categories/{category.id}",
        headers=admin_headers,
    )

    assert first.status_code == 200

    second = client.delete(
        f"/api/v1/categories/{category.id}",
        headers=admin_headers,
    )

    assert second.status_code == 404

    body = second.json()

    assert body["success"] is False
    assert body["message"] == "Category not found."