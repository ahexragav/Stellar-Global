
from fastapi import HTTPException
from models import productmodels as models
from dto import productschemas as schemas
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
def get_card_type(db: Session, card_type_id: int):
    return db.query(models.CardType).filter(models.CardType.card_type_id == card_type_id).first()

# Get a card type by name
def get_card_type_by_name(db: Session, type_name: str):
    return db.query(models.CardType).filter(models.CardType.type_name == type_name).first()

# Get all card types with pagination
def get_card_types(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.CardType).offset(skip).limit(limit).all()

# Update a card type
def update_card_type(db: Session, card_type: models.CardType, new_data: schemas.CardTypeCreate):
    card_type.type_name = new_data.type_name
    db.commit()
    db.refresh(card_type)
    return card_type

# Delete a card type
def delete_card_type(db: Session, card_type_id: int):
    db_card_type = db.query(models.CardType).filter(models.CardType.card_type_id == card_type_id).first()
    db.delete(db_card_type)
    db.commit()

# Create a new active card
def create_active_card(db: Session, active_card: schemas.ActiveCardCreate):
    db_active_card =models. ActiveCard(**active_card.dict())
    db.add(db_active_card)
    db.commit()
    db.refresh(db_active_card)
    return db_active_card

# Read all active cards
def get_active_cards(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.ActiveCard).offset(skip).limit(limit).all()

# Read an active card by customer ID and tap card serial
def get_active_card(db: Session, customer_id: int, tapcard_serial: str):
    return db.query(models.ActiveCard).filter(
        models.ActiveCard.customer_id == customer_id,
        models.ActiveCard.tapcard_serial == tapcard_serial
    ).first()

# Update an active card
def update_active_card(db: Session, customer_id: int, tapcard_serial: str, active_card_data: schemas.ActiveCardBase):
    db_active_card = get_active_card(db, customer_id, tapcard_serial)
    if db_active_card:
        for key, value in active_card_data.dict().items():
            setattr(db_active_card, key, value)
        db.commit()
        db.refresh(db_active_card)
        return db_active_card
    return None

# Delete an active card
def delete_active_card(db: Session, customer_id: int, tapcard_serial: str):
    db_active_card = get_active_card(db, customer_id, tapcard_serial)
    if db_active_card:
        db.delete(db_active_card)
        db.commit()
        return db_active_card
    return None

# create_customer_type
def create_customer_type(db: Session, customer_type: schemas.CustomerTypeCreate):
    db_customer_type = models.CustomerType(type_name=customer_type.type_name)  # Pass the instance's value, not type
    db.add(db_customer_type)
    db.commit()
    db.refresh(db_customer_type)
    return db_customer_type

# get_customer_type by id
def get_customer_type(db:Session,customer_type_id:int):
    return db.query(models.CustomerType).filter(models.CustomerType.customer_type_id==customer_type_id).first()

# Get a customer type by name
def get_customer_type_by_name(db: Session, type_name: str):
    return db.query(models.CustomerType).filter(models.CustomerType.type_name == type_name).first()


#get customer types using pagination
def get_customer_types(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.CustomerType).offset(skip).limit(limit).all()

# Update a customer type
def update_customer_type(db: Session, customer_type_id: int, customer_type: schemas.CustomerTypeCreate):
    db_customer_type = get_customer_type(db, customer_type_id)
    if db_customer_type:
        db_customer_type.type_name = customer_type.type_name
        db.commit()
        db.refresh(db_customer_type)
        return db_customer_type
    return None

# Delete a customer type
def delete_customer_type(db: Session, customer_type_id: int):
    db_customer_type = get_customer_type(db, customer_type_id)
    if db_customer_type:
        db.delete(db_customer_type)
        db.commit()
        return db_customer_type
    return None


# CRUD Functions
def create_customer(db: Session, customer: schemas.CustomerCreate):
    db_customer = models.Customer(**customer.dict())
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer
def update_customer(db: Session, customer_id: str, customer_data: schemas.CustomerUpdate):
    db_customer = db.query(models.Customer).filter(models.Customer.customer_id == customer_id).first()
    
    if db_customer:
        # Update fields provided in the request
        update_data = customer_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_customer, key, value)
        
        # Commit and refresh the database object
        db.commit()
        db.refresh(db_customer)
        return db_customer

    return None
def get_customers(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.Customer).offset(skip).limit(limit).all()

def get_customer(db: Session, customer_id: str):
    return db.query(models.Customer).filter(models.Customer.customer_id == customer_id).first()


def delete_customer(db: Session, customer_id: str):
    db_customer = db.query(models.Customer).filter(models.Customer.customer_id == customer_id).first()
    if db_customer:
        db.delete(db_customer)
        db.commit()
        return db_customer
    return None



# Create a new TapCard
def create_tapcard(db: Session, tapcard: schemas.TapCardCreate):
    db_tapcard = models.TapCard(**tapcard.dict())
    db.add(db_tapcard)
    db.commit()
    db.refresh(db_tapcard)
    return db_tapcard

# Read all TapCards with pagination
def get_tapcards(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.TapCard).offset(skip).limit(limit).all()

# Read a TapCard by PIN
def get_tapcard(db: Session, pin: str):
    return db.query(models.TapCard).filter(models.TapCard.pin == pin).first()

# Update a TapCard
def update_tapcard(db: Session, pin: str, tapcard_data: schemas.TapCardUpdate):
    db_tapcard = db.query(models.TapCard).filter(models.TapCard.pin == pin).first()
    if db_tapcard:
        for key, value in tapcard_data.dict(exclude_unset=True).items():
            setattr(db_tapcard, key, value)
        db.commit()
        db.refresh(db_tapcard)
        return db_tapcard
    return None

# Delete a TapCard
def delete_tapcard(db: Session, pin: str):
    db_tapcard = db.query(models.TapCard).filter(models.TapCard.pin == pin).first()
    if db_tapcard:
        db.delete(db_tapcard)
        db.commit()
        return db_tapcard
    return None

# Create a new state
def create_state(db: Session, state: schemas.StateLookupCreate):
    db_state = models.StateLookup(**state.dict())
    db.add(db_state)
    db.commit()
    db.refresh(db_state)
    return db_state

# Read all states with pagination
def get_states(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.StateLookup).offset(skip).limit(limit).all()

# Read a state by ID
def get_state(db: Session, state_id: int):
    return db.query(models.StateLookup).filter(models.StateLookup.state_id == state_id).first()

# Update a state
def update_state(db: Session, state_id: int, state_data: schemas.StateLookupUpdate):
    db_state = db.query(models.StateLookup).filter(models.StateLookup.state_id == state_id).first()
    if db_state:
        for key, value in state_data.dict().items():
            setattr(db_state, key, value)
        db.commit()
        db.refresh(db_state)
        return db_state
    return None

# Delete a state
def delete_state(db: Session, state_id: int):
    db_state = db.query(models.StateLookup).filter(models.StateLookup.state_id == state_id).first()
    if db_state:
        db.delete(db_state)
        db.commit()
        return db_state
    return None



def create_social_media_platform(db: Session, platform: schemas.SocialMediaPlatformCreate):
    # Check if a record with the same platform_name_id already exists
    existing_platform = db.query(models.SocialMediaPlatform).filter_by(platform_name_id=platform.platform_name_id).first()
    if existing_platform:
        raise HTTPException(
            status_code=400,
            detail=f"Platform with platform_name_id '{platform.platform_name_id}' already exists"
        )
    try:
        db_platform = models.SocialMediaPlatform(**platform.dict())
        db.add(db_platform)
        db.commit()
        db.refresh(db_platform)
        return db_platform
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="An integrity error occurred while creating the platform. Please check your data."
        ) from e

def get_social_media_platforms(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.SocialMediaPlatform).offset(skip).limit(limit).all()

def get_social_media_platform(db: Session, platform_id: int):
    return db.query(models.SocialMediaPlatform).filter(models.SocialMediaPlatform.platform_id == platform_id).first()

def update_social_media_platform(db: Session, platform_id: int, platform_data: schemas.SocialMediaPlatformUpdate):
    db_platform = db.query(models.SocialMediaPlatform).filter(models.SocialMediaPlatform.platform_id == platform_id).first()
    if db_platform:
        for key, value in platform_data.dict(exclude_unset=True).items():
            setattr(db_platform, key, value)
        db.commit()
        db.refresh(db_platform)
        return db_platform
    return None

def delete_social_media_platform(db: Session, platform_id: int):
    db_platform = db.query(models.SocialMediaPlatform).filter(models.SocialMediaPlatform.platform_id == platform_id).first()
    if db_platform:
        db.delete(db_platform)
        db.commit()
        return db_platform
    return None

def create_overview_count(db: Session, name: str, count: int):
    overview_count = models.OverviewCounts(name=name, overall_count=count)
    db.add(overview_count)
    db.commit()
    db.refresh(overview_count)
    return overview_count

def update_overview_count(db: Session, name: str, count: int):
    overview_count = db.query(models.OverviewCounts).filter(models.OverviewCounts.name == name).first()
    if overview_count:
        overview_count.overall_count = count
        db.commit()
        db.refresh(overview_count)
    return overview_count






# # Create a new AddCard
# def create_add_card(db: Session, add_card: schemas.AddCardCreate):
#     db_add_card = models.AddCard(
#         customer_id=add_card.customer_id,
#         tapcard_serial=add_card.tapcard_serial,
#         card_type=add_card.card_type,
#         card_data=add_card.card_data,
#         card_item=add_card.card_item,
#         active=add_card.active,  # Use the active field
#     )
#     db.add(db_add_card)
#     db.commit()
#     db.refresh(db_add_card)
#     return db_add_card
# # Update the active status of an AddCard
# def update_add_card_data(db: Session, tapcard_serial: str, card_data: str, card_item: str):
#     db_add_card = db.query(models.AddCard).filter(models.AddCard.tapcard_serial == tapcard_serial).first()
#     print(db_add_card, card_data)  # For debugging purposes
#     if db_add_card:
#         db_add_card.card_data = card_data  # Assuming card_data is a string field
#         db_add_card.card_item = card_item  # Adding card_item to the update
#         print("Updated data:", db_add_card.card_data)
#         db.commit()
#         db.refresh(db_add_card)
#         return db_add_card
#     return None


# # Update the active status of an AddCard
# def update_add_card_active(db: Session, tapcard_serial: str, active_status: str):
#     db_add_card = db.query(models.AddCard).filter(models.AddCard.tapcard_serial == tapcard_serial).first()
#     if db_add_card:
#         db_add_card.active = active_status
#         db.commit()
#         db.refresh(db_add_card)
#         return db_add_card
#     return None

# # Delete an AddCard by tapcard_serial
# def delete_add_card(db: Session, tapcard_serial: str):
#     db_add_card = db.query(models.AddCard).filter(models.AddCard.tapcard_serial == tapcard_serial).first()
#     if db_add_card:
#         db.delete(db_add_card)
#         db.commit()
#         return db_add_card
#     return None




# Create a new AddCard
def create_add_card(db: Session, add_card: schemas.AddCardCreate):
    db_add_card = models.AddCard(
        customer_id=add_card.customer_id,
        tapcard_serial=add_card.tapcard_serial,
        card_type=add_card.card_type,
        card_data=add_card.card_data,
        card_item=add_card.card_item,
        active=add_card.active,  # Use the active field
    )
    db.add(db_add_card)
    db.commit()
    db.refresh(db_add_card)
    return db_add_card
# Update the active status of an AddCard
def update_add_card_data(
    db: Session, 
    id: str, 
    card_data: str, 
    card_item: str
):

    # Query the AddCard object by tapcard_serial
    db_add_card = db.query(models.AddCard).filter(
        models.AddCard.tapcard_serial == id
    ).first()

    # If card exists, update its fields
    if db_add_card:
        db_add_card.card_data = card_data
        db_add_card.card_item = card_item
        db.commit()
        db.refresh(db_add_card)
        return db_add_card

    # If card doesn't exist, return None
    return None

# Update the active status of an AddCard
def update_add_card_active(db: Session, tapcard_serial: str, active_status: str):
    db_add_card = db.query(models.AddCard).filter(models.AddCard.tapcard_serial == tapcard_serial).first()
    if db_add_card:
        db_add_card.active = active_status
        db.commit()
        db.refresh(db_add_card)
        return db_add_card
    return None

# Delete an AddCard by tapcard_serial
def delete_add_card(db: Session, tapcard_serial: str):
    db_add_card = db.query(models.AddCard).filter(models.AddCard.tapcard_serial == tapcard_serial).first()
    if db_add_card:
        db.delete(db_add_card)
        db.commit()
        return db_add_card
    return None