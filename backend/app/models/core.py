from sqlalchemy import Column, Integer, String, Text, Boolean, Numeric, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

# 1. Users Table
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False) # 'admin' or 'employee'
    created_at = Column(DateTime, default=func.now())

    # Relationships
    sales = relationship("Sale", back_populates="user")
    batches_created = relationship("InventoryBatch", back_populates="created_by_user")
    losses_logged = relationship("LossLog", back_populates="user")
    transactions = relationship("InventoryTransaction", back_populates="user")


# 2. Categories Table
class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)

    # Relationships
    products = relationship("Product", back_populates="category")


# 3. Suppliers Table
class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(150), unique=True, nullable=False)
    contact_person = Column(String(100), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(100), nullable=True)
    address = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    batches = relationship("InventoryBatch", back_populates="supplier")


# 4. Customers Table
class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(150), nullable=False)
    identification_number = Column(String(50), unique=True, nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(100), nullable=True)
    address = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    sales = relationship("Sale", back_populates="customer")


# 5. Products Table
class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False)
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    sku_or_barcode = Column(String(50), unique=True, index=True, nullable=True)
    unit_of_measure = Column(String(20), nullable=False, default="Units")
    base_price = Column(Numeric(10, 2), nullable=False, default=0.00)
    min_stock_threshold = Column(Integer, nullable=False, default=5)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    category = relationship("Category", back_populates="products")
    batches = relationship("InventoryBatch", back_populates="product")
    sale_items = relationship("SaleItem", back_populates="product")
    transactions = relationship("InventoryTransaction", back_populates="product")


# 6. Inventory Batches Table
class InventoryBatch(Base):
    __tablename__ = "inventory_batches"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="RESTRICT"), index=True, nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    batch_number = Column(String(50), nullable=True)
    initial_quantity = Column(Integer, nullable=False)
    current_quantity = Column(Integer, nullable=False)
    cost_price = Column(Numeric(10, 2), nullable=False)
    selling_price = Column(Numeric(10, 2), nullable=False)
    expiration_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    received_date = Column(DateTime, default=func.now())

    # Relationships
    product = relationship("Product", back_populates="batches")
    supplier = relationship("Supplier", back_populates="batches")
    created_by_user = relationship("User", back_populates="batches_created")
    sale_items = relationship("SaleItem", back_populates="batch")
    loss_logs = relationship("LossLog", back_populates="batch")
    transactions = relationship("InventoryTransaction", back_populates="batch")


# 7. Sales Table
class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)
    total_amount = Column(Numeric(10, 2), nullable=False, default=0.00)
    payment_method = Column(String(50), nullable=False, default="Cash")
    payment_status = Column(String(20), nullable=False, default="Paid")
    sold_at = Column(DateTime, default=func.now(), index=True)

    # Relationships
    user = relationship("User", back_populates="sales")
    customer = relationship("Customer", back_populates="sales")
    items = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")
    transactions = relationship("InventoryTransaction", back_populates="sale")


# 8. Sale Items Table
class SaleItem(Base):
    __tablename__ = "sale_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    sale_id = Column(Integer, ForeignKey("sales.id", ondelete="CASCADE"), nullable=False)
    batch_id = Column(Integer, ForeignKey("inventory_batches.id", ondelete="RESTRICT"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    quantity_sold = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)

    # Relationships
    sale = relationship("Sale", back_populates="items")
    batch = relationship("InventoryBatch", back_populates="sale_items")
    product = relationship("Product", back_populates="sale_items")


# 9. Loss Logs Table
class LossLog(Base):
    __tablename__ = "loss_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    batch_id = Column(Integer, ForeignKey("inventory_batches.id", ondelete="RESTRICT"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    quantity_lost = Column(Integer, nullable=False)
    reason = Column(String(50), nullable=False)
    logged_at = Column(DateTime, default=func.now())
    notes = Column(Text, nullable=True)

    # Relationships
    batch = relationship("InventoryBatch", back_populates="loss_logs")
    user = relationship("User", back_populates="losses_logged")
    transactions = relationship("InventoryTransaction", back_populates="loss")


# 10. Inventory Transactions Table
class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    batch_id = Column(Integer, ForeignKey("inventory_batches.id", ondelete="RESTRICT"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    quantity_changed = Column(Integer, nullable=False)
    transaction_type = Column(String(20), nullable=False) # 'IN', 'OUT', 'LOSS', 'ADJUSTMENT'
    sale_id = Column(Integer, ForeignKey("sales.id", ondelete="SET NULL"), nullable=True)
    loss_id = Column(Integer, ForeignKey("loss_logs.id", ondelete="SET NULL"), nullable=True)
    notes = Column(Text, nullable=True)
    performed_at = Column(DateTime, default=func.now(), index=True)

    # Relationships
    product = relationship("Product", back_populates="transactions")
    batch = relationship("InventoryBatch", back_populates="transactions")
    user = relationship("User", back_populates="transactions")
    sale = relationship("Sale", back_populates="transactions")
    loss = relationship("LossLog", back_populates="transactions")