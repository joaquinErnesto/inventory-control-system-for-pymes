# ==================================================
# CREATE PRODUCT
# ==================================================

def test_create_product_success(
    client,
    admin_headers,
    category,
):
    """
    Admin can create a product successfully.
    """

    response = client.post(
        "/api/v1/products/",
        headers=admin_headers,
        json={
            "category_id": category.id,
            "name": "Coca-Cola 500ml",
            "description": "Soft drink",
            "sku_or_barcode": "SKU-COCA-001",
            "unit_of_measure": "Units",
            "base_price": "25.50",
            "min_stock_threshold": 10,
            "is_active": True,
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["success"] is True
    assert body["message"] == "Product created successfully"

    product = body["data"]

    assert product["id"] > 0
    assert product["category_id"] == category.id
    assert product["name"] == "Coca-Cola 500ml"
    assert product["description"] == "Soft drink"
    assert product["sku_or_barcode"] == "SKU-COCA-001"
    assert product["unit_of_measure"] == "Units"
    assert product["base_price"] == "25.50"
    assert product["min_stock_threshold"] == 10
    assert product["is_active"] is True

    assert "created_at" in product


def test_create_product_employee_forbidden(
    client,
    employee_headers,
    category,
):
    """
    Employees cannot create products.
    """

    response = client.post(
        "/api/v1/products/",
        headers=employee_headers,
        json={
            "category_id": category.id,
            "name": "Pepsi",
            "description": "Drink",
            "sku_or_barcode": "SKU-PEPSI-001",
            "unit_of_measure": "Units",
            "base_price": "20.00",
            "min_stock_threshold": 5,
            "is_active": True,
        },
    )

    assert response.status_code == 403

    body = response.json()

    assert body["success"] is False


def test_create_product_requires_authentication(
    client,
    category,
):
    """
    Authentication is required.
    """

    response = client.post(
        "/api/v1/products/",
        json={
            "category_id": category.id,
            "name": "Pepsi",
            "description": "Drink",
            "sku_or_barcode": "SKU-PEPSI-001",
            "unit_of_measure": "Units",
            "base_price": "20.00",
            "min_stock_threshold": 5,
            "is_active": True,
        },
    )

    assert response.status_code == 401

    body = response.json()

    assert body["success"] is False


def test_create_product_invalid_token(
    client,
    category,
):
    """
    Invalid JWT tokens should not be accepted.
    """

    response = client.post(
        "/api/v1/products/",
        headers={
            "Authorization": "Bearer invalid_token"
        },
        json={
            "category_id": category.id,
            "name": "Pepsi",
            "description": "Drink",
            "sku_or_barcode": "SKU-PEPSI-001",
            "unit_of_measure": "Units",
            "base_price": "20.00",
            "min_stock_threshold": 5,
            "is_active": True,
        },
    )

    assert response.status_code == 401

    body = response.json()

    assert body["success"] is False


# ==================================================
# CREATE PRODUCT - ERROR HANDLING
# ==================================================

def test_create_product_category_not_found(
    client,
    admin_headers,
):
    """
    Category must exist.
    """

    response = client.post(
        "/api/v1/products/",
        headers=admin_headers,
        json={
            "category_id": 999999,
            "name": "Orange Juice",
            "description": "Drink",
            "sku_or_barcode": "SKU-001",
            "unit_of_measure": "Units",
            "base_price": "15.00",
            "min_stock_threshold": 5,
            "is_active": True,
        },
    )

    assert response.status_code == 400

    body = response.json()

    assert body["success"] is False
    assert body["message"] == (
        "Category with ID 999999 does not exist."
    )


def test_create_product_duplicate_sku(
    client,
    admin_headers,
    product_factory,
):
    """
    SKU/barcode must be unique.
    """

    product_factory(
        sku_or_barcode="SKU-DUPLICATE"
    )

    response = client.post(
        "/api/v1/products/",
        headers=admin_headers,
        json={
            "category_id": 1,
            "name": "Another Product",
            "description": "Description",
            "sku_or_barcode": "SKU-DUPLICATE",
            "unit_of_measure": "Units",
            "base_price": "20.00",
            "min_stock_threshold": 5,
            "is_active": True,
        },
    )

    assert response.status_code == 400

    body = response.json()

    assert body["success"] is False
    assert body["message"] == (
        "A product with this SKU or barcode already exists."
    )


def test_create_product_name_too_short(
    client,
    admin_headers,
    category,
):
    """
    Product name must contain at least 3 characters.
    """

    response = client.post(
        "/api/v1/products/",
        headers=admin_headers,
        json={
            "category_id": category.id,
            "name": "AB",
            "description": "Description",
            "sku_or_barcode": "SKU-001",
            "unit_of_measure": "Units",
            "base_price": "20.00",
            "min_stock_threshold": 5,
            "is_active": True,
        },
    )

    assert response.status_code == 422

    body = response.json()

    assert body["success"] is False


def test_create_product_invalid_unit_of_measure(
    client,
    admin_headers,
    category,
):
    """
    UnitOfMeasure must be a valid enum value.
    """

    response = client.post(
        "/api/v1/products/",
        headers=admin_headers,
        json={
            "category_id": category.id,
            "name": "Rice",
            "description": "Food",
            "sku_or_barcode": "SKU-RICE",
            "unit_of_measure": "Gallons",
            "base_price": "50.00",
            "min_stock_threshold": 5,
            "is_active": True,
        },
    )

    assert response.status_code == 422

    body = response.json()

    assert body["success"] is False


def test_create_product_invalid_price(
    client,
    admin_headers,
    category,
):
    """
    Base price must be greater than zero.
    """

    response = client.post(
        "/api/v1/products/",
        headers=admin_headers,
        json={
            "category_id": category.id,
            "name": "Rice",
            "description": "Food",
            "sku_or_barcode": "SKU-RICE",
            "unit_of_measure": "Units",
            "base_price": "0.00",
            "min_stock_threshold": 5,
            "is_active": True,
        },
    )

    assert response.status_code == 422

    body = response.json()

    assert body["success"] is False


def test_create_product_negative_stock_threshold(
    client,
    admin_headers,
    category,
):
    """
    Stock threshold cannot be negative.
    """

    response = client.post(
        "/api/v1/products/",
        headers=admin_headers,
        json={
            "category_id": category.id,
            "name": "Rice",
            "description": "Food",
            "sku_or_barcode": "SKU-RICE",
            "unit_of_measure": "Units",
            "base_price": "10.00",
            "min_stock_threshold": -1,
            "is_active": True,
        },
    )

    assert response.status_code == 422

    body = response.json()

    assert body["success"] is False


def test_create_product_invalid_category_id(
    client,
    admin_headers,
):
    """
    category_id must be greater than zero.
    """

    response = client.post(
        "/api/v1/products/",
        headers=admin_headers,
        json={
            "category_id": 0,
            "name": "Rice",
            "description": "Food",
            "sku_or_barcode": "SKU-RICE",
            "unit_of_measure": "Units",
            "base_price": "10.00",
            "min_stock_threshold": 5,
            "is_active": True,
        },
    )

    assert response.status_code == 422

    body = response.json()

    assert body["success"] is False


# ==================================================
# GET PRODUCTS
# ==================================================

def test_get_products_success(
    client,
    admin_headers,
    product_factory,
):
    """
    Authenticated users can retrieve the product list.
    """

    product_factory(name="Apple Juice")
    product_factory(name="Orange Juice")

    response = client.get(
        "/api/v1/products/",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True

    products = body["data"]

    assert len(products) >= 2

    first = products[0]

    assert "id" in first
    assert "category_id" in first
    assert "name" in first
    assert "description" in first
    assert "sku_or_barcode" in first
    assert "unit_of_measure" in first
    assert "base_price" in first
    assert "min_stock_threshold" in first
    assert "is_active" in first
    assert "created_at" in first

    pagination = body["pagination"]

    assert pagination["page"] == 1
    assert pagination["page_size"] == 100
    assert pagination["total_items"] >= 2
    assert pagination["total_pages"] >= 1


def test_get_products_employee_success(
    client,
    employee_headers,
    product_factory,
):
    """
    Employees can retrieve the product list.
    """

    product_factory()

    response = client.get(
        "/api/v1/products/",
        headers=employee_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert len(body["data"]) >= 1


def test_get_products_requires_authentication(
    client,
):
    """
    Authentication is required.
    """

    response = client.get(
        "/api/v1/products/",
    )

    assert response.status_code == 401

    body = response.json()

    assert body["success"] is False


def test_get_products_invalid_token(
    client,
):
    """
    Invalid JWT tokens should not be accepted.
    """

    response = client.get(
        "/api/v1/products/",
        headers={
            "Authorization": "Bearer invalid_token"
        },
    )

    assert response.status_code == 401

    body = response.json()

    assert body["success"] is False


# ==================================================
# GET PRODUCTS - PAGINATION & SORTING
# ==================================================

def test_get_products_pagination(
    client,
    admin_headers,
    product_factory,
):
    """
    Pagination should return the requested page size.
    """

    for i in range(5):
        product_factory(
            name=f"Product {i}"
        )

    response = client.get(
        "/api/v1/products/?skip=1&limit=2",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True

    products = body["data"]

    assert len(products) == 2

    pagination = body["pagination"]

    assert pagination["page_size"] == 2
    assert pagination["total_items"] >= 5
    assert pagination["has_next"] is True


def test_get_products_sort_name_desc(
    client,
    admin_headers,
    product_factory,
):
    """
    Products should be sortable by name descending.
    """

    product_factory(name="Apple")
    product_factory(name="Orange")
    product_factory(name="Banana")

    response = client.get(
        "/api/v1/products/?sort=name&order=desc",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    names = [
        product["name"]
        for product in body["data"]
    ]

    assert names == sorted(
        names,
        reverse=True,
    )


def test_get_products_sort_base_price(
    client,
    admin_headers,
    product_factory,
):
    """
    Products should be sortable by base price.
    """

    product_factory(
        name="Cheap",
        base_price="5.00",
    )

    product_factory(
        name="Medium",
        base_price="20.00",
    )

    product_factory(
        name="Expensive",
        base_price="100.00",
    )

    response = client.get(
        "/api/v1/products/?sort=base_price&order=asc",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    prices = [
        float(product["base_price"])
        for product in body["data"]
    ]

    assert prices == sorted(prices)


def test_get_products_sort_created_at(
    client,
    admin_headers,
    product_factory,
):
    """
    Sorting by created_at should work.
    """

    product_factory(name="First")
    product_factory(name="Second")

    response = client.get(
        "/api/v1/products/?sort=created_at&order=asc",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert len(body["data"]) >= 2


def test_get_products_invalid_sort_field(
    client,
    admin_headers,
    product_factory,
):
    """
    Invalid sort fields should return HTTP 400.
    """

    product_factory()

    response = client.get(
        "/api/v1/products/?sort=invalid_field",
        headers=admin_headers,
    )

    assert response.status_code == 400

    body = response.json()
    
    print(body)

    assert body["success"] is False

    assert body["message"] == (
        "Invalid sort field. Allowed values: "
        "name, base_price, created_at, min_stock_threshold"
    )

# ==================================================
# SEARCH PRODUCTS
# ==================================================

def test_search_products_success(
    client,
    admin_headers,
    product_factory,
):
    """
    Search products by name.
    """

    product_factory(name="Coca-Cola")
    product_factory(name="Pepsi")

    response = client.get(
        "/api/v1/products/search/?q=Coca",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True

    products = body["data"]

    assert len(products) == 1
    assert products[0]["name"] == "Coca-Cola"


def test_search_products_by_sku(
    client,
    admin_headers,
    product_factory,
):
    """
    Products should be searchable by SKU/barcode.
    """

    product_factory(
        name="Rice",
        sku_or_barcode="SKU-RICE-001",
    )

    response = client.get(
        "/api/v1/products/search/?q=SKU-RICE",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert len(body["data"]) == 1
    assert body["data"][0]["sku_or_barcode"] == "SKU-RICE-001"


def test_search_products_by_description(
    client,
    admin_headers,
    product_factory,
):
    """
    Products should be searchable by description.
    """

    product_factory(
        name="Orange Juice",
        description="Natural fruit beverage",
    )

    response = client.get(
        "/api/v1/products/search/?q=fruit",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert len(body["data"]) == 1
    assert body["data"][0]["name"] == "Orange Juice"


def test_search_products_returns_only_active_products(
    client,
    admin_headers,
    product_factory,
):
    """
    Search endpoint should ignore inactive products.
    """

    product_factory(
        name="Old Product",
        is_active=False,
    )

    product_factory(
        name="New Product",
        is_active=True,
    )

    response = client.get(
        "/api/v1/products/search/?q=Product",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True

    products = body["data"]

    assert len(products) == 1
    assert products[0]["name"] == "New Product"
    assert products[0]["is_active"] is True


# ==================================================
# SEARCH PRODUCTS - ERROR HANDLING
# ==================================================

def test_search_products_no_results(
    client,
    admin_headers,
):
    """
    Searching for a nonexistent product should
    return an empty list.
    """

    response = client.get(
        "/api/v1/products/search/?q=NonexistentProduct",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["data"] == []

    pagination = body["pagination"]

    assert pagination["total_items"] == 0
    assert pagination["page"] == 1


def test_search_products_requires_authentication(
    client,
):
    """
    Authentication is required.
    """

    response = client.get(
        "/api/v1/products/search/?q=Coca",
    )

    assert response.status_code == 401

    body = response.json()

    assert body["success"] is False


def test_search_products_invalid_token(
    client,
):
    """
    Invalid JWT tokens should not be accepted.
    """

    response = client.get(
        "/api/v1/products/search/?q=Coca",
        headers={
            "Authorization": "Bearer invalid_token"
        },
    )

    assert response.status_code == 401

    body = response.json()

    assert body["success"] is False


def test_search_products_query_validation(
    client,
    admin_headers,
):
    """
    Query must contain at least one character.
    """

    response = client.get(
        "/api/v1/products/search/?q=",
        headers=admin_headers,
    )

    assert response.status_code == 422

    body = response.json()

    assert body["success"] is False


def test_search_products_pagination(
    client,
    admin_headers,
    product_factory,
):
    """
    Search endpoint should support pagination.
    """

    for i in range(5):
        product_factory(
            name=f"Milk {i}",
        )

    response = client.get(
        "/api/v1/products/search/?q=Milk&skip=1&limit=2",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True

    assert len(body["data"]) == 2

    pagination = body["pagination"]

    assert pagination["page_size"] == 2
    assert pagination["total_items"] == 5
    assert pagination["has_next"] is True


# ==================================================
# GET PRODUCT BY ID
# ==================================================

def test_get_single_product_success(
    client,
    admin_headers,
    product,
):
    """
    Retrieve an existing product by ID.
    """

    response = client.get(
        f"/api/v1/products/{product.id}",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True

    returned_product = body["data"]

    assert returned_product["id"] == product.id
    assert returned_product["name"] == product.name
    assert (
        returned_product["category_id"]
        == product.category_id
    )
    assert (
        returned_product["sku_or_barcode"]
        == product.sku_or_barcode
    )
    assert (
        returned_product["unit_of_measure"]
        == product.unit_of_measure
    )

    assert float(returned_product["base_price"]) == float(
        product.base_price
    )

    assert (
        returned_product["min_stock_threshold"]
        == product.min_stock_threshold
    )

    assert (
        returned_product["is_active"]
        == product.is_active
    )


def test_get_single_product_employee_success(
    client,
    employee_headers,
    product,
):
    """
    Employees can retrieve a product by ID.
    """

    response = client.get(
        f"/api/v1/products/{product.id}",
        headers=employee_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["data"]["id"] == product.id


def test_get_single_product_not_found(
    client,
    admin_headers,
):
    """
    Nonexistent product IDs should return HTTP 404.
    """

    response = client.get(
        "/api/v1/products/999999",
        headers=admin_headers,
    )

    assert response.status_code == 404

    body = response.json()

    assert body["success"] is False
    assert body["message"] == "Product not found."


def test_get_single_product_requires_authentication(
    client,
    product,
):
    """
    Authentication is required.
    """

    response = client.get(
        f"/api/v1/products/{product.id}",
    )

    assert response.status_code == 401

    body = response.json()

    assert body["success"] is False


def test_get_single_product_invalid_token(
    client,
    product,
):
    """
    Invalid JWT tokens should not be accepted.
    """

    response = client.get(
        f"/api/v1/products/{product.id}",
        headers={
            "Authorization": "Bearer invalid_token"
        },
    )

    assert response.status_code == 401

    body = response.json()

    assert body["success"] is False


# ==================================================
# UPDATE PRODUCT
# ==================================================

def test_update_product_success(
    client,
    admin_headers,
    product,
    category_factory,
):
    """
    An administrator can update an existing product.
    """

    new_category = category_factory(
        name="Updated Category"
    )

    payload = {
        "category_id": new_category.id,
        "name": "Updated Product",
        "description": "Updated description.",
        "sku_or_barcode": "UPDATED-SKU-001",
        "unit_of_measure": "Boxes",
        "base_price": "24.99",
        "min_stock_threshold": 15,
        "is_active": False,
    }

    response = client.put(
        f"/api/v1/products/{product.id}",
        headers=admin_headers,
        json=payload,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["message"] == "Product updated successfully"

    updated = body["data"]

    assert updated["id"] == product.id
    assert updated["category_id"] == new_category.id
    assert updated["name"] == payload["name"]
    assert updated["description"] == payload["description"]
    assert updated["sku_or_barcode"] == payload["sku_or_barcode"]
    assert updated["unit_of_measure"] == payload["unit_of_measure"]
    assert float(updated["base_price"]) == 24.99
    assert updated["min_stock_threshold"] == 15
    assert updated["is_active"] is False


def test_update_product_keep_same_sku(
    client,
    admin_headers,
    product,
):
    """
    Keeping the same SKU should not trigger
    the duplicate SKU validation.
    """

    payload = {
        "category_id": product.category_id,
        "name": "Updated Name",
        "description": "Updated description",
        "sku_or_barcode": product.sku_or_barcode,
        "unit_of_measure": product.unit_of_measure,
        "base_price": "30.00",
        "min_stock_threshold": 8,
        "is_active": True,
    }

    response = client.put(
        f"/api/v1/products/{product.id}",
        headers=admin_headers,
        json=payload,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True

    updated = body["data"]

    assert updated["sku_or_barcode"] == product.sku_or_barcode
    assert updated["name"] == "Updated Name"
    assert float(updated["base_price"]) == 30.00


def test_update_product_change_category(
    client,
    admin_headers,
    product,
    category_factory,
):
    """
    A product can be moved to another valid category.
    """

    another_category = category_factory(
        name="Food"
    )

    payload = {
        "category_id": another_category.id,
        "name": product.name,
        "description": product.description,
        "sku_or_barcode": product.sku_or_barcode,
        "unit_of_measure": product.unit_of_measure,
        "base_price": str(product.base_price),
        "min_stock_threshold": product.min_stock_threshold,
        "is_active": product.is_active,
    }

    response = client.put(
        f"/api/v1/products/{product.id}",
        headers=admin_headers,
        json=payload,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["data"]["category_id"] == another_category.id


# ==================================================
# UPDATE PRODUCT - ERROR HANDLING
# ==================================================

def test_update_product_not_found(
    client,
    admin_headers,
    category,
):
    """
    Updating a nonexistent product should return HTTP 404.
    """

    payload = {
        "category_id": category.id,
        "name": "Updated Product",
        "description": "Updated description",
        "sku_or_barcode": "UPDATED-001",
        "unit_of_measure": "Units",
        "base_price": "15.00",
        "min_stock_threshold": 5,
        "is_active": True,
    }

    response = client.put(
        "/api/v1/products/999999",
        headers=admin_headers,
        json=payload,
    )

    assert response.status_code == 404

    body = response.json()

    assert body["success"] is False
    assert body["message"] == "Product not found."


def test_update_product_invalid_category(
    client,
    admin_headers,
    product,
):
    """
    Updating a product with a nonexistent category should fail.
    """

    payload = {
        "category_id": 999999,
        "name": product.name,
        "description": product.description,
        "sku_or_barcode": product.sku_or_barcode,
        "unit_of_measure": product.unit_of_measure,
        "base_price": str(product.base_price),
        "min_stock_threshold": product.min_stock_threshold,
        "is_active": product.is_active,
    }

    response = client.put(
        f"/api/v1/products/{product.id}",
        headers=admin_headers,
        json=payload,
    )

    assert response.status_code == 400

    body = response.json()

    assert body["success"] is False
    assert "Category with ID" in body["message"]


def test_update_product_duplicate_sku(
    client,
    admin_headers,
    product_factory,
):
    """
    A duplicated SKU/barcode should not be accepted.
    """

    product1 = product_factory(
        sku_or_barcode="SKU-001"
    )

    product2 = product_factory(
        sku_or_barcode="SKU-002"
    )

    payload = {
        "category_id": product2.category_id,
        "name": product2.name,
        "description": product2.description,
        "sku_or_barcode": "SKU-001",
        "unit_of_measure": product2.unit_of_measure,
        "base_price": str(product2.base_price),
        "min_stock_threshold": product2.min_stock_threshold,
        "is_active": product2.is_active,
    }

    response = client.put(
        f"/api/v1/products/{product2.id}",
        headers=admin_headers,
        json=payload,
    )

    assert response.status_code == 400

    body = response.json()

    assert body["success"] is False
    assert "SKU or barcode already exists" in body["message"]


def test_update_product_requires_authentication(
    client,
    product,
):
    """
    Authentication is required.
    """

    payload = {
        "category_id": product.category_id,
        "name": product.name,
        "description": product.description,
        "sku_or_barcode": product.sku_or_barcode,
        "unit_of_measure": product.unit_of_measure,
        "base_price": str(product.base_price),
        "min_stock_threshold": product.min_stock_threshold,
        "is_active": product.is_active,
    }

    response = client.put(
        f"/api/v1/products/{product.id}",
        json=payload,
    )

    assert response.status_code == 401

    body = response.json()

    assert body["success"] is False


def test_update_product_invalid_token(
    client,
    product,
):
    """
    Invalid JWT tokens should not be accepted.
    """

    payload = {
        "category_id": product.category_id,
        "name": product.name,
        "description": product.description,
        "sku_or_barcode": product.sku_or_barcode,
        "unit_of_measure": product.unit_of_measure,
        "base_price": str(product.base_price),
        "min_stock_threshold": product.min_stock_threshold,
        "is_active": product.is_active,
    }

    response = client.put(
        f"/api/v1/products/{product.id}",
        headers={
            "Authorization": "Bearer invalid_token"
        },
        json=payload,
    )

    assert response.status_code == 401

    body = response.json()

    assert body["success"] is False


def test_update_product_employee_forbidden(
    client,
    employee_headers,
    product,
):
    """
    Employees cannot update products.
    """

    payload = {
        "category_id": product.category_id,
        "name": product.name,
        "description": product.description,
        "sku_or_barcode": product.sku_or_barcode,
        "unit_of_measure": product.unit_of_measure,
        "base_price": str(product.base_price),
        "min_stock_threshold": product.min_stock_threshold,
        "is_active": product.is_active,
    }

    response = client.put(
        f"/api/v1/products/{product.id}",
        headers=employee_headers,
        json=payload,
    )

    assert response.status_code == 403

    body = response.json()

    assert body["success"] is False


# ==================================================
# DELETE PRODUCT
# ==================================================

def test_delete_product_success(
    client,
    admin_token,
    product,
):
    response = client.delete(
        f"/api/v1/products/{product.id}",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["message"] == "Product deleted succesfully"


def test_delete_product_not_found(
    client,
    admin_token,
):
    response = client.delete(
        "/api/v1/products/999999",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == 404

    body = response.json()

    # print(body)
    
    assert body["success"] is False
    assert body["message"] == "Product not found."


def test_delete_product_requires_authentication(
    client,
    product,
):
    response = client.delete(
        f"/api/v1/products/{product.id}",
    )

    assert response.status_code == 401


def test_delete_product_invalid_token(
    client,
    product,
):
    response = client.delete(
        f"/api/v1/products/{product.id}",
        headers={
            "Authorization": "Bearer invalid_token"
        },
    )

    assert response.status_code == 401


def test_delete_product_employee_forbidden(
    client,
    employee_token,
    product,
):
    response = client.delete(
        f"/api/v1/products/{product.id}",
        headers={
            "Authorization": f"Bearer {employee_token}"
        },
    )

    assert response.status_code == 403


def test_delete_product_invalid_id_zero(
    client,
    admin_token,
):
    response = client.delete(
        "/api/v1/products/0",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == 422