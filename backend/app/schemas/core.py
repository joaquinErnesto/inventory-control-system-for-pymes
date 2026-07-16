from pydantic import BaseModel, ConfigDict, Field, EmailStr
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
    
class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"

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
    username: str = Field(..., min_length=3, max_length=50)
    role: UserRole

class UserCreate(UserBase):
    password: str = Field(..., min_length=8) # Plain text password to be hashed by your logic

class UserUpdate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    role: UserRole

class UserPasswordUpdate(BaseModel):
    password: str = Field(..., min_length=8)
    
class UserResponse(UserBase):
    id: int = Field(gt=0)
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 2. CATEGORIES
# ==========================================
class CategoryBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: int = Field(gt=0)

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 3. SUPPLIERS
# ==========================================
class SupplierBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=150)
    contact_person: Optional[str] = Field(None, min_length=3, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    is_active: bool = True

class SupplierCreate(SupplierBase):
    pass

class SupplierUpdate(SupplierBase):
    pass

class SupplierResponse(SupplierBase):
    id: int = Field(gt=0)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 4. CUSTOMERS
# ==========================================
class CustomerBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=150)
    identification_number: Optional[str] = Field(None, max_length=50)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    address: Optional[str] = None

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(CustomerBase):
    pass

class CustomerResponse(CustomerBase):
    id: int = Field(gt=0)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 5. PRODUCTS
# ==========================================
class ProductBase(BaseModel):
    category_id: int = Field(gt=0)
    name: str = Field(..., min_length=3, max_length=150)
    description: Optional[str] = None
    sku_or_barcode: Optional[str] = Field(None, max_length=50)
    unit_of_measure: UnitOfMeasure
    base_price: Decimal = Field(default=Decimal("0.01"), decimal_places=2, gt=0)
    min_stock_threshold: int = Field(default=5, ge=0)
    is_active: bool = True

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: int = Field(gt=0)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 6. INVENTORY BATCHES
# ==========================================
class InventoryBatchBase(BaseModel):
    product_id: int = Field(gt=0)
    supplier_id: Optional[int] = Field(default=None, gt=0)
    batch_number: Optional[str] = Field(None, max_length=50)
    initial_quantity: int = Field(gt=0)
    cost_price: Decimal = Field(..., decimal_places=2, gt=0)
    selling_price: Decimal = Field(..., decimal_places=2, gt=0)
    expiration_date: Optional[date] = None
    notes: Optional[str] = None

class InventoryBatchCreate(InventoryBatchBase):
    pass

class InventoryBatchResponse(InventoryBatchBase):
    id: int = Field(gt=0)
    current_quantity: int = Field(ge=0)
    created_by_user_id: int = Field(gt=0)
    received_date: datetime

    model_config = ConfigDict(from_attributes=True)
    
class ExpiringBatchResponse(BaseModel):
    product_name: str = Field(min_length=3, max_length=50)
    batch_number: Optional[str] = Field(default=None, max_length=50)
    current_quantity: int = Field(ge=0)
    expiration_date: date
    days_remaining: int = Field(ge=0)

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 7. SALE ITEMS
# ==========================================
class SaleItemBase(BaseModel):
    product_id: int = Field(gt=0)
    quantity_sold: int = Field(gt=0)
    unit_price: Decimal = Field(..., decimal_places=2, gt=0)

class SaleItemCreate(SaleItemBase):
    pass

class SaleItemResponse(SaleItemBase):
    id: int = Field(gt=0)
    sale_id: int = Field(gt=0)
    batch_id: int = Field(gt=0)

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 8. SALES
# ==========================================
class SaleBase(BaseModel):
    customer_id: Optional[int] = Field(default=None, gt=0)
    payment_method: PaymentMethod
    payment_status: PaymentStatus

class SaleCreate(SaleBase):
    items: List[SaleItemCreate]  # A single POST request will include the sale AND its items

class SaleResponse(SaleBase):
    id: int = Field(gt=0)
    user_id: int = Field(gt=0)
    total_amount: Decimal = Field(ge=0)
    sold_at: datetime
    items: List[SaleItemResponse] # Returns the nested items in the JSON response

    model_config = ConfigDict(from_attributes=True)

# ==========================================
# SALE DETAILS (Receipt View)
# ==========================================

class SaleItemDetailResponse(BaseModel):
    product_id: int = Field(gt=0)
    product_name: str = Field(min_length=3, max_length=50)
    batch_id: int = Field(gt=0)
    quantity_sold: int = Field(gt=0)
    unit_price: Decimal = Field(gt=0)
    subtotal: Decimal = Field(gt=0)

    model_config = ConfigDict(from_attributes=True)


class SaleDetailResponse(BaseModel):
    id: int = Field(gt=0)

    sold_at: datetime

    total_amount: Decimal

    payment_method: PaymentMethod

    payment_status: PaymentStatus

    customer_id: Optional[int] = Field(default=None, gt=0)
    customer_name: Optional[str] = Field(default=None, max_length=150)

    user_id: int = Field(gt=0)
    employee_username: str = Field(min_length=3, max_length=50)

    items: List[SaleItemDetailResponse]

# ==========================================
# 9. LOSS LOGS
# ==========================================
class LossLogBase(BaseModel):
    batch_id: int = Field(gt=0)
    quantity_lost: int = Field(gt=0)
    reason: LossReason
    notes: Optional[str] = None

class LossLogCreate(LossLogBase):
    pass

class LossLogResponse(LossLogBase):
    id: int = Field(gt=0)
    user_id: int = Field(gt=0)
    logged_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 10. INVENTORY TRANSACTIONS
# ==========================================
# Note: We do not need a "Create" schema here because the API should never 
# allow a user to manually POST a transaction. These are generated automatically
# by the backend when sales, losses, or batches occur.
class InventoryTransactionResponse(BaseModel):
    id: int = Field(gt=0)
    product_id: int = Field(gt=0)
    batch_id: int = Field(gt=0)
    user_id: int = Field(gt=0)
    quantity_changed: int
    transaction_type: str
    sale_id: Optional[int] = Field(default=None, gt=0)
    loss_id: Optional[int] = Field(default=None, gt=0)
    notes: Optional[str] = None
    performed_at: datetime

    model_config = ConfigDict(from_attributes=True)
    
class InventoryTransactionDetailedResponse(BaseModel):
    id: int = Field(gt=0)

    product_id: int = Field(gt=0)
    product_name: str

    batch_id: int = Field(gt=0)
    batch_number: Optional[str]

    user_id: int = Field(gt=0)
    username: str

    quantity_changed: int
    transaction_type: str

    sale_id: Optional[int] = Field(default=None, gt=0)
    loss_id: Optional[int] = Field(default=None, gt=0)

    notes: Optional[str] = None

    performed_at: datetime

    model_config = ConfigDict(from_attributes=True)

class InventoryTransactionSummaryResponse(BaseModel):
    total_transactions: int
    incoming_transactions: int
    outgoing_transactions: int
    loss_transactions: int
    adjustment_transactions: int
 
    
# ==========================================
# 11. AUTHENTICATION
# ==========================================

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str
    user_id: int
    role: UserRole
    

# ==========================================
# 12. AUTHENTICATION
# ==========================================

class LowStockItemResponse(BaseModel):
    product_id: int = Field(gt=0)
    product_name: str
    current_stock: int = Field(ge=0)
    min_threshold: int = Field(ge=0)
    status: str
    
class BatchAuditTransactionResponse(BaseModel):
    performed_at: datetime
    type: str
    quantity_change: int
    user_id: int = Field(gt=0)
    sale_id: Optional[int] = Field(default=None, gt=0)
    loss_id: Optional[int] = Field(default=None, gt=0)
    notes: Optional[str] = None
    
class BatchAuditResponse(BaseModel):
    batch_id: int = Field(gt=0)
    product_name: str
    batch_number: Optional[str]
    initial_quantity: int
    current_quantity: int
    audit_trail: List[BatchAuditTransactionResponse]
    
class SalesPerformanceResponse(BaseModel):
    start_date: datetime
    end_date: datetime
    customer_id: Optional[int] = Field(default=None, gt=0)
    total_sales_count: int
    total_revenue: Decimal
    average_sale: Decimal
    sales_records: List[SaleResponse]