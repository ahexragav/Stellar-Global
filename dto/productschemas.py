from pydantic import BaseModel,validator,EmailStr
from datetime import datetime,date
from typing import Optional,List,Dict,Any
class CardType(BaseModel):
    card_type_id: int
    type_name: str
    image: str  # Use 'image' to match your database model

    class Config:
        orm_mode = True
class CardTypeBase(BaseModel):
    type_name: str
    img_url: str

class CardTypeCreate(CardTypeBase):
    pass


class TapEvent(BaseModel):
    id: int
    customer_id: Optional[str]  # Nullable as not explicitly marked as `nullable=False`
    tapcard_serial: str  # Foreign key, likely a required string
    timestamp: datetime
    ip_address: Optional[str] = None  # Optional IP address
    user_agent: Optional[str] = None  # Optional user agent
    location: Optional[str] = None  # Optional location field

    class Config:
        orm_mode = True
class CardItems(BaseModel):
    id: int
    type_name: str  # Matches the `type_name` column in your model

    class Config:
        orm_mode = True
class CardTypeResponse(BaseModel):
    card_type_id: int
    type_name: str
    img_url: str





class ActiveCardBase(BaseModel):
    customer_id: str  # Match the database model
    tapcard_serial: str
    card_type: str
    card_data: str
    card_item: str
    timestamp: datetime

    class Config:
        orm_mode = True
class ActiveCardCreate(ActiveCardBase):
    pass
# Base schema for  customer type
class CustomerTypeBase(BaseModel):
    type_name: str  # Correct usage

# Schema for creating a new CustomerType
class CustomerTypeCreate(CustomerTypeBase):
    pass

# Schema for reading the CustomerType
class CustomerType(CustomerTypeBase):
    customer_type_id: int  # Change to an int field
    type_name: str  # Ensure this is correct

    class Config:
        orm_mode = True


class CustomerBase(BaseModel):
    customer_id: str
    first_name: Optional[str]
    last_name: Optional[str]
    email_address: Optional[str]
    recovery_email: Optional[str]
    phone_number: Optional[str]
    title: Optional[str]
    address_1: Optional[str]
    address_2: Optional[str]
    city: Optional[str]
    state_abv: Optional[int]
    zip: Optional[str]
    zip_4: Optional[str]
    country: Optional[str]
    account_creation_date: Optional[date]
    last_login_date: Optional[date]
    account_status: Optional[str]
    preferred_contact_method: Optional[str]
    marketing_opt_in: Optional[str]
    created_by: Optional[str]
    creation_date: Optional[date]
    last_modified_by: Optional[str]
    last_modified_date: Optional[date]
    notes: Optional[str]

    class Config:
        orm_mode = True

class CustomerCreate(CustomerBase):
    first_name: str
    last_name: str
    email_address: str

class CustomerUpdate(CustomerBase):
    pass

class Customer(CustomerBase):
    pass
#tapcard schemas

# Base schema for TapCard (common fields for create, update, and read operations)
class TapCardBase(BaseModel):
    url: str
    serial: str
    allocated: Optional[str] = None
    assigned: Optional[str] = None

# Schema for creating a new TapCard (PIN is required for creation)
class TapCardCreate(TapCardBase):
    pin: str

# Schema for updating an existing TapCard (inherits from TapCardBase)
class TapCardUpdate(TapCardBase):
    pass  # All fields are optional for updating

# Schema for reading a TapCard, includes the primary key (pin)
class TapCard(TapCardBase):
    pin: str  # Include pin for reading operations

    class Config:
        orm_mode = True  # Enable ORM mode for compatibility with SQLAlchemy models

#StateLookup
class StateLookupBase(BaseModel):
    state_name: str
    state_abbreviation: str

class StateLookupCreate(BaseModel):
    state_name: str
    state_abbreviation: str

class StateLookupUpdate(StateLookupBase):
    pass  # You can add additional fields if needed for updating

class StateLookup(StateLookupBase):
    state_id: int

    class Config:
        orm_mode = True

class SocialMediaPlatformBase(BaseModel):
    platform_name: str
    category: str
    description: Optional[str] = None
    url: str
    platform_name_id: str

class SocialMediaPlatformCreate(SocialMediaPlatformBase):
    pass

class SocialMediaPlatformUpdate(SocialMediaPlatformBase):
    pass

class SocialMediaPlatform(SocialMediaPlatformBase):
    platform_id: int

    class Config:
        orm_mode = True




#SocialMediaPlatform
class OverViewCountBase(BaseModel):
    name: str
    overall_count: int


class OverViewCountCreate(OverViewCountBase):
    pass

class OverViewCountUpdate(OverViewCountBase):
    pass

class OverViewCount(OverViewCountBase):
    id: int

    class Config:
        orm_mode = True




class TapBase(BaseModel):
    card_id: str
    tap_count: int
    last_tap_timestamp: datetime

class TapResponse(TapBase):
    class Config:
        orm_mode = True

class TapsResponse(BaseModel):
    taps: List[TapResponse]


class Settings(BaseModel):
    authjwt_secret_key: str = "your_jwt_secret_key"


class AddCardBase(BaseModel):
    customer_id: str
    tapcard_serial: str
    card_type: str
    card_data: Optional[str]  # Allow None values
    card_item: Optional[str] 
    active: Optional[str] = "yes"  # Default to "yes"

class AddCardCreate(AddCardBase):
    pass

class AddCard(AddCardBase):
    id:int
    timestamp: datetime

    class Config:
        orm_mode = True

class ActiveStatusBase(BaseModel):
    pin:str
    class Config:
        orm_mode =True
class AddCardRequestSchema(BaseModel):
    id: Optional[str] = None  # Optional card serial number
    card_item: str
    card_data: str
# class AddCardBase(BaseModel):
#     customer_id: str
#     tapcard_serial: str
#     card_type: str
#     card_data: Optional[str] = None
#     card_item: Optional[str] = None
#     active: Optional[str] = "yes"



# class AddCardCreate(AddCardBase):
#     pass

# class AddCard(AddCardBase):
#     timestamp: datetime

#     class Config:
#         orm_mode = True


class ProductSummary(BaseModel):
    product_id: int
    product_name: str
    product_image: str

    class Config:
        orm_mode = True

class ProductDetail(BaseModel):
    product_id: int
    product_name: str
    product_image: str
    product_price: float
    attributes: Optional[dict]

    class Config:
        orm_mode = True
    

# Pydantic Models
class CategorySummary(BaseModel):
    category_id: int
    category_name: str
    product_image: str

    class Config:
        orm_mode = True


class AddProductCreate(BaseModel):
    product_id: int
    category_id :int
    product_name: str
    product_image: str
    product_price: float
    quantity: int
    attributes: Optional[Dict[str, Any]] = None

    class Config:
        orm_mode = True  # This allows SQLAlchemy models to be serialized to Pydantic models


class AddressBase(BaseModel):
    first_name: str
    last_name: str
    recovery_email: Optional[EmailStr] = None
    phone_number: str
    title: Optional[str] = None
    address_1: str
    address_2: Optional[str] = None
    city: str
    state :str
    zip: str
    zip_4: Optional[str] = None
    country: str
    preferred_contact_method: Optional[str] = None
    marketing_opt_in: Optional[str] = None

    class Config:
        orm_mode = True

    
class CheckoutRequest(BaseModel):
    token: str  # Add this to the model if it's expected as part of the payload

    
class PaymentRequest(BaseModel):
    token: str
    session_id: str
    payment_details: dict 