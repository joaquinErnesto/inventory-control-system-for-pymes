from typing import Generic, Optional, TypeVar

from pydantic import BaseModel
from pydantic.generics import GenericModel

# ==========================================
# GENERIC TYPE
# ==========================================

T = TypeVar("T")


# ==========================================
# SUCCESS RESPONSE (WITHOUT MESSAGE)
# ==========================================

class SuccessResponse(GenericModel, Generic[T]):
    success: bool = True
    data: T


# ==========================================
# SUCCESS RESPONSE (WITH MESSAGE)
# ==========================================

class SuccessMessageResponse(GenericModel, Generic[T]):
    success: bool = True
    message: str
    data: T


# ==========================================
# SUCCESS RESPONSE (MESSAGE ONLY)
# ==========================================

class MessageResponse(BaseModel):
    success: bool = True
    message: str


# ==========================================
# PAGINATION METADATA
# (Reserved for future implementation)
# ==========================================

class PaginationMeta(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool


# ==========================================
# PAGINATED RESPONSE
# (Reserved for future implementation)
# ==========================================

class PaginatedResponse(GenericModel, Generic[T]):
    success: bool = True
    data: T
    pagination: PaginationMeta