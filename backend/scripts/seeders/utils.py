from typing import Any

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session


# ==================================================
# CONSOLE OUTPUT
# ==================================================

def print_section(title: str) -> None:
    """
    Print a formatted section title.
    """

    print()
    print("=" * 60)
    print(title)
    print("=" * 60)


def print_created(message: str) -> None:
    """
    Print a success message.
    """

    print(f"✔ {message}")


def print_exists(message: str) -> None:
    """
    Print a message indicating the record already exists.
    """

    print(f"ℹ {message}")


def print_error(message: str) -> None:
    """
    Print an error message.
    """

    print(f"✖ {message}")


# ==================================================
# DATABASE HELPERS
# ==================================================

def save(db: Session, instance: Any) -> Any:
    """
    Persist a SQLAlchemy model.

    This helper performs:
        - add()
        - commit()
        - refresh()

    If anything fails, the transaction is rolled back.
    """

    try:

        db.add(instance)
        db.commit()
        db.refresh(instance)

        return instance

    except SQLAlchemyError:

        db.rollback()
        raise


def already_exists(
    db: Session,
    model: Any,
    **filters,
) -> bool:
    """
    Check whether a record already exists.

    Example
    -------
    already_exists(
        db,
        User,
        username="admin"
    )
    """

    return (
        db.query(model)
        .filter_by(**filters)
        .first()
        is not None
    )


def get_one(
    db: Session,
    model: Any,
    **filters,
):
    """
    Return the first matching object or None.

    Example
    -------
    admin = get_one(
        db,
        User,
        username="admin"
    )
    """

    return (
        db.query(model)
        .filter_by(**filters)
        .first()
    )
    

def add_if_not_exists(
    db: Session,
    model,
    filters: dict,
    values: dict | None = None,
):
    """
    Create a record only if it doesn't already exist.

    Parameters
    ----------
    db:
        SQLAlchemy session.

    model:
        SQLAlchemy model class.

    filters:
        Fields used to determine whether the record already exists.

    values:
        Additional values used when creating the record.
    """

    instance = (
        db.query(model)
        .filter_by(**filters)
        .first()
    )

    if instance:
        return instance

    data = filters.copy()

    if values:
        data.update(values)

    instance = model(**data)

    db.add(instance)
    db.commit()
    db.refresh(instance)

    return instance