from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from enum import Enum
from datetime import datetime, date
from decimal import Decimal

# ==========================================
# ENUMS FOR THE CONSTRAINTS
# ==========================================

class UnitOfMeasure(str, Enum):
    UNITS = "Units"
    KILOGRAMS = "Kilograms"
    LITERS = "Liters"
    BOXES = "Boxes"
    PACK = "Pack"

class UserRole(str, Enum):
    ADMIN = "admin"
    EMPLOYEE = "employee"

class TransactionType(str, Enum):
    IN = "IN"
    OUT = "OUT"
    LOSS = "LOSS"
    ADJUSTMENT = "ADJUSTMENT"

class PaymentMethod(str, Enum):
    CASH = "Cash"
    CARD = "Card"
    TRANSFER = "Transfer"
    MIXED = "Mixed"

class PaymentStatus(str, Enum):
    PAID = "Paid"
    PENDING = "Pending"
    CANCELLED = "Cancelled"

class LossReason(str, Enum):
    EXPIRED = "Expired"
    DAMAGED = "Damaged"
    THEFT = "Theft"
    OTHER = "Other"    
    
# ==========================================
# 1. USERS
# ==========================================
class UserBase(BaseModel):
    username: str = Field(..., max_length=50)
    role: UserRole

class UserCreate(UserBase):
    password: str = Field(..., min_length=8) # Plain text password to be hashed by your logic

class UserResponse(UserBase):
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 2. CATEGORIES
# ==========================================
class CategoryBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 3. SUPPLIERS
# ==========================================
class SupplierBase(BaseModel):
    name: str = Field(..., max_length=150)
    contact_person: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = None
    is_active: bool = True

class SupplierCreate(SupplierBase):
    pass

class SupplierUpdate(SupplierBase):
    pass

class SupplierResponse(SupplierBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 4. CUSTOMERS
# ==========================================
class CustomerBase(BaseModel):
    name: str = Field(..., max_length=150)
    identification_number: Optional[str] = Field(None, max_length=50)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = None

class CustomerCreate(CustomerBase):
    pass

class CustomerResponse(CustomerBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 5. PRODUCTS
# ==========================================
class ProductBase(BaseModel):
    category_id: int
    name: str = Field(..., max_length=150)
    description: Optional[str] = None
    sku_or_barcode: Optional[str] = Field(None, max_length=50)
    unit_of_measure: UnitOfMeasure
    base_price: Decimal = Field(default=0.00, decimal_places=2)
    min_stock_threshold: int = 5
    is_active: bool = True

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 6. INVENTORY BATCHES
# ==========================================
class InventoryBatchBase(BaseModel):
    product_id: int
    supplier_id: Optional[int] = None
    batch_number: Optional[str] = Field(None, max_length=50)
    initial_quantity: int
    cost_price: Decimal = Field(..., decimal_places=2)
    selling_price: Decimal = Field(..., decimal_places=2)
    expiration_date: Optional[date] = None
    notes: Optional[str] = None

class InventoryBatchCreate(InventoryBatchBase):
    pass

class InventoryBatchResponse(InventoryBatchBase):
    id: int
    current_quantity: int
    created_by_user_id: int
    received_date: datetime

    model_config = ConfigDict(from_attributes=True)
    
class ExpiringBatchResponse(BaseModel):
    product_name: str
    batch_number: Optional[str] = None
    current_quantity: int
    expiration_date: date
    days_remaining: int

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 7. SALE ITEMS
# ==========================================
class SaleItemBase(BaseModel):
    product_id: int
    quantity_sold: int
    unit_price: Decimal = Field(..., decimal_places=2)

class SaleItemCreate(SaleItemBase):
    pass

class SaleItemResponse(SaleItemBase):
    id: int
    sale_id: int
    batch_id: int  # Added back for the response so the frontend can see the deductions

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 8. SALES
# ==========================================
class SaleBase(BaseModel):
    customer_id: Optional[int] = None
    payment_method: PaymentMethod
    payment_status: PaymentStatus

class SaleCreate(SaleBase):
    items: List[SaleItemCreate]  # A single POST request will include the sale AND its items

class SaleResponse(SaleBase):
    id: int
    user_id: int
    total_amount: Decimal
    sold_at: datetime
    items: List[SaleItemResponse] # Returns the nested items in the JSON response

    model_config = ConfigDict(from_attributes=True)

# ==========================================
# SALE DETAILS (Receipt View)
# ==========================================

class SaleItemDetailResponse(BaseModel):
    product_id: int
    product_name: str
    batch_id: int
    quantity_sold: int
    unit_price: Decimal
    subtotal: Decimal

    model_config = ConfigDict(from_attributes=True)


class SaleDetailResponse(BaseModel):
    id: int

    sold_at: datetime

    total_amount: Decimal

    payment_method: PaymentMethod

    payment_status: PaymentStatus

    customer_id: Optional[int]
    customer_name: Optional[str]

    user_id: int
    employee_username: str

    items: List[SaleItemDetailResponse]

# ==========================================
# 9. LOSS LOGS
# ==========================================
class LossLogBase(BaseModel):
    batch_id: int
    quantity_lost: int
    reason: LossReason
    notes: Optional[str] = None

class LossLogCreate(LossLogBase):
    pass

class LossLogResponse(LossLogBase):
    id: int
    user_id: int
    logged_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 10. INVENTORY TRANSACTIONS
# ==========================================
# Note: We do not need a "Create" schema here because the API should never 
# allow a user to manually POST a transaction. These are generated automatically
# by the backend when sales, losses, or batches occur.
class InventoryTransactionResponse(BaseModel):
    id: int
    product_id: int
    batch_id: int
    user_id: int
    quantity_changed: int
    transaction_type: str
    sale_id: Optional[int] = None
    loss_id: Optional[int] = None
    notes: Optional[str] = None
    performed_at: datetime

    model_config = ConfigDict(from_attributes=True)
    
class InventoryTransactionDetailedResponse(BaseModel):
    id: int

    product_id: int
    product_name: str

    batch_id: int
    batch_number: Optional[str]

    user_id: int
    username: str

    quantity_changed: int
    transaction_type: str

    sale_id: Optional[int] = None
    loss_id: Optional[int] = None

    notes: Optional[str] = None

    performed_at: datetime

    model_config = ConfigDict(from_attributes=True)
    
# ==========================================
# 11. AUTHENTICATION
# ==========================================

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None