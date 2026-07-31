# ==================================================
# CREATE CUSTOMER
# ==================================================

def test_create_customer_success(
    client,
    admin_headers,
):
    """
    Admin can create a customer successfully.
    """

    response = client.post(
        "/api/v1/customers/",
        headers=admin_headers,
        json={
            "name": "John Doe",
            "identification_number": "12345678901",
            "phone": "+53 5555 1234",
            "email": "john@example.com",
            "address": "Baracoa, Guantánamo",
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["success"] is True
    assert body["message"] == "Customer created successfully"

    customer = body["data"]

    assert customer["id"] > 0
    assert customer["name"] == "John Doe"
    assert customer["identification_number"] == "12345678901"
    assert customer["phone"] == "+53 5555 1234"
    assert customer["email"] == "john@example.com"
    assert customer["address"] == "Baracoa, Guantánamo"

    assert "created_at" in customer


def test_create_customer_duplicate_identification(
    client,
    admin_headers,
    customer_factory,
):
    """
    Creating two customers with the same
    identification number should return HTTP 400.
    """

    customer_factory(
        identification_number="99999999999",
    )

    response = client.post(
        "/api/v1/customers/",
        headers=admin_headers,
        json={
            "name": "Another Customer",
            "identification_number": "99999999999",
            "phone": "+53 8888 8888",
            "email": "another@example.com",
            "address": "Havana",
        },
    )

    assert response.status_code == 400

    body = response.json()

    assert body["success"] is False
    assert body["message"] == (
        "A customer with this identification number already exists."
    )


def test_create_customer_requires_authentication(
    client,
):
    """
    Creating a customer without authentication
    should return HTTP 401.
    """

    response = client.post(
        "/api/v1/customers/",
        json={
            "name": "John Doe",
            "identification_number": "12345678901",
            "phone": "+53 5555 1234",
            "email": "john@example.com",
            "address": "Baracoa",
        },
    )

    assert response.status_code == 401


def test_create_customer_invalid_token(
    client,
):
    """
    Invalid JWT tokens should not be accepted.
    """

    response = client.post(
        "/api/v1/customers/",
        headers={
            "Authorization": "Bearer invalid_token"
        },
        json={
            "name": "John Doe",
            "identification_number": "12345678901",
            "phone": "+53 5555 1234",
            "email": "john@example.com",
            "address": "Baracoa",
        },
    )

    assert response.status_code == 401


def test_create_customer_employee_forbidden(
    client,
    employee_headers,
):
    """
    Employees cannot create customers.
    """

    response = client.post(
        "/api/v1/customers/",
        headers=employee_headers,
        json={
            "name": "John Doe",
            "identification_number": "12345678901",
            "phone": "+53 5555 1234",
            "email": "john@example.com",
            "address": "Baracoa",
        },
    )

    assert response.status_code == 403


# ==================================================
# CREATE CUSTOMER - VALIDATION & ERRORS
# ==================================================

def test_create_customer_validation_error(
    client,
    admin_headers,
):
    """
    Customer name must contain at least 3 characters.
    """

    response = client.post(
        "/api/v1/customers/",
        headers=admin_headers,
        json={
            "name": "AB",
            "identification_number": "12345678901",
            "phone": "+53 5555 1234",
            "email": "john@example.com",
            "address": "Baracoa",
        },
    )

    assert response.status_code == 422

    body = response.json()

    assert body["success"] is False


def test_create_customer_invalid_email(
    client,
    admin_headers,
):
    """
    Invalid email addresses should be rejected.
    """

    response = client.post(
        "/api/v1/customers/",
        headers=admin_headers,
        json={
            "name": "John Doe",
            "identification_number": "12345678901",
            "phone": "+53 5555 1234",
            "email": "not-an-email",
            "address": "Baracoa",
        },
    )

    assert response.status_code == 422

    body = response.json()

    assert body["success"] is False


def test_create_customer_without_identification_number(
    client,
    admin_headers,
):
    """
    Identification number is optional.
    """

    response = client.post(
        "/api/v1/customers/",
        headers=admin_headers,
        json={
            "name": "John Doe",
            "phone": "+53 5555 1234",
            "email": "john@example.com",
            "address": "Baracoa",
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["success"] is True
    assert body["data"]["identification_number"] is None


def test_create_customer_without_email(
    client,
    admin_headers,
):
    """
    Email is optional.
    """

    response = client.post(
        "/api/v1/customers/",
        headers=admin_headers,
        json={
            "name": "John Doe",
            "identification_number": "77777777777",
            "phone": "+53 5555 1234",
            "address": "Baracoa",
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["success"] is True
    assert body["data"]["email"] is None


def test_create_customer_with_minimum_required_fields(
    client,
    admin_headers,
):
    """
    Customer can be created using only the required field.
    """

    response = client.post(
        "/api/v1/customers/",
        headers=admin_headers,
        json={
            "name": "Minimal Customer",
        },
    )

    assert response.status_code == 201

    body = response.json()

    customer = body["data"]

    assert body["success"] is True
    assert customer["name"] == "Minimal Customer"
    assert customer["identification_number"] is None
    assert customer["phone"] is None
    assert customer["email"] is None
    assert customer["address"] is None


# ==================================================
# GET ALL CUSTOMERS
# ==================================================

def test_get_all_customers_success(
    client,
    admin_headers,
    customer_factory,
):
    """
    Admin can retrieve the customer list.
    """

    customer_factory(name="Alice")
    customer_factory(name="Bob")

    response = client.get(
        "/api/v1/customers/",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()
    
    # print(body)

    assert body["success"] is True

    assert "data" in body
    assert "pagination" in body

    assert len(body["data"]) >= 2

    pagination = body["pagination"]

    assert pagination["page"] == 1
    assert pagination["page_size"] == 100
    assert pagination["total_items"] >= 2
    assert pagination["total_pages"] >= 1
    assert pagination["has_previous"] is False


def test_get_all_customers_employee_success(
    client,
    employee_headers,
    customer_factory,
):
    """
    Employees can retrieve customers.
    """

    customer_factory(name="Customer One")

    response = client.get(
        "/api/v1/customers/",
        headers=employee_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert len(body["data"]) >= 1


def test_get_all_customers_requires_authentication(
    client,
):
    """
    Authentication is required.
    """

    response = client.get(
        "/api/v1/customers/",
    )

    assert response.status_code == 401


def test_get_all_customers_invalid_token(
    client,
):
    """
    Invalid JWT tokens should return 401.
    """

    response = client.get(
        "/api/v1/customers/",
        headers={
            "Authorization": "Bearer invalid_token"
        },
    )

    assert response.status_code == 401


def test_get_all_customers_pagination(
    client,
    admin_headers,
    customer_factory,
):
    """
    Pagination should respect skip and limit.
    """

    for i in range(5):
        customer_factory(
            name=f"Customer {i}"
        )

    response = client.get(
        "/api/v1/customers/?skip=1&limit=2",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()
    
    # print(body)

    assert len(body["data"]) == 2

    pagination = body["pagination"]

    assert pagination["page"] == 1
    assert pagination["page_size"] == 2
    assert pagination["total_items"] == 5
    assert pagination["total_pages"] == 3
    assert pagination["has_next"] is True
    assert pagination["has_previous"] is False


def test_get_all_customers_sort_name_desc(
    client,
    admin_headers,
    customer_factory,
):
    """
    Customers can be sorted by name descending.
    """

    customer_factory(name="Alpha")
    customer_factory(name="Zulu")

    response = client.get(
        "/api/v1/customers/?sort=name&order=desc",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    names = [
        customer["name"]
        for customer in body["data"]
    ]

    assert names == sorted(
        names,
        reverse=True,
    )


def test_get_all_customers_sort_created_at(
    client,
    admin_headers,
    customer_factory,
):
    """
    Customers can be sorted by creation date.
    """

    customer_factory(name="First")
    customer_factory(name="Second")

    response = client.get(
        "/api/v1/customers/?sort=created_at&order=asc",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert len(body["data"]) >= 2


# ==================================================
# GET ALL CUSTOMERS - ERROR HANDLING
# ==================================================

def test_get_all_customers_invalid_sort_field(
    client,
    admin_headers,
):
    """
    Invalid sort fields should return HTTP 400.
    """

    response = client.get(
        "/api/v1/customers/?sort=invalid_field",
        headers=admin_headers,
    )

    assert response.status_code == 400

    body = response.json()

    assert body["success"] is False
    assert "Invalid sort field" in body["message"]


def test_get_all_customers_invalid_order(
    client,
    admin_headers,
):
    """
    Invalid order values should fail validation.
    """

    response = client.get(
        "/api/v1/customers/?order=ascending",
        headers=admin_headers,
    )

    assert response.status_code == 422

    body = response.json()

    assert body["success"] is False


def test_get_all_customers_negative_skip(
    client,
    admin_headers,
):
    """
    Skip cannot be negative.
    """

    response = client.get(
        "/api/v1/customers/?skip=-1",
        headers=admin_headers,
    )

    assert response.status_code == 422

    body = response.json()

    assert body["success"] is False


def test_get_all_customers_limit_zero(
    client,
    admin_headers,
):
    """
    Limit must be greater than zero.
    """

    response = client.get(
        "/api/v1/customers/?limit=0",
        headers=admin_headers,
    )

    assert response.status_code == 422

    body = response.json()

    assert body["success"] is False


def test_get_all_customers_limit_above_maximum(
    client,
    admin_headers,
):
    """
    Limit greater than 100 should fail validation.
    """

    response = client.get(
        "/api/v1/customers/?limit=101",
        headers=admin_headers,
    )

    assert response.status_code == 422

    body = response.json()

    assert body["success"] is False


# ==================================================
# SEARCH CUSTOMERS
# ==================================================

def test_search_customers_by_name(
    client,
    admin_headers,
    customer_factory,
):
    """
    Customers can be searched by name.
    """

    customer_factory(name="Alice Johnson")
    customer_factory(name="Bob Smith")

    response = client.get(
        "/api/v1/customers/search/?q=Alice",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert len(body["data"]) == 1
    assert body["data"][0]["name"] == "Alice Johnson"


def test_search_customers_by_identification_number(
    client,
    admin_headers,
    customer_factory,
):
    """
    Customers can be searched by identification number.
    """

    customer_factory(
        name="Customer",
        identification_number="1234567890",
    )

    response = client.get(
        "/api/v1/customers/search/?q=1234567890",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body["data"]) == 1
    assert (
        body["data"][0]["identification_number"]
        == "1234567890"
    )


def test_search_customers_by_phone(
    client,
    admin_headers,
    customer_factory,
):
    """
    Customers can be searched by phone.
    """

    customer_factory(
        name="Phone Customer",
        phone="+53 7777 9999",
    )

    response = client.get(
        "/api/v1/customers/search/?q=7777",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body["data"]) == 1
    assert body["data"][0]["phone"] == "+53 7777 9999"


def test_search_customers_by_email(
    client,
    admin_headers,
    customer_factory,
):
    """
    Customers can be searched by email.
    """

    customer_factory(
        name="Email Customer",
        email="customer@example.com",
    )

    response = client.get(
        "/api/v1/customers/search/?q=customer@example.com",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body["data"]) == 1
    assert body["data"][0]["email"] == "customer@example.com"


def test_search_customers_multiple_results(
    client,
    admin_headers,
    customer_factory,
):
    """
    Search should return multiple matching customers.
    """

    customer_factory(name="Carlos Perez")
    customer_factory(name="Carlos Diaz")
    customer_factory(name="Juan Lopez")

    response = client.get(
        "/api/v1/customers/search/?q=Carlos",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body["data"]) == 2


def test_search_customers_no_results(
    client,
    admin_headers,
):
    """
    Searching for a nonexistent customer should
    return an empty list.
    """

    response = client.get(
        "/api/v1/customers/search/?q=DoesNotExist",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["data"] == []


def test_search_customers_employee_success(
    client,
    employee_headers,
    customer_factory,
):
    """
    Employees can search customers.
    """

    customer_factory(name="Employee Search")

    response = client.get(
        "/api/v1/customers/search/?q=Employee",
        headers=employee_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body["data"]) == 1


def test_search_customers_requires_authentication(
    client,
):
    """
    Authentication is required.
    """

    response = client.get(
        "/api/v1/customers/search/?q=John"
    )

    assert response.status_code == 401

    body = response.json()

    assert body["success"] is False


def test_search_customers_invalid_token(
    client,
):
    """
    Invalid JWT tokens should not be accepted.
    """

    response = client.get(
        "/api/v1/customers/search/?q=John",
        headers={
            "Authorization": "Bearer invalid_token"
        },
    )

    assert response.status_code == 401

    body = response.json()

    assert body["success"] is False


def test_search_customers_pagination(
    client,
    admin_headers,
    customer_factory,
):
    """
    Search results should support pagination.
    """

    for i in range(5):
        customer_factory(
            name=f"Customer {i}"
        )

    response = client.get(
        "/api/v1/customers/search/?q=Customer&skip=1&limit=2",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body["data"]) == 2

    pagination = body["pagination"]

    assert pagination["page_size"] == 2
    assert pagination["total_items"] == 5


# ==================================================
# GET CUSTOMER BY ID
# ==================================================

def test_get_customer_success(
    client,
    admin_headers,
    customer,
):
    """
    Admin can retrieve a customer by ID.
    """

    response = client.get(
        f"/api/v1/customers/{customer.id}",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True

    retrieved = body["data"]

    assert retrieved["id"] == customer.id
    assert retrieved["name"] == customer.name
    assert (
        retrieved["identification_number"]
        == customer.identification_number
    )
    assert retrieved["phone"] == customer.phone
    assert retrieved["email"] == customer.email
    assert retrieved["address"] == customer.address


def test_get_customer_employee_success(
    client,
    employee_headers,
    customer,
):
    """
    Employees can retrieve a customer by ID.
    """

    response = client.get(
        f"/api/v1/customers/{customer.id}",
        headers=employee_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["data"]["id"] == customer.id


def test_get_customer_not_found(
    client,
    admin_headers,
):
    """
    Requesting a non-existing customer returns 404.
    """

    response = client.get(
        "/api/v1/customers/999999",
        headers=admin_headers,
    )

    assert response.status_code == 404

    body = response.json()

    assert body["success"] is False
    assert body["message"] == "Customer not found."


def test_get_customer_requires_authentication(
    client,
    customer,
):
    """
    Authentication is required.
    """

    response = client.get(
        f"/api/v1/customers/{customer.id}",
    )

    assert response.status_code == 401

    body = response.json()

    assert body["success"] is False


def test_get_customer_invalid_token(
    client,
    customer,
):
    """
    Invalid JWT tokens are rejected.
    """

    response = client.get(
        f"/api/v1/customers/{customer.id}",
        headers={
            "Authorization": "Bearer invalid_token"
        },
    )

    assert response.status_code == 401

    body = response.json()

    assert body["success"] is False


def test_get_customer_invalid_id_validation(
    client,
    admin_headers,
):
    """
    Customer ID must be greater than zero.
    """

    response = client.get(
        "/api/v1/customers/0",
        headers=admin_headers,
    )

    assert response.status_code == 422

    body = response.json()

    assert body["success"] is False


# ==================================================
# UPDATE CUSTOMER
# ==================================================

def test_update_customer_success(
    client,
    admin_headers,
    customer_factory,
):
    """
    Admin can update a customer successfully.
    """

    customer = customer_factory(
        name="John Doe",
        identification_number="123456789",
    )

    response = client.put(
        f"/api/v1/customers/{customer.id}",
        headers=admin_headers,
        json={
            "name": "John Updated",
            "identification_number": "987654321",
            "phone": "+53 5555 9999",
            "email": "updated@example.com",
            "address": "Havana, Cuba",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["message"] == "Customer updated successfully"

    data = body["data"]

    assert data["id"] == customer.id
    assert data["name"] == "John Updated"
    assert data["identification_number"] == "987654321"
    assert data["phone"] == "+53 5555 9999"
    assert data["email"] == "updated@example.com"
    assert data["address"] == "Havana, Cuba"


def test_update_customer_same_identification_allowed(
    client,
    admin_headers,
    customer_factory,
):
    """
    Updating a customer without changing the identification
    number should succeed.
    """

    customer = customer_factory(
        identification_number="ABC123"
    )

    response = client.put(
        f"/api/v1/customers/{customer.id}",
        headers=admin_headers,
        json={
            "name": "Updated Name",
            "identification_number": "ABC123",
            "phone": "+53 8888",
            "email": "updated@example.com",
            "address": "New Address",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["data"]["identification_number"] == "ABC123"


# ==================================================
# UPDATE CUSTOMER - ERROR HANDLING
# ==================================================

def test_update_customer_not_found(
    client,
    admin_headers,
):
    """
    Updating a non-existing customer should return 404.
    """

    response = client.put(
        "/api/v1/customers/999999",
        headers=admin_headers,
        json={
            "name": "Updated Customer",
            "identification_number": "123456789",
            "phone": "+53 5555 0000",
            "email": "updated@example.com",
            "address": "Havana",
        },
    )

    assert response.status_code == 404

    body = response.json()

    assert body["success"] is False
    assert body["message"] == "Customer not found."


def test_update_customer_duplicate_identification(
    client,
    admin_headers,
    customer_factory,
):
    """
    Updating a customer using another customer's identification number
    should return HTTP 400.
    """

    customer1 = customer_factory(
        name="Customer One",
        identification_number="111111111",
    )

    customer2 = customer_factory(
        name="Customer Two",
        identification_number="222222222",
    )

    response = client.put(
        f"/api/v1/customers/{customer2.id}",
        headers=admin_headers,
        json={
            "name": "Customer Two",
            "identification_number": customer1.identification_number,
            "phone": customer2.phone,
            "email": customer2.email,
            "address": customer2.address,
        },
    )

    assert response.status_code == 400

    body = response.json()

    assert body["success"] is False
    assert body["message"] == (
        "A customer with this identification number already exists."
    )


def test_update_customer_requires_authentication(
    client,
    customer,
):
    """
    Updating a customer without authentication
    should return HTTP 401.
    """

    response = client.put(
        f"/api/v1/customers/{customer.id}",
        json={
            "name": "Updated",
            "identification_number": customer.identification_number,
            "phone": customer.phone,
            "email": customer.email,
            "address": customer.address,
        },
    )

    assert response.status_code == 401

    body = response.json()

    assert body["success"] is False


def test_update_customer_invalid_token(
    client,
    customer,
):
    """
    Invalid JWT tokens should not be accepted.
    """

    response = client.put(
        f"/api/v1/customers/{customer.id}",
        headers={
            "Authorization": "Bearer invalid_token"
        },
        json={
            "name": "Updated",
            "identification_number": customer.identification_number,
            "phone": customer.phone,
            "email": customer.email,
            "address": customer.address,
        },
    )

    assert response.status_code == 401

    body = response.json()

    assert body["success"] is False


def test_update_customer_employee_forbidden(
    client,
    employee_headers,
    customer,
):
    """
    Employees cannot update customers.
    """

    response = client.put(
        f"/api/v1/customers/{customer.id}",
        headers=employee_headers,
        json={
            "name": "Updated",
            "identification_number": customer.identification_number,
            "phone": customer.phone,
            "email": customer.email,
            "address": customer.address,
        },
    )

    assert response.status_code == 403

    body = response.json()

    assert body["success"] is False


def test_update_customer_validation_error(
    client,
    admin_headers,
    customer,
):
    """
    Invalid payload should return HTTP 422.
    """

    response = client.put(
        f"/api/v1/customers/{customer.id}",
        headers=admin_headers,
        json={
            "name": "AB",
            "identification_number": customer.identification_number,
            "phone": customer.phone,
            "email": customer.email,
            "address": customer.address,
        },
    )

    assert response.status_code == 422

    body = response.json()

    assert body["success"] is False


def test_update_customer_invalid_email(
    client,
    admin_headers,
    customer,
):
    """
    Invalid email should return HTTP 422.
    """

    response = client.put(
        f"/api/v1/customers/{customer.id}",
        headers=admin_headers,
        json={
            "name": customer.name,
            "identification_number": customer.identification_number,
            "phone": customer.phone,
            "email": "not-an-email",
            "address": customer.address,
        },
    )

    assert response.status_code == 422

    body = response.json()

    assert body["success"] is False


# ==================================================
# DELETE CUSTOMER
# ==================================================

def test_delete_customer_success(
    client,
    admin_headers,
    customer,
):
    """
    Admin can delete a customer successfully.
    """

    response = client.delete(
        f"/api/v1/customers/{customer.id}",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["message"] == "Customer deleted successfully"

    # Verify it was actually removed
    response = client.get(
        f"/api/v1/customers/{customer.id}",
        headers=admin_headers,
    )

    assert response.status_code == 404


def test_delete_customer_not_found(
    client,
    admin_headers,
):
    """
    Deleting a non-existing customer should return HTTP 404.
    """

    response = client.delete(
        "/api/v1/customers/999999",
        headers=admin_headers,
    )

    assert response.status_code == 404

    body = response.json()

    assert body["success"] is False
    assert body["message"] == "Customer not found."


def test_delete_customer_requires_authentication(
    client,
    customer,
):
    """
    Authentication is required.
    """

    response = client.delete(
        f"/api/v1/customers/{customer.id}",
    )

    assert response.status_code == 401

    body = response.json()

    assert body["success"] is False


def test_delete_customer_invalid_token(
    client,
    customer,
):
    """
    Invalid JWT tokens should not be accepted.
    """

    response = client.delete(
        f"/api/v1/customers/{customer.id}",
        headers={
            "Authorization": "Bearer invalid_token"
        },
    )

    assert response.status_code == 401

    body = response.json()

    assert body["success"] is False


def test_delete_customer_employee_forbidden(
    client,
    employee_headers,
    customer,
):
    """
    Employees cannot delete customers.
    """

    response = client.delete(
        f"/api/v1/customers/{customer.id}",
        headers=employee_headers,
    )

    assert response.status_code == 403

    body = response.json()

    assert body["success"] is False


def test_delete_customer_invalid_id_validation(
    client,
    admin_headers,
):
    """
    Customer ID must be greater than zero.
    """

    response = client.delete(
        "/api/v1/customers/0",
        headers=admin_headers,
    )

    assert response.status_code == 422

    body = response.json()

    assert body["success"] is False


# ==================================================
# DELETE CUSTOMER - ERROR HANDLING
# ==================================================

def test_delete_customer_negative_id(
    client,
    admin_headers,
):
    """
    Negative customer IDs should fail validation.
    """

    response = client.delete(
        "/api/v1/customers/-1",
        headers=admin_headers,
    )

    assert response.status_code == 422

    body = response.json()

    assert body["success"] is False


def test_delete_customer_invalid_path_parameter(
    client,
    admin_headers,
):
    """
    Non-integer customer IDs should fail validation.
    """

    response = client.delete(
        "/api/v1/customers/not-an-id",
        headers=admin_headers,
    )

    assert response.status_code == 422

    body = response.json()

    assert body["success"] is False


def test_delete_customer_twice(
    client,
    admin_headers,
    customer,
):
    """
    Deleting the same customer twice should return 404
    on the second request.
    """

    response = client.delete(
        f"/api/v1/customers/{customer.id}",
        headers=admin_headers,
    )

    assert response.status_code == 200

    response = client.delete(
        f"/api/v1/customers/{customer.id}",
        headers=admin_headers,
    )

    assert response.status_code == 404

    body = response.json()

    assert body["success"] is False
    assert body["message"] == "Customer not found."