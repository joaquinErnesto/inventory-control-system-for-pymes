from fastapi import HTTPException
from sqlalchemy.orm import Query

from app.schemas import core as schemas


def apply_sorting(
    query: Query,
    sort: str,
    order: schemas.SortOrder,
    allowed_fields: dict,
):
    """
    Apply validated sorting to a SQLAlchemy query.

    Parameters
    ----------
    query:
        SQLAlchemy query.

    sort:
        Field requested by the client.

    order:
        Sort order (ASC or DESC).

    allowed_fields:
        Dictionary mapping field names to SQLAlchemy columns.
    """

    if sort not in allowed_fields:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid sort field. "
                f"Allowed values: {', '.join(allowed_fields.keys())}"
            ),
        )

    column = allowed_fields[sort]

    if order == schemas.SortOrder.DESC:
        return query.order_by(column.desc())

    return query.order_by(column.asc())