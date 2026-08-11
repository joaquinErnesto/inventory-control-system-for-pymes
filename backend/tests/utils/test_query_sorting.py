import pytest

from fastapi import HTTPException

from app.models.core import User
from app.schemas.core import SortOrder
from app.utils.query_sorting import apply_sorting


# ==================================================
# HELPERS
# ==================================================

ALLOWED_FIELDS = {
    "id": User.id,
    "username": User.username,
    "created_at": User.created_at,
}


# ==================================================
# ASCENDING SORT
# ==================================================

def test_apply_sorting_username_ascending(
    db,
    user_factory,
):
    user_factory(username="charlie")
    user_factory(username="alice")
    user_factory(username="bob")

    query = db.query(User)

    query = apply_sorting(
        query=query,
        sort="username",
        order=SortOrder.ASC,
        allowed_fields=ALLOWED_FIELDS,
    )

    usernames = [user.username for user in query.all()]

    assert usernames == sorted(usernames)


# ==================================================
# DESCENDING SORT
# ==================================================

def test_apply_sorting_username_descending(
    db,
    user_factory,
):
    user_factory(username="charlie")
    user_factory(username="alice")
    user_factory(username="bob")

    query = db.query(User)

    query = apply_sorting(
        query=query,
        sort="username",
        order=SortOrder.DESC,
        allowed_fields=ALLOWED_FIELDS,
    )

    usernames = [user.username for user in query.all()]

    assert usernames == sorted(
        usernames,
        reverse=True,
    )


# ==================================================
# INVALID FIELD
# ==================================================

def test_apply_sorting_invalid_field(
    db,
):
    query = db.query(User)

    with pytest.raises(HTTPException) as exc:

        apply_sorting(
            query=query,
            sort="invalid_field",
            order=SortOrder.ASC,
            allowed_fields=ALLOWED_FIELDS,
        )

    assert exc.value.status_code == 400

    assert "Invalid sort field" in exc.value.detail


# ==================================================
# DEFAULT ORDER (ASC)
# ==================================================

def test_apply_sorting_default_order(
    db,
    user_factory,
):
    user_factory(username="zulu")
    user_factory(username="alpha")

    query = db.query(User)

    query = apply_sorting(
        query=query,
        sort="username",
        order=SortOrder.ASC,
        allowed_fields=ALLOWED_FIELDS,
    )

    usernames = [user.username for user in query.all()]

    assert usernames[0] == "alpha"
    assert usernames[-1] == "zulu"


# ==================================================
# RETURNS SQLALCHEMY QUERY
# ==================================================

def test_apply_sorting_returns_query(
    db,
):
    query = db.query(User)

    sorted_query = apply_sorting(
        query=query,
        sort="id",
        order=SortOrder.ASC,
        allowed_fields=ALLOWED_FIELDS,
    )

    assert isinstance(sorted_query, type(query))