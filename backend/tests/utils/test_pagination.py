import pytest

from app.models.core import User
from app.utils.pagination import paginate


# ==================================================
# TESTS
# ==================================================

def test_paginate_first_page(
    db,
    user_factory,
):
    for i in range(25):
        user_factory(
            username=f"user_{i}"
        )

    query = db.query(User).order_by(User.id)

    items, pagination = paginate(
        query=query,
        skip=0,
        limit=10,
    )

    assert len(items) == 10

    assert pagination.page == 1
    assert pagination.page_size == 10
    assert pagination.total_items == 25
    assert pagination.total_pages == 3
    assert pagination.has_next is True
    assert pagination.has_previous is False


def test_paginate_middle_page(
    db,
    user_factory,
):
    for i in range(25):
        user_factory(
            username=f"user_{i}"
        )

    query = db.query(User).order_by(User.id)

    items, pagination = paginate(
        query=query,
        skip=10,
        limit=10,
    )

    assert len(items) == 10

    assert pagination.page == 2
    assert pagination.total_pages == 3
    assert pagination.has_next is True
    assert pagination.has_previous is True


def test_paginate_last_page(
    db,
    user_factory,
):
    for i in range(25):
        user_factory(
            username=f"user_{i}"
        )

    query = db.query(User).order_by(User.id)

    items, pagination = paginate(
        query=query,
        skip=20,
        limit=10,
    )

    assert len(items) == 5

    assert pagination.page == 3
    assert pagination.total_pages == 3
    assert pagination.has_next is False
    assert pagination.has_previous is True


def test_paginate_empty_query(
    db,
):
    query = db.query(User)

    items, pagination = paginate(
        query=query,
        skip=0,
        limit=10,
    )

    assert items == []

    assert pagination.page == 1
    assert pagination.total_items == 0
    assert pagination.total_pages == 0
    assert pagination.has_next is False
    assert pagination.has_previous is False


def test_paginate_limit_larger_than_total(
    db,
    user_factory,
):
    for i in range(5):
        user_factory(
            username=f"user_{i}"
        )

    query = db.query(User)

    items, pagination = paginate(
        query=query,
        skip=0,
        limit=100,
    )

    assert len(items) == 5

    assert pagination.page == 1
    assert pagination.total_items == 5
    assert pagination.total_pages == 1
    assert pagination.has_next is False
    assert pagination.has_previous is False


def test_paginate_invalid_limit(
    db,
):
    query = db.query(User)

    with pytest.raises(ValueError) as exc:
        paginate(
            query=query,
            skip=0,
            limit=0,
        )

    assert str(exc.value) == (
        "limit must be greater than zero."
    )


def test_paginate_negative_skip(
    db,
):
    query = db.query(User)

    with pytest.raises(ValueError) as exc:
        paginate(
            query=query,
            skip=-1,
            limit=10,
        )

    assert str(exc.value) == (
        "skip cannot be negative."
    )