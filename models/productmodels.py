from sqlalchemy import Column, Integer, String,Text,UniqueConstraint,ForeignKey, Float, JSON,LargeBinary, PrimaryKeyConstraint,DateTime,Sequence,Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
Base = declarative_base()
class CardType(Base):
    __tablename__ = "tbl_card_types"
    
    card_type_id = Column(Integer, primary_key=True, autoincrement=True)
    type_name = Column(Text, nullable=False, unique=True)
    image = Column(String, nullable=False)

    # Relationships
    add_cards = relationship("AddCard", back_populates="card_type_rel")
    active_cards = relationship("ActiveCard", back_populates="card_type_rel")  # Add this relationship

class CardItems(Base):
    __tablename__ = "tbl_card_items"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    type_name = Column(Text, nullable=False, unique=True)

    # Relationships
    add_cards = relationship("AddCard", back_populates="card_items_rel")
    active_cards = relationship("ActiveCard", back_populates="card_items_rel")  # Add this relationship

class AddCard(Base):
    __tablename__ = "tbl_add_cards"
    
    customer_id = Column(String(10), nullable=False, index=True)
    tapcard_serial = Column(Text, nullable=False, unique=True)
    card_type = Column(Text, ForeignKey('tbl_card_types.type_name'), nullable=False)
    card_data = Column(Text, nullable=True)
    card_item = Column(Text, ForeignKey('tbl_card_items.type_name'), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    active = Column(Text, default="yes")

    __table_args__ = (
        PrimaryKeyConstraint('customer_id', 'tapcard_serial'),
    )

    # Relationships
    card_type_rel = relationship("CardType", back_populates="add_cards")
    card_items_rel = relationship("CardItems", back_populates="add_cards")

class ActiveCard(Base):
    __tablename__ = "tbl_active_cards"
    
    customer_id = Column(String(10), nullable=False, index=True)
    tapcard_serial = Column(Text, nullable=False, unique=True)
    card_type = Column(Text, ForeignKey('tbl_card_types.type_name'), nullable=False)
    card_data = Column(Text, nullable=True)
    card_item = Column(Text, ForeignKey('tbl_card_items.type_name'), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        PrimaryKeyConstraint('customer_id', 'tapcard_serial'),
    )

    # Relationships
    card_type_rel = relationship("CardType", back_populates="active_cards")
    card_items_rel = relationship("CardItems", back_populates="active_cards")





class Customer(Base):
    __tablename__ = 'tbl_customer'

    customer_id = Column(String, primary_key=True)
    first_name = Column(Text)
    last_name = Column(Text)
    email_address = Column(Text, index=True)
    recovery_email = Column(Text)
    phone_number = Column(Text, index=True)
    title = Column(Text)
    address_1 = Column(Text)
    address_2 = Column(Text)
    city = Column(Text)
    state_abv = Column(Integer, ForeignKey('tbl_state_lookup.state_id'))
    zip = Column(Text)
    zip_4 = Column(Text)
    country = Column(Text)
    account_creation_date = Column(Date)
    last_login_date = Column(Date)
    account_status = Column(Text)
    preferred_contact_method = Column(Text)
    marketing_opt_in = Column(Text)
    customer_type = Column(Integer, ForeignKey('tbl_customer_types.customer_type_id'))
    loyalty_id = Column(Text)
    created_by = Column(Text)
    creation_date = Column(Date)
    last_modified_by = Column(Text)
    last_modified_date = Column(Date)
    notes = Column(Text)

    # Relationships to other tables
    state = relationship('StateLookup', back_populates='customers')
    customer_type_rel = relationship('CustomerType', back_populates='customers')
    # payments = relationship("PaymentDetails", back_populates="customer")


class CustomerType(Base):
    __tablename__ = "tbl_customer_types"

    customer_type_id = Column(Integer, primary_key=True, autoincrement=True)
    type_name = Column(String, nullable=False, unique=True)

    customers = relationship("Customer", back_populates="customer_type_rel")


class StateLookup(Base):
    __tablename__ = "tbl_state_lookup"

    state_id = Column(Integer, primary_key=True, index=True)
    state_name = Column(String, nullable=False)
    state_abbreviation = Column(String, nullable=False)

    customers = relationship("Customer", back_populates="state")

class TapCard(Base):
    __tablename__ = "tbl_tapcards"

    pin = Column(Text, primary_key=True, index=True)
    url = Column(Text, nullable=False)
    serial = Column(Text, nullable=False, unique=True)  # Add unique constraint
    allocated = Column(Text)
    assigned = Column(Text)



class TapEvent(Base):
    __tablename__ = "tap_events"

    id = Column(Integer, primary_key=True)
    customer_id= Column(String(10))
    tapcard_serial = Column(Text, ForeignKey("tbl_tapcards.serial"))  # Foreign key to tbl_tapcards.serial
    timestamp = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String(50))
    user_agent = Column(Text)
    location = Column(Text)


class SocialMediaPlatform(Base):
    __tablename__ = "tbl_social_media_platforms"

    platform_id = Column(Integer, primary_key=True, index=True)
    platform_name = Column(String, unique=True, nullable=False)  # Already unique
    category = Column(String, nullable=False)
    description = Column(String)
    url = Column(String, nullable=False)
    platform_name_id = Column(String, unique=True, nullable=False)  # Add unique constraint


class OverviewCounts(Base):
    __tablename__="tbl_overview_counts"
    id=Column(Integer,primary_key=True,autoincrement=True)
    name=Column(String,nullable=True)
    overall_count=Column(Integer,nullable=True)


class ProductCategory(Base):
    __tablename__ = "tbl_product_categories"

    category_id = Column(Integer, primary_key=True, autoincrement=True)
    category_name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=False)  # Added description field

    # Relationship with ProductType
    product_types = relationship("ProductType", back_populates="category")


class ProductType(Base):
    __tablename__ = "tbl_product_types"

    type_id = Column(Integer, primary_key=True, autoincrement=True)
    type_name = Column(String, nullable=False)
    category_id = Column(Integer, ForeignKey("tbl_product_categories.category_id"), nullable=False)

    # Relationship with ProductCategory and Product
    category = relationship("ProductCategory", back_populates="product_types")
    products = relationship("Product", back_populates="type")

    # Unique constraint to ensure a type name is unique within a category
    __table_args__ = (
        UniqueConstraint("type_name", "category_id", name="uq_type_name_category_id"),
    )


class Product(Base):
    __tablename__ = "tbl_products"

    product_id = Column(Integer, primary_key=True, autoincrement=True)
    type_id = Column(Integer, ForeignKey("tbl_product_types.type_id"), nullable=False)
    product_name = Column(String, nullable=False)
    product_price = Column(Float, nullable=False)
    product_image = Column(String, nullable=False)
    attributes = Column(JSON, nullable=True)  # Additional attributes stored as JSON

    # Relationship with ProductType
    type = relationship("ProductType", back_populates="products")

class AddProduct(Base):
    __tablename__ = "tbl_add_product"

    id = Column(Integer, primary_key=True, index=True)

    product_id = Column(Integer, nullable=False)
    category_id= Column(Integer,nullable=False)
    product_name = Column(String, nullable=False)
    product_image = Column(String, nullable=False)
    product_price = Column(Float, nullable=False)
    quantity = Column(Integer, default=1)
    user_id = Column(Integer, nullable=False)  # To associate the cart with a user
    attributes = Column(JSON, nullable=True) 


class PaymentDetails(Base):
    __tablename__ = "tbl_payment_details"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # customer_id = Column(String(10), ForeignKey("tbl_customer.customer_id"), nullable=False)
    customer_id = Column(String(10),nullable=False)
    payment_id = Column(String, unique=True, nullable=False)  # Payment gateway's unique ID
    amount = Column(Float, nullable=False)  # Payment amount
    status = Column(String, nullable=False)  # Payment status (e.g., 'success', 'failed')
    method = Column(String, nullable=True)  # Payment method (e.g., 'card', 'paypal')
    timestamp = Column(DateTime, default=datetime.utcnow)

# class ProductAttribute(Base):
#     __tablename__ = "tbl_product_attributes"

#     attribute_id = Column(Integer, primary_key=True, autoincrement=True)
#     product_id = Column(Integer, ForeignKey("tbl_products.product_id"), nullable=False)
#     attribute_name = Column(String, nullable=False)
#     attribute_value = Column(String, nullable=False)

#     product = relationship("Product", back_populates="attributes")



    # Relationship with Customer
    # customer = relationship("Customer", back_populates="payments")

# class AddCard(Base):
#     __tablename__ = "tbl_add_cards"
#     __table_args__ = {'extend_existing': True}

#     id = Column(Integer, primary_key=True, autoincrement=True)
#     customer_id = Column(String(10), nullable=False)
#     tapcard_serial = Column(Text, nullable=False, unique=True)
#     card_type = Column(Text, ForeignKey('tbl_card_types.type_name'), nullable=False)
#     card_data = Column(Text, nullable=False)
#     card_item = Column(Text, ForeignKey('tbl_card_items.type_name'), nullable=True)
#     timestamp = Column(DateTime, default=datetime.utcnow)
#     active = Column(Text, default="yes")

#     card_type_rel = relationship("CardType", back_populates="add_cards")
#     card_items_rel = relationship("CardItems", back_populates="add_cards")


# # class AddCard(Base):
# #     __tablename__ = "tbl_add_cards"  # Match the table name in your database
    
# #     customer_id = Column(String(10), nullable=False, index=True)  # Part of composite primary key
# #     tapcard_serial = Column(Text, nullable=False, unique=True)  # Unique serial for each card
# #     card_type = Column(Text, ForeignKey('tbl_card_types.type_name'), nullable=False)  # Foreign key reference to CardType
# #     card_data = Column(Text, nullable=False)
# #     card_item = Column(Text, ForeignKey('tbl_card_items.type_name'), nullable=True)  # Foreign key reference to CardItems
# #     timestamp = Column(DateTime, default=datetime.utcnow)
# #     active = Column(Text, default="yes")


# class ActiveCard(Base):
#     __tablename__ = "tbl_active_cards"  # Match the table name in your database
    
#     customer_id = Column(String(10), nullable=False, index=True)  # Part of composite primary key
#     tapcard_serial = Column(Text, nullable=False, unique=True)  # Unique serial for each card
#     card_type = Column(Text, ForeignKey('tbl_card_types.type_name'), nullable=False)  # Foreign key reference to CardType
#     card_data = Column(Text, nullable=False)
#     card_item = Column(Text, ForeignKey('tbl_card_items.type_name'), nullable=False)  # Foreign key reference to CardItems
#     timestamp = Column(DateTime, default=datetime.utcnow)
#     # Composite primary key
#     __table_args__ = (
#         PrimaryKeyConstraint('customer_id', 'tapcard_serial'),
#     )

#     # Establish relationships with CardType and CardItems
#     card_type_rel = relationship("CardType", back_populates="active_cards")
#     card_items_rel = relationship("CardItems", back_populates="active_cards")
# class AddCard(Base):
#     __tablename__ = "tbl_add_cards"  # Match the table name in your database
    
#     customer_id = Column(String(10), nullable=False, index=True)  # Part of composite primary key
#     tapcard_serial = Column(Text, nullable=False, unique=True)  # Unique serial for each card
#     card_type = Column(Text, ForeignKey('tbl_card_types.type_name'), nullable=False)  # Foreign key reference to CardType
#     card_data = Column(Text, nullable=False)
#     card_item = Column(Text, ForeignKey('tbl_card_items.type_name'), nullable=True)  # Foreign key reference to CardItems
#     timestamp = Column(DateTime, default=datetime.utcnow)
#     active = Column(Text, default="yes")
    
#     # Composite primary key
#     __table_args__ = (
#         PrimaryKeyConstraint('customer_id', 'tapcard_serial'),
#     )

#     # Establish relationships with CardType and CardItems
#     card_type_rel = relationship("CardType", back_populates="add_cards")  # Ensure the name is consistent
#     card_items_rel = relationship("CardItems", back_populates="add_cards")  # Ensure the name is consistent
