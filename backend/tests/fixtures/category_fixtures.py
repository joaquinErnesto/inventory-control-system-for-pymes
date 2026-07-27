import uuid

import pytest

from app.models.core import Category


# ==================================================
# CATEGORY FACTORY
# ==================================================

@pytest.fixture
def category_factory(db):
    """
    Factory fixture for creating product categories.

    Example:
        beverages = category_factory(
            name="Beverages",
            description="Soft drinks"
        )
    """

    created_categories = []

    def factory(
        name: str | None = None,
        description: str | None = "Category created for testing.",
    ) -> Category:

        if name is None :
            name = f"Test Category {uuid.uuid4().hex[:8]}"
        
        category = Category(
            name=name,
            description=description,
        )

        db.add(category)
        db.commit()
        db.refresh(category)

        created_categories.append(category)

        return category

    return factory


# ==================================================
# DEFAULT CATEGORY
# ==================================================

@pytest.fixture
def category(category_factory):
    """
    Creates a default category for tests.
    """

    return category_factory()