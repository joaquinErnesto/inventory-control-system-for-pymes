# ==================================================
# CREATE SUPPLIER
# ==================================================

def test_create_supplier_success(
    client,
    admin_headers,
):
    """
    Admin can create a supplier successfully.
    """

    response = client.post(
        "/api/v1/suppliers/",
        headers=admin_headers,
        json={
            "name": "Coca-Cola Cuba",
            "contact_person": "John Doe",
            "phone": "+53 5555 1234",
            "email": "sales@cocacola.cu",
            "address": "Havana, Cuba",
            "is_active": True,
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["success"] is True
    assert body["message"] == "Supplier created successfully"

    supplier = body["data"]

    assert supplier["id"] > 0
    assert supplier["name"] == "Coca-Cola Cuba"
    assert supplier["contact_person"] == "John Doe"
    assert supplier["phone"] == "+53 5555 1234"
    assert supplier["email"] == "sales@cocacola.cu"
    assert supplier["address"] == "Havana, Cuba"
    assert supplier["is_active"] is True

    assert "created_at" in supplier


# ==================================================
# CREATE SUPPLIER - ERROR HANDLING
# ==================================================

def test_create_supplier_duplicate_name(
    client,
    admin_headers,
    supplier_factory,
):
    supplier_factory(name="Coca-Cola Cuba")

    response = client.post(
        "/api/v1/suppliers/",
        headers=admin_headers,
        json={
            "name": "Coca-Cola Cuba",
            "contact_person": "John Doe",
            "phone": "+53 5555 0000",
            "email": "duplicate@test.com",
            "address": "Havana",
            "is_active": True,
        },
    )

    assert response.status_code == 400

    body = response.json()

    assert body["success"] is False
    assert body["message"] == (
        "A supplier with this name already exists."
    )


def test_create_supplier_requires_authentication(client):
    response = client.post(
        "/api/v1/suppliers/",
        json={
            "name": "Supplier Without Auth",
            "contact_person": "John",
            "phone": "+53 5555 0000",
            "email": "supplier@test.com",
            "address": "Baracoa",
            "is_active": True,
        },
    )

    assert response.status_code == 401

    body = response.json()

    assert body["success"] is False


def test_create_supplier_invalid_token(client):
    response = client.post(
        "/api/v1/suppliers/",
        headers={
            "Authorization": "Bearer invalid_token"
        },
        json={
            "name": "Supplier",
            "contact_person": "John",
            "phone": "+53 5555 0000",
            "email": "supplier@test.com",
            "address": "Baracoa",
            "is_active": True,
        },
    )

    assert response.status_code == 401

    body = response.json()

    assert body["success"] is False


def test_create_supplier_employee_forbidden(
    client,
    employee_headers,
):
    response = client.post(
        "/api/v1/suppliers/",
        headers=employee_headers,
        json={
            "name": "Supplier",
            "contact_person": "John",
            "phone": "+53 5555 0000",
            "email": "supplier@test.com",
            "address": "Baracoa",
            "is_active": True,
        },
    )

    assert response.status_code == 403

    body = response.json()

    assert body["success"] is False


def test_create_supplier_validation_error(
    client,
    admin_headers,
):
    response = client.post(
        "/api/v1/suppliers/",
        headers=admin_headers,
        json={
            "name": "AB",
            "contact_person": "John",
            "phone": "+53 5555 0000",
            "email": "supplier@test.com",
            "address": "Baracoa",
            "is_active": True,
        },
    )

    assert response.status_code == 422

    body = response.json()

    assert body["success"] is False


def test_create_supplier_invalid_email(
    client,
    admin_headers,
):
    response = client.post(
        "/api/v1/suppliers/",
        headers=admin_headers,
        json={
            "name": "Supplier",
            "contact_person": "John",
            "phone": "+53 5555 0000",
            "email": "not-an-email",
            "address": "Baracoa",
            "is_active": True,
        },
    )

    assert response.status_code == 422

    body = response.json()

    assert body["success"] is False


# ==================================================
# GET ALL SUPPLIERS
# ==================================================

def test_get_all_suppliers_success(
    client,
    admin_headers,
    supplier_factory,
):
    """
    Admin can retrieve all suppliers.
    """

    supplier_factory(name="Supplier A")
    supplier_factory(name="Supplier B")

    response = client.get(
        "/api/v1/suppliers/",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert len(body["data"]) == 2
    assert body["pagination"]["total_items"] == 2


def test_get_all_suppliers_employee_success(
    client,
    employee_headers,
    supplier_factory,
):
    """
    Employees can retrieve suppliers.
    """

    supplier_factory()

    response = client.get(
        "/api/v1/suppliers/",
        headers=employee_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert len(body["data"]) == 1


def test_get_all_suppliers_empty_database(
    client,
    admin_headers,
):
    """
    Empty database should return an empty list.
    """

    response = client.get(
        "/api/v1/suppliers/",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["data"] == []
    assert body["pagination"]["total_items"] == 0


def test_get_all_suppliers_requires_authentication(
    client,
):
    """
    Authentication is required.
    """

    response = client.get(
        "/api/v1/suppliers/",
    )

    assert response.status_code == 401

    body = response.json()

    assert body["success"] is False


def test_get_all_suppliers_invalid_token(
    client,
):
    """
    Invalid JWT token should be rejected.
    """

    response = client.get(
        "/api/v1/suppliers/",
        headers={
            "Authorization": "Bearer invalid_token"
        },
    )

    assert response.status_code == 401

    body = response.json()

    assert body["success"] is False


# ==================================================
# SEARCH SUPPLIERS
# ==================================================

def test_search_suppliers_by_name(
    client,
    admin_headers,
    supplier_factory,
):
    """
    Search suppliers by company name.
    """

    supplier_factory(
        name="Coca-Cola Cuba",
        contact_person="John Doe",
    )

    supplier_factory(
        name="Nestlé Cuba",
        contact_person="Jane Doe",
    )

    response = client.get(
        "/api/v1/suppliers/search/?q=Coca",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert len(body["data"]) == 1
    assert body["data"][0]["name"] == "Coca-Cola Cuba"


def test_search_suppliers_by_contact_person(
    client,
    admin_headers,
    supplier_factory,
):
    """
    Search suppliers by contact person.
    """

    supplier_factory(
        name="Supplier A",
        contact_person="Carlos Pérez",
    )

    supplier_factory(
        name="Supplier B",
        contact_person="María Gómez",
    )

    response = client.get(
        "/api/v1/suppliers/search/?q=Carlos",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body["data"]) == 1
    assert body["data"][0]["contact_person"] == "Carlos Pérez"


def test_search_suppliers_by_phone(
    client,
    admin_headers,
    supplier_factory,
):
    """
    Search suppliers by phone.
    """

    supplier_factory(
        phone="+53 1111 1111",
    )

    supplier_factory(
        phone="+53 9999 9999",
    )

    response = client.get(
        "/api/v1/suppliers/search/?q=1111",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body["data"]) == 1
    assert body["data"][0]["phone"] == "+53 1111 1111"


def test_search_suppliers_by_email(
    client,
    admin_headers,
    supplier_factory,
):
    """
    Search suppliers by email.
    """

    supplier_factory(
        email="sales@cocacola.com",
    )

    supplier_factory(
        email="info@nestle.com",
    )

    response = client.get(
        "/api/v1/suppliers/search/?q=cocacola",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body["data"]) == 1
    assert body["data"][0]["email"] == "sales@cocacola.com"


def test_search_suppliers_no_results(
    client,
    admin_headers,
    supplier_factory,
):
    """
    Searching with no matches should return an empty list.
    """

    supplier_factory(
        name="Supplier One",
    )

    response = client.get(
        "/api/v1/suppliers/search/?q=NothingHere",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["data"] == []
    assert body["pagination"]["total_items"] == 0

def test_search_suppliers_employee_success(
    client,
    employee_headers,
    supplier_factory,
):
    """
    Employees are allowed to search suppliers.
    """

    supplier_factory(
        name="Pepsi Cuba",
    )

    response = client.get(
        "/api/v1/suppliers/search/?q=Pepsi",
        headers=employee_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body["data"]) == 1


def test_search_suppliers_requires_authentication(
    client,
):
    """
    Authentication is required.
    """

    response = client.get(
        "/api/v1/suppliers/search/?q=test"
    )

    assert response.status_code == 401

    body = response.json()

    assert body["success"] is False


def test_search_suppliers_invalid_token(
    client,
):
    """
    Invalid JWT tokens are rejected.
    """

    response = client.get(
        "/api/v1/suppliers/search/?q=test",
        headers={
            "Authorization": "Bearer invalid_token"
        },
    )

    assert response.status_code == 401

    body = response.json()

    assert body["success"] is False


def test_search_suppliers_empty_query_validation(
    client,
    admin_headers,
):
    """
    Empty query string is invalid.
    """

    response = client.get(
        "/api/v1/suppliers/search/?q=",
        headers=admin_headers,
    )

    assert response.status_code == 422

    body = response.json()

    assert body["success"] is False


def test_search_suppliers_query_too_long(
    client,
    admin_headers,
):
    """
    Query longer than 100 characters is rejected.
    """

    response = client.get(
        f"/api/v1/suppliers/search/?q={'a'*101}",
        headers=admin_headers,
    )

    assert response.status_code == 422

    body = response.json()

    assert body["success"] is False


# ==================================================
# GET SUPPLIER BY ID
# ==================================================

def test_get_supplier_success(
    client,
    admin_headers,
    supplier,
):
    """
    Admin can retrieve a supplier by ID.
    """

    response = client.get(
        f"/api/v1/suppliers/{supplier.id}",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True

    data = body["data"]

    assert data["id"] == supplier.id
    assert data["name"] == supplier.name
    assert data["contact_person"] == supplier.contact_person
    assert data["phone"] == supplier.phone
    assert data["email"] == supplier.email
    assert data["address"] == supplier.address
    assert data["is_active"] == supplier.is_active

    assert "created_at" in data


def test_get_supplier_employee_success(
    client,
    employee_headers,
    supplier,
):
    """
    Employees can retrieve a supplier by ID.
    """

    response = client.get(
        f"/api/v1/suppliers/{supplier.id}",
        headers=employee_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["data"]["id"] == supplier.id


def test_get_supplier_not_found(
    client,
    admin_headers,
):
    """
    Requesting a non-existing supplier should return 404.
    """

    response = client.get(
        "/api/v1/suppliers/999999",
        headers=admin_headers,
    )

    assert response.status_code == 404

    body = response.json()

    assert body["success"] is False
    assert body["message"] == "Supplier not found."


def test_get_supplier_requires_authentication(
    client,
    supplier,
):
    """
    Authentication is required.
    """

    response = client.get(
        f"/api/v1/suppliers/{supplier.id}",
    )

    assert response.status_code == 401

    body = response.json()

    assert body["success"] is False


def test_get_supplier_invalid_token(
    client,
    supplier,
):
    """
    Invalid JWT token should return 401.
    """

    response = client.get(
        f"/api/v1/suppliers/{supplier.id}",
        headers={
            "Authorization": "Bearer invalid_token"
        },
    )

    assert response.status_code == 401

    body = response.json()

    assert body["success"] is False


def test_get_supplier_invalid_id(
    client,
    admin_headers,
):
    """
    IDs must be greater than zero.
    """

    response = client.get(
        "/api/v1/suppliers/0",
        headers=admin_headers,
    )

    assert response.status_code == 422

    body = response.json()

    assert body["success"] is False


# ==================================================
# GET SUPPLIER BY ID - ADDITIONAL TESTS
# ==================================================

def test_get_supplier_returns_exact_database_record(
    client,
    admin_headers,
    supplier_factory,
):
    """
    The endpoint should return exactly the requested supplier,
    even when multiple suppliers exist.
    """

    supplier_factory(name="Supplier A")
    target = supplier_factory(name="Supplier B")
    supplier_factory(name="Supplier C")

    response = client.get(
        f"/api/v1/suppliers/{target.id}",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["data"]["id"] == target.id
    assert body["data"]["name"] == "Supplier B"


def test_get_supplier_preserves_all_fields(
    client,
    admin_headers,
    supplier_factory,
):
    """
    All stored supplier fields should be returned unchanged.
    """

    supplier = supplier_factory(
        name="Nestlé Cuba",
        contact_person="Carlos Pérez",
        phone="+53 51234567",
        email="nestle@example.com",
        address="Santiago de Cuba",
        is_active=False,
    )

    response = client.get(
        f"/api/v1/suppliers/{supplier.id}",
        headers=admin_headers,
    )

    assert response.status_code == 200

    data = response.json()["data"]

    assert data["name"] == "Nestlé Cuba"
    assert data["contact_person"] == "Carlos Pérez"
    assert data["phone"] == "+53 51234567"
    assert data["email"] == "nestle@example.com"
    assert data["address"] == "Santiago de Cuba"
    assert data["is_active"] is False


def test_get_supplier_large_nonexistent_id(
    client,
    admin_headers,
):
    """
    Very large IDs that do not exist should return 404.
    """

    response = client.get(
        "/api/v1/suppliers/999999999",
        headers=admin_headers,
    )

    assert response.status_code == 404

    body = response.json()

    assert body["success"] is False
    assert body["message"] == "Supplier not found."


def test_get_supplier_negative_id(
    client,
    admin_headers,
):
    """
    Negative IDs should fail FastAPI validation.
    """

    response = client.get(
        "/api/v1/suppliers/-1",
        headers=admin_headers,
    )

    assert response.status_code == 422

    body = response.json()

    assert body["success"] is False


def test_get_supplier_response_contains_created_at(
    client,
    admin_headers,
    supplier,
):
    """
    The API response should always include created_at.
    """

    response = client.get(
        f"/api/v1/suppliers/{supplier.id}",
        headers=admin_headers,
    )

    assert response.status_code == 200

    data = response.json()["data"]

    assert "created_at" in data
    assert data["created_at"] is not None
    

# ==================================================
# UPDATE SUPPLIER
# ==================================================

def test_update_supplier_success(
    client,
    admin_headers,
    supplier,
):
    """
    Admin can update an existing supplier.
    """

    response = client.put(
        f"/api/v1/suppliers/{supplier.id}",
        headers=admin_headers,
        json={
            "name": "Updated Supplier",
            "contact_person": "Jane Doe",
            "phone": "+53 7777 8888",
            "email": "updated@example.com",
            "address": "Havana",
            "is_active": False,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["message"] == "Supplier updated successfully"

    data = body["data"]

    assert data["id"] == supplier.id
    assert data["name"] == "Updated Supplier"
    assert data["contact_person"] == "Jane Doe"
    assert data["phone"] == "+53 7777 8888"
    assert data["email"] == "updated@example.com"
    assert data["address"] == "Havana"
    assert data["is_active"] is False


def test_update_supplier_persists_database(
    client,
    admin_headers,
    supplier,
    db,
):
    """
    Changes should be committed to the database.
    """

    response = client.put(
        f"/api/v1/suppliers/{supplier.id}",
        headers=admin_headers,
        json={
            "name": "Persistent Supplier",
            "contact_person": "Peter",
            "phone": "+53 1111 2222",
            "email": "persistent@example.com",
            "address": "Baracoa",
            "is_active": True,
        },
    )

    assert response.status_code == 200

    db.refresh(supplier)

    assert supplier.name == "Persistent Supplier"
    assert supplier.contact_person == "Peter"
    assert supplier.phone == "+53 1111 2222"
    assert supplier.email == "persistent@example.com"
    assert supplier.address == "Baracoa"
    assert supplier.is_active is True


def test_update_supplier_not_found(
    client,
    admin_headers,
):
    """
    Updating a non-existing supplier should return 404.
    """

    response = client.put(
        "/api/v1/suppliers/999999",
        headers=admin_headers,
        json={
            "name": "Supplier",
            "contact_person": "John",
            "phone": "+53 5555",
            "email": "supplier@example.com",
            "address": "Baracoa",
            "is_active": True,
        },
    )

    assert response.status_code == 404

    body = response.json()

    assert body["success"] is False
    assert body["message"] == "Supplier not found."


def test_update_supplier_duplicate_name(
    client,
    admin_headers,
    supplier_factory,
):
    """
    Two suppliers cannot have the same name.
    """

    supplier_a = supplier_factory(
        name="Supplier A",
    )

    supplier_factory(
        name="Supplier B",
    )

    response = client.put(
        f"/api/v1/suppliers/{supplier_a.id}",
        headers=admin_headers,
        json={
            "name": "Supplier B",
            "contact_person": "John",
            "phone": "+53 5555",
            "email": "supplier@example.com",
            "address": "Baracoa",
            "is_active": True,
        },
    )

    assert response.status_code == 400

    body = response.json()

    assert body["success"] is False
    assert body["message"] == (
        "A supplier with this name already exists."
    )


def test_update_supplier_requires_authentication(
    client,
    supplier,
):
    """
    Authentication is required.
    """

    response = client.put(
        f"/api/v1/suppliers/{supplier.id}",
        json={
            "name": "Updated",
            "contact_person": "John",
            "phone": "+53 5555",
            "email": "supplier@example.com",
            "address": "Baracoa",
            "is_active": True,
        },
    )

    assert response.status_code == 401


def test_update_supplier_employee_forbidden(
    client,
    employee_headers,
    supplier,
):
    """
    Employees cannot update suppliers.
    """

    response = client.put(
        f"/api/v1/suppliers/{supplier.id}",
        headers=employee_headers,
        json={
            "name": "Updated",
            "contact_person": "John",
            "phone": "+53 5555",
            "email": "supplier@example.com",
            "address": "Baracoa",
            "is_active": True,
        },
    )

    assert response.status_code == 403


# ==================================================
# UPDATE SUPPLIER - VALIDATION
# ==================================================

def test_update_supplier_invalid_token(
    client,
    supplier,
):
    """
    Invalid JWT tokens should be rejected.
    """

    response = client.put(
        f"/api/v1/suppliers/{supplier.id}",
        headers={
            "Authorization": "Bearer invalid_token"
        },
        json={
            "name": "Updated Supplier",
            "contact_person": "John",
            "phone": "+53 5555",
            "email": "supplier@example.com",
            "address": "Baracoa",
            "is_active": True,
        },
    )

    assert response.status_code == 401

    body = response.json()

    assert body["success"] is False


def test_update_supplier_invalid_id(
    client,
    admin_headers,
):
    """
    Supplier ID must be greater than zero.
    """

    response = client.put(
        "/api/v1/suppliers/0",
        headers=admin_headers,
        json={
            "name": "Updated Supplier",
            "contact_person": "John",
            "phone": "+53 5555",
            "email": "supplier@example.com",
            "address": "Baracoa",
            "is_active": True,
        },
    )

    assert response.status_code == 422

    body = response.json()

    assert body["success"] is False


def test_update_supplier_negative_id(
    client,
    admin_headers,
):
    """
    Negative supplier IDs are invalid.
    """

    response = client.put(
        "/api/v1/suppliers/-1",
        headers=admin_headers,
        json={
            "name": "Updated Supplier",
            "contact_person": "John",
            "phone": "+53 5555",
            "email": "supplier@example.com",
            "address": "Baracoa",
            "is_active": True,
        },
    )

    assert response.status_code == 422

    body = response.json()

    assert body["success"] is False


def test_update_supplier_invalid_email(
    client,
    admin_headers,
    supplier,
):
    """
    Invalid email addresses should fail validation.
    """

    response = client.put(
        f"/api/v1/suppliers/{supplier.id}",
        headers=admin_headers,
        json={
            "name": "Updated Supplier",
            "contact_person": "John",
            "phone": "+53 5555",
            "email": "not-an-email",
            "address": "Baracoa",
            "is_active": True,
        },
    )

    assert response.status_code == 422

    body = response.json()

    assert body["success"] is False


def test_update_supplier_name_too_short(
    client,
    admin_headers,
    supplier,
):
    """
    Supplier name must contain at least 3 characters.
    """

    response = client.put(
        f"/api/v1/suppliers/{supplier.id}",
        headers=admin_headers,
        json={
            "name": "AB",
            "contact_person": "John",
            "phone": "+53 5555",
            "email": "supplier@example.com",
            "address": "Baracoa",
            "is_active": True,
        },
    )

    assert response.status_code == 422

    body = response.json()

    assert body["success"] is False


def test_update_supplier_contact_person_too_short(
    client,
    admin_headers,
    supplier,
):
    """
    Contact person must contain at least 3 characters.
    """

    response = client.put(
        f"/api/v1/suppliers/{supplier.id}",
        headers=admin_headers,
        json={
            "name": "Updated Supplier",
            "contact_person": "AB",
            "phone": "+53 5555",
            "email": "supplier@example.com",
            "address": "Baracoa",
            "is_active": True,
        },
    )

    assert response.status_code == 422

    body = response.json()

    assert body["success"] is False
    
    
# ==================================================
# DELETE SUPPLIER
# ==================================================

def test_delete_supplier_success(
    client,
    admin_headers,
    supplier,
    db,
):
    """
    Admin can delete an existing supplier.
    """

    supplier_id = supplier.id

    response = client.delete(
        f"/api/v1/suppliers/{supplier_id}",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["message"] == "Supplier deleted successfully"

    from app.models.core import Supplier

    deleted_supplier = (
        db.query(Supplier)
        .filter(Supplier.id == supplier_id)
        .first()
    )

    assert deleted_supplier is None


def test_delete_supplier_not_found(
    client,
    admin_headers,
):
    """
    Deleting a non-existing supplier should return 404.
    """

    response = client.delete(
        "/api/v1/suppliers/999999",
        headers=admin_headers,
    )

    assert response.status_code == 404

    body = response.json()

    assert body["success"] is False
    assert body["message"] == "Supplier not found."


def test_delete_supplier_requires_authentication(
    client,
    supplier,
):
    """
    Authentication is required.
    """

    response = client.delete(
        f"/api/v1/suppliers/{supplier.id}",
    )

    assert response.status_code == 401

    body = response.json()

    assert body["success"] is False


def test_delete_supplier_invalid_token(
    client,
    supplier,
):
    """
    Invalid JWT token should return 401.
    """

    response = client.delete(
        f"/api/v1/suppliers/{supplier.id}",
        headers={
            "Authorization": "Bearer invalid_token"
        },
    )

    assert response.status_code == 401

    body = response.json()

    assert body["success"] is False


def test_delete_supplier_employee_forbidden(
    client,
    employee_headers,
    supplier,
):
    """
    Employees cannot delete suppliers.
    """

    response = client.delete(
        f"/api/v1/suppliers/{supplier.id}",
        headers=employee_headers,
    )

    assert response.status_code == 403

    body = response.json()

    assert body["success"] is False


def test_delete_supplier_persists_database(
    client,
    admin_headers,
    supplier_factory,
    db,
):
    """
    Supplier should be permanently removed from the database.
    """

    supplier = supplier_factory(
        name="Supplier To Delete",
    )

    supplier_id = supplier.id

    response = client.delete(
        f"/api/v1/suppliers/{supplier_id}",
        headers=admin_headers,
    )

    assert response.status_code == 200

    from app.models.core import Supplier

    db.expire_all()

    assert (
        db.query(Supplier)
        .filter(Supplier.id == supplier_id)
        .first()
        is None
    )


# ==================================================
# DELETE SUPPLIER - VALIDATION
# ==================================================

def test_delete_supplier_invalid_id(
    client,
    admin_headers,
):
    """
    Supplier ID must be greater than zero.
    """

    response = client.delete(
        "/api/v1/suppliers/0",
        headers=admin_headers,
    )

    assert response.status_code == 422

    body = response.json()

    assert body["success"] is False


def test_delete_supplier_negative_id(
    client,
    admin_headers,
):
    """
    Negative supplier IDs are invalid.
    """

    response = client.delete(
        "/api/v1/suppliers/-1",
        headers=admin_headers,
    )

    assert response.status_code == 422

    body = response.json()

    assert body["success"] is False


def test_delete_supplier_twice_returns_not_found(
    client,
    admin_headers,
    supplier,
):
    """
    Deleting the same supplier twice should return 404
    on the second attempt.
    """

    response = client.delete(
        f"/api/v1/suppliers/{supplier.id}",
        headers=admin_headers,
    )

    assert response.status_code == 200

    response = client.delete(
        f"/api/v1/suppliers/{supplier.id}",
        headers=admin_headers,
    )

    assert response.status_code == 404

    body = response.json()

    assert body["success"] is False
    assert body["message"] == "Supplier not found."