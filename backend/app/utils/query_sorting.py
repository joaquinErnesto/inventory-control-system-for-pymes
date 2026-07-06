from fastapi import HTTPException
from sqlalchemy.orm import Query


def apply_sorting(
    query: Query,
    sort: str,
    order: str,
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
        asc or desc.

    allowed_fields:
        Dictionary mapping field names to SQLAlchemy columns.
    """

    if sort not in allowed_fields:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sort field. Allowed values: {', '.join(allowed_fields.keys())}"
        )

    column = allowed_fields[sort]

    if order.lower() == "desc":
        return query.order_by(column.desc())

    return query.order_by(column.asc())