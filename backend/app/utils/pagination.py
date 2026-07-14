from sqlalchemy.orm import Query

from app.schemas.responses import PaginationMeta


def paginate(
    query: Query,
    skip: int,
    limit: int,
):
    """
    Apply pagination to a SQLAlchemy query and return both the paginated items and the pagination metadata.

    Args:
        query:
            SQLAlchemy query after all filters and sorting have already been applied.

        skip:
            Number of records to skip.

        limit:
            Maximum number of records to return.

    Returns:
        tuple:
            (
                items,
                PaginationMeta
            )
    """

    if limit <= 0:
        raise ValueError("limit must be greater than zero.")

    if skip < 0:
        raise ValueError("skip cannot be negative.")

    total_items = query.count()

    items = (
        query
        .offset(skip)
        .limit(limit)
        .all()
    )

    page = (skip // limit) + 1

    total_pages = (
        (total_items + limit - 1)
        // limit
    )

    pagination = PaginationMeta(
        page=page,
        page_size=limit,
        total_items=total_items,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1,
    )

    return items, pagination