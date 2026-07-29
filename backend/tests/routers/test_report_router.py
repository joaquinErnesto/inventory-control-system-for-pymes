from datetime import datetime, timedelta

from app.models.core import InventoryBatch


# ==================================================
# LOW STOCK REPORT
# ==================================================

def test_get_low_stock_report_success(
    client,
    admin_headers,
    low_stock_product,
    normal_stock_product,
):
    """
    The report should return only products
    whose stock is at or below the threshold.
    """

    response = client.get(
        "/api/v1/reports/low-stock",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True

    assert len(body["data"]) == 1

    item = body["data"][0]

    assert item["product_id"] == low_stock_product.id
    assert item["product_name"] == low_stock_product.name


def test_low_stock_report_requires_authentication(
    client,
):
    """
    Authentication is required.
    """

    response = client.get(
        "/api/v1/reports/low-stock",
    )

    assert response.status_code == 401


def test_low_stock_report_employee_forbidden(
    client,
    employee_headers,
):
    """
    Employees cannot access reports.
    """

    response = client.get(
        "/api/v1/reports/low-stock",
        headers=employee_headers,
    )

    assert response.status_code == 403

    body = response.json()

    assert body["message"] == "Only administrators can access reports."


def test_low_stock_report_empty(
    client,
    admin_headers,
):
    """
    If no products are below threshold,
    the report should be empty.
    """

    response = client.get(
        "/api/v1/reports/low-stock",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True

    assert body["data"] == []


def test_low_stock_report_status_values(
    client,
    admin_headers,
    db,
    product_factory,
    inventory_batch_factory,
):
    """
    Verify both possible status values.

    REORDER_NOW
    AT_THRESHOLD
    """

    product_threshold = product_factory(
        name="Threshold Product",
        min_stock_threshold=10,
    )

    inventory_batch_factory(
        product=product_threshold,
        initial_quantity=10,
        current_quantity=10,
    )

    product_below = product_factory(
        name="Below Threshold Product",
        min_stock_threshold=10,
    )

    inventory_batch_factory(
        product=product_below,
        initial_quantity=5,
        current_quantity=5,
    )

    response = client.get(
        "/api/v1/reports/low-stock",
        headers=admin_headers,
    )

    assert response.status_code == 200

    print(response.json())
    items = response.json()["data"]

    statuses = {
        item["product_id"]: item["status"]
        for item in items
    }

    assert statuses[product_threshold.id] == "AT_THRESHOLD"

    assert statuses[product_below.id] == "REORDER_NOW"


# ==================================================
# GET BATCH AUDIT
# ==================================================

def test_get_batch_audit_success(
    client,
    admin_headers,
    batch_audit_dataset,
):
    """
    Administrator can retrieve the complete audit trail
    for an inventory batch.
    """

    response = client.get(
        f"/api/v1/reports/batch-audit/{batch_audit_dataset.id}",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True

    report = body["data"]

    assert report["batch_id"] == batch_audit_dataset.id
    assert report["product_name"] == batch_audit_dataset.product.name
    assert report["current_quantity"] == batch_audit_dataset.current_quantity

    assert len(report["audit_trail"]) == 3
    

def test_get_batch_audit_requires_authentication(
    client,
    batch_audit_dataset,
):
    """
    Authentication is required.
    """

    response = client.get(
        f"/api/v1/reports/batch-audit/{batch_audit_dataset.id}",
    )

    assert response.status_code == 401


def test_get_batch_audit_requires_authentication(
    client,
    batch_audit_dataset,
):
    """
    Authentication is required.
    """

    response = client.get(
        f"/api/v1/reports/batch-audit/{batch_audit_dataset.id}",
    )

    assert response.status_code == 401


def test_get_batch_audit_employee_forbidden(
    client,
    employee_headers,
    batch_audit_dataset,
):
    """
    Employees cannot access reports.
    """

    response = client.get(
        f"/api/v1/reports/batch-audit/{batch_audit_dataset.id}",
        headers=employee_headers,
    )

    assert response.status_code == 403

    body = response.json()

    assert body["message"] == "Only administrators can access reports."


def test_get_batch_audit_not_found(
    client,
    admin_headers,
):
    """
    Unknown batch IDs should return 404.
    """

    response = client.get(
        "/api/v1/reports/batch-audit/999999",
        headers=admin_headers,
    )

    assert response.status_code == 404

    body = response.json()

    assert body["message"] == "Batch not found."


def test_get_batch_audit_order(
    client,
    admin_headers,
    batch_audit_dataset,
):
    """
    Transactions must be returned in chronological order.
    """

    response = client.get(
        f"/api/v1/reports/batch-audit/{batch_audit_dataset.id}",
        headers=admin_headers,
    )

    assert response.status_code == 200

    trail = response.json()["data"]["audit_trail"]

    dates = [
        tx["performed_at"]
        for tx in trail
    ]

    assert dates == sorted(dates)


# ==================================================
# SALES PERFORMANCE REPORT
# ==================================================

def test_sales_performance_success(
    client,
    admin_headers,
    sales_report_dataset,
):
    """
    Administrator can retrieve the sales performance report.
    """

    from datetime import datetime, timedelta

    response = client.get(
        "/api/v1/reports/sales-performance",
        params={
            "start_date": (
                datetime.utcnow() - timedelta(days=1)
            ).isoformat(),
            "end_date": (
                datetime.utcnow() + timedelta(days=1)
            ).isoformat(),
        },
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True

    report = body["data"]

    assert report["total_sales_count"] == 3
    assert float(report["total_revenue"]) == 600.00
    assert float(report["average_sale"]) == 200.00

    assert len(report["sales_records"]) == 3


def test_sales_performance_requires_authentication(
    client,
):
    """
    Authentication is required.
    """

    from datetime import datetime, timedelta

    response = client.get(
        "/api/v1/reports/sales-performance",
        params={
            "start_date": (
                datetime.utcnow() - timedelta(days=1)
            ).isoformat(),
            "end_date": (
                datetime.utcnow() + timedelta(days=1)
            ).isoformat(),
        },
    )

    assert response.status_code == 401


def test_sales_performance_employee_forbidden(
    client,
    employee_headers,
):
    """
    Employees cannot access reports.
    """

    from datetime import datetime, timedelta

    response = client.get(
        "/api/v1/reports/sales-performance",
        params={
            "start_date": (
                datetime.utcnow() - timedelta(days=1)
            ).isoformat(),
            "end_date": (
                datetime.utcnow() + timedelta(days=1)
            ).isoformat(),
        },
        headers=employee_headers,
    )

    assert response.status_code == 403

    body = response.json()

    assert body["message"] == "Only administrators can access reports."


def test_sales_performance_invalid_date_range(
    client,
    admin_headers,
):
    """
    start_date cannot be after end_date.
    """

    from datetime import datetime, timedelta

    response = client.get(
        "/api/v1/reports/sales-performance",
        params={
            "start_date": (
                datetime.utcnow() + timedelta(days=5)
            ).isoformat(),
            "end_date": (
                datetime.utcnow()
            ).isoformat(),
        },
        headers=admin_headers,
    )

    assert response.status_code == 400

    body = response.json()

    assert body["message"] == "start_date must be earlier than end_date."


def test_sales_performance_empty_period(
    client,
    admin_headers,
):
    """
    No sales should produce zero metrics.
    """

    from datetime import datetime

    response = client.get(
        "/api/v1/reports/sales-performance",
        params={
            "start_date": datetime(2000, 1, 1).isoformat(),
            "end_date": datetime(2000, 1, 2).isoformat(),
        },
        headers=admin_headers,
    )

    assert response.status_code == 200

    report = response.json()["data"]

    assert report["total_sales_count"] == 0
    assert float(report["total_revenue"]) == 0.0
    assert float(report["average_sale"]) == 0.0
    assert report["sales_records"] == []


# ==================================================
# EXPIRING SOON REPORT
# ==================================================

def test_expiring_soon_success(
    client,
    admin_headers,
    expiring_batch,
):
    """
    Administrator can retrieve batches
    that expire within the default period.
    """

    response = client.get(
        "/api/v1/reports/expiring-soon",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True

    report = body["data"]

    assert len(report) == 1

    assert report[0]["batch_number"] == expiring_batch.batch_number
    assert report[0]["current_quantity"] == expiring_batch.current_quantity


def test_expiring_soon_requires_authentication(
    client,
):
    """
    Authentication is required.
    """

    response = client.get(
        "/api/v1/reports/expiring-soon",
    )

    assert response.status_code == 401


def test_expiring_soon_employee_forbidden(
    client,
    employee_headers,
):
    """
    Employees cannot access reports.
    """

    response = client.get(
        "/api/v1/reports/expiring-soon",
        headers=employee_headers,
    )

    assert response.status_code == 403

    body = response.json()

    assert body["message"] == "Only administrators can access reports."


def test_expiring_soon_excludes_non_expiring_batches(
    client,
    admin_headers,
    expiring_batch,
    non_expiring_batch,
    expired_batch,
    batch_without_expiration,
):
    """
    Only batches expiring within the selected
    period should be returned.
    """

    response = client.get(
        "/api/v1/reports/expiring-soon",
        headers=admin_headers,
    )

    assert response.status_code == 200

    report = response.json()["data"]

    returned_batches = {
        item["batch_number"]
        for item in report
    }

    assert expiring_batch.batch_number in returned_batches

    assert non_expiring_batch.batch_number not in returned_batches

    assert expired_batch.batch_number not in returned_batches

    assert (
        batch_without_expiration.batch_number
        not in returned_batches
    )


def test_expiring_soon_custom_days_filter(
    client,
    admin_headers,
    expiring_batch,
):
    """
    Custom day threshold should work.
    """

    response = client.get(
        "/api/v1/reports/expiring-soon",
        params={
            "days": 15,
        },
        headers=admin_headers,
    )

    assert response.status_code == 200

    report = response.json()["data"]

    assert len(report) == 1

    assert report[0]["batch_number"] == expiring_batch.batch_number


def test_expiring_soon_invalid_days_validation(
    client,
    admin_headers,
):
    """
    FastAPI validation should reject
    invalid values.
    """

    response = client.get(
        "/api/v1/reports/expiring-soon",
        params={
            "days": 0,
        },
        headers=admin_headers,
    )

    assert response.status_code == 422