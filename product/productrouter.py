from fastapi import APIRouter, Depends,HTTPException
from sqlalchemy.orm import Session
from config.database import get_db
from models.productmodels import *
from  dto import productschemas as schemas
from product import product_service as crud
# ActiveCard endpoints
import boto3
# from PIL import Image
from io import BytesIO
from sqlalchemy.orm import Session
from config.config import settings
from config.database import get_db
from models.productmodels import CardType,ActiveCard
from fastapi import Depends, HTTPException
from fastapi.routing import APIRouter
from dto.productschemas import CardTypeResponse, CardTypeCreate
from typing import List
from config.selectors import CurrentAdmin,CurrentUser
router = APIRouter(tags=["products"])
app=router

@app.get("/card-types/{card_type_id}", response_model=schemas.CardType)
def read_card_type(card_type_id: int, db: Session = Depends(get_db)):
    db_card_type = crud.get_card_type(db=db, card_type_id=card_type_id)
    if db_card_type is None:
        raise HTTPException(status_code=404, detail="Card Type not found")
    return db_card_type
# @app.post("/card-types/", response_model=CardTypeResponse)
# async def upload_to_aws(card_type: CardTypeCreate, db: Session = Depends(get_db)):
#     # AWS S3 configuration
#     aws_access_key_id = settings.AWS_ACCESS_KEY_ID
#     aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY
#     region_name = settings.AWS_REGION
#     bucket_name = settings.AWS_S3_BUCKET_NAME

#     # Generate a unique file name for S3
#     s3_file_path = f'card_images/{card_type.type_name.lower().replace(" ", "_")}.jpg'
#     print(s3_file_path)

#     # Load and process the image
#     try:
#         with open(card_type.img_url, 'rb') as img_file:
#             image = Image.open(img_file)
#             image = image.convert('RGB')
        
#             with BytesIO() as img_byte_arr:
#                 # Save the image in JPEG format
#                 image.save(img_byte_arr, format='JPEG')  # Use 'JPEG' here
#                 img_byte_arr.seek(0)

#                 # Upload to S3
#                 s3 = boto3.client('s3', aws_access_key_id=aws_access_key_id,
#                                   aws_secret_access_key=aws_secret_access_key,
#                                   region_name=region_name)
#                 try:
#                     s3.upload_fileobj(img_byte_arr, bucket_name, s3_file_path, ExtraArgs={'ContentType': 'image/jpeg'})
#                     s3_image_url = f"https://{bucket_name}.s3.{region_name}.amazonaws.com/{s3_file_path}"
#                 except Exception as e:
#                     raise HTTPException(status_code=500, detail=f"Failed to upload image to S3: {str(e)}")
#     except FileNotFoundError:
#         raise HTTPException(status_code=404, detail="Image file not found.")
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error loading image: {str(e)}")

#     # Store the card type in the database
#     try:
#         db_card_type = CardType(type_name=card_type.type_name, image=s3_image_url)
#         db.add(db_card_type)
#         db.commit()
#         db.refresh(db_card_type)
#         return {
#             "card_type_id": db_card_type.card_type_id,
#             "type_name": db_card_type.type_name,
#             "img_url": db_card_type.image
#         }
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=f"Failed to store data in the database: {str(e)}")
#     finally:
#         db.close()


# ActiveCard endpoints
@app.post("/active-cards/", status_code=201)
def create_active_card(active_card: schemas.ActiveCardBase, db: Session = Depends(get_db)):
   
    # Check for existing tapcard_serial
    existing_card = db.query(ActiveCard).filter_by(tapcard_serial=active_card.tapcard_serial).first()
    if existing_card:
        raise HTTPException(status_code=400, detail="Tapcard serial already exists.")

    # Create a new ActiveCard object
    new_card = ActiveCard(
        customer_id=active_card.customer_id,
        tapcard_serial=active_card.tapcard_serial,
        card_type=active_card.card_type,
        card_data=active_card.card_data,
        card_item=active_card.card_item,
        timestamp=datetime.utcnow()
    )

    # Add and commit to the database
    db.add(new_card)
    db.commit()
    db.refresh(new_card)

    return {"message": "Active card created successfully", "data": active_card}

@app.get("/active-cards/{customer_id}/{tapcard_serial}", response_model=schemas.ActiveCardBase)
def read_active_card(customer_id: str, tapcard_serial: str, db: Session = Depends(get_db)):
    db_active_card = crud.get_active_card(db=db, customer_id=customer_id, tapcard_serial=tapcard_serial)
    if db_active_card is None:
        raise HTTPException(status_code=404, detail="Active Card not found")
    return db_active_card

@app.put("/active-cards/{customer_id}/{tapcard_serial}", response_model=schemas.ActiveCardBase)
def update_active_card(customer_id: str, tapcard_serial: str, active_card_data: schemas.ActiveCardBase, db: Session = Depends(get_db)):
    db_active_card = crud.update_active_card(db=db, customer_id=customer_id, tapcard_serial=tapcard_serial, active_card_data=active_card_data)
    if db_active_card is None:
        raise HTTPException(status_code=404, detail="Active Card not found")
    return db_active_card

@app.delete("/active-cards/{customer_id}/{tapcard_serial}", response_model=schemas.ActiveCardBase)
def delete_active_card(customer_id: str, tapcard_serial: str, db: Session = Depends(get_db)):
    db_active_card = crud.delete_active_card(db=db, customer_id=customer_id, tapcard_serial=tapcard_serial)
    if db_active_card is None:
        raise HTTPException(status_code=404, detail="Active Card not found")
    return db_active_card
# Create a new customer type
# Updated create_customer_type endpoint with role verification
@app.post("/customer-type/", response_model=schemas.CustomerType)
def create_customer_types(
    customer_type: schemas.CustomerTypeCreate,
    db: Session = Depends(get_db),
    current_user: dict = CurrentAdmin  # Check if the current user is an admin
):
    print("Current user data:", current_user)  # Debugging line
    
    db_customer_type = crud.get_customer_type_by_name(db=db, type_name=customer_type.type_name)
    if db_customer_type:
        raise HTTPException(status_code=400, detail="Customer type already exists")
    
    return crud.create_customer_type(db=db, customer_type=customer_type)


# Create a new customer type
# @app.post("/customer-type/", response_model=schemas.CustomerType)
# def create_customer_type(customer_type: schemas.CustomerTypeCreate, db: Session = Depends(get_db)):
#     return crud.create_customer_type(db=db, customer_type=customer_type)

@router.post("/customer-type/", response_model=schemas.CustomerType)
def create_customer_type(
    customer_type: schemas.CustomerTypeCreate,
    db: Session = Depends(get_db),
    current_user: dict = CurrentUser  # Ensures that the user is authenticated and authorized
):
    return crud.create_customer_type(db=db, customer_type=customer_type)
# Get a customer type by ID
@app.get("/customer-type/{customer_type_id}", response_model=schemas.CustomerType)
def read_customer_type(customer_type_id: int, db: Session = Depends(get_db)):
    db_customer_type = crud.get_customer_type(db=db, customer_type_id=customer_type_id)
    if db_customer_type is None:
        raise HTTPException(status_code=404, detail="Customer type not found")
    return db_customer_type
# Get a customer type by name
@app.get("/customer-type/name/{type_name}", response_model=schemas.CustomerType)
def read_customer_type_by_name(type_name: str, db: Session = Depends(get_db)):
    db_customer_type = crud.get_customer_type_by_name(db=db, type_name=type_name)
    if db_customer_type is None:
        raise HTTPException(status_code=404, detail="Customer type not found")
    return db_customer_type

# Update a customer type
@app.put("/customer-type/{customer_type_id}", response_model=schemas.CustomerType)
def update_customer_type(customer_type_id: int, customer_type: schemas.CustomerTypeCreate, db: Session = Depends(get_db)):
    updated_customer_type = crud.update_customer_type(db=db, customer_type_id=customer_type_id, customer_type=customer_type)
    if updated_customer_type is None:
        raise HTTPException(status_code=404, detail="Customer type not found")
    return updated_customer_type

# Delete a customer type
@app.delete("/customer-type/{customer_type_id}", response_model=schemas.CustomerType)
def delete_customer_type(customer_type_id: int, db: Session = Depends(get_db)):
    deleted_customer_type = crud.delete_customer_type(db=db, customer_type_id=customer_type_id)
    if deleted_customer_type is None:
        raise HTTPException(status_code=404, detail="Customer type not found")
    return deleted_customer_type
# Create a new customer


# Get all customers with pagination
@app.get("/customers/", response_model=List[schemas.Customer])
def read_customers(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    customers = crud.get_customers(db=db, skip=skip, limit=limit)
    return customers

# Get a single customer by ID
@app.get("/customers/{customer_id}", response_model=schemas.Customer)
def read_customer(customer_id: str, db: Session = Depends(get_db)):
    db_customer = crud.get_customer(db=db, customer_id=customer_id)
    if db_customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return db_customer
@app.post("/customers/", response_model=schemas.Customer)
def create_customer(customer: schemas.CustomerCreate, db: Session = Depends(get_db)):
    return crud.create_customer(db=db, customer=customer)
@app.put("/customers/{customer_id}", response_model=schemas.Customer)
def update_customer(
    customer_id: str, 
    customer: schemas.CustomerUpdate, 
    db: Session = Depends(get_db)
):
    # Fetch the customer from the database
    db_customer = crud.update_customer(db=db, customer_id=customer_id, customer_data=customer)
    
    # Raise an error if the customer doesn't exist
    if db_customer is None:
        raise HTTPException(status_code=404, detail=f"Customer with ID {customer_id} not found")
    
    return db_customer


# Delete a customer
@app.delete("/customers/{customer_id}", response_model=schemas.Customer)
def delete_customer(customer_id: str, db: Session = Depends(get_db)):
    db_customer = crud.delete_customer(db=db, customer_id=customer_id)
    if db_customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return db_customer


# Create a new TapCard
@router.post("/tapcards/", response_model=schemas.TapCard)
def create_tapcard(tapcard: schemas.TapCardCreate, db: Session = Depends(get_db)):
    return crud.create_tapcard(db=db, tapcard=tapcard)

# Read a TapCard by PIN
@router.get("/tapcards/{pin}", response_model=schemas.TapCard)
def read_tapcard(pin: str, db: Session = Depends(get_db)):
    db_tapcard = crud.get_tapcard(db=db, pin=pin)
    if db_tapcard is None:
        raise HTTPException(status_code=404, detail="TapCard not found")
    return db_tapcard

# Update a TapCard
@router.put("/tapcards/{pin}", response_model=schemas.TapCard)
def update_tapcard(pin: str, tapcard: schemas.TapCardUpdate, db: Session = Depends(get_db)):
    db_tapcard = crud.get_tapcard(db=db, pin=pin)
    if db_tapcard is None:
        raise HTTPException(status_code=404, detail="TapCard not found")
    return crud.update_tapcard(db=db, pin=pin, tapcard_data=tapcard)

# Delete a TapCard
@router.delete("/tapcards/{pin}", response_model=schemas.TapCard)
def delete_tapcard(pin: str, db: Session = Depends(get_db)):
    db_tapcard = crud.get_tapcard(db=db, pin=pin)
    if db_tapcard is None:
        raise HTTPException(status_code=404, detail="TapCard not found")
    return crud.delete_tapcard(db=db, pin=pin)
# States endpoints
@app.post("/states/", response_model=schemas.StateLookup)
def create_state(state: schemas.StateLookupCreate, db: Session = Depends(get_db)):
    return crud.create_state(db=db, state=state)


@app.get("/states/{state_id}", response_model=schemas.StateLookup)
def read_state(state_id: int, db: Session = Depends(get_db)):
    db_state = crud.get_state(db=db, state_id=state_id)
    if db_state is None:
        raise HTTPException(status_code=404, detail="State not found")
    return db_state

@app.put("/states/{state_id}", response_model=schemas.StateLookup)
def update_state(state_id: int, state_data: schemas.StateLookupUpdate, db: Session = Depends(get_db)):
    updated_state = crud.update_state(db=db, state_id=state_id, state_data=state_data)
    if updated_state is None:
        raise HTTPException(status_code=404, detail="State not found")
    return updated_state

@app.delete("/states/{state_id}", response_model=schemas.StateLookup)
def delete_state(state_id: int, db: Session = Depends(get_db)):
    deleted_state = crud.delete_state(db=db, state_id=state_id)
    if deleted_state is None:
        raise HTTPException(status_code=404, detail="State not found")
    return deleted_state


@app.post("/social-media-platforms/", response_model=schemas.SocialMediaPlatform)
def create_platform(platform: schemas.SocialMediaPlatformCreate, db: Session = Depends(get_db)):
    return crud.create_social_media_platform(db=db, platform=platform)




@app.get("/social-media-platforms/{platform_id}", response_model=schemas.SocialMediaPlatform)
def read_platform(platform_id: int, db: Session = Depends(get_db)):
    db_platform = crud.get_social_media_platform(db=db, platform_id=platform_id)
    if db_platform is None:
        raise HTTPException(status_code=404, detail="Platform not found")
    return db_platform

@app.put("/social-media-platforms/{platform_id}", response_model=schemas.SocialMediaPlatform)
def update_platform(platform_id: int, platform: schemas.SocialMediaPlatformUpdate, db: Session = Depends(get_db)):
    db_platform = crud.update_social_media_platform(db=db, platform_id=platform_id, platform_data=platform)
    if db_platform is None:
        raise HTTPException(status_code=404, detail="Platform not found")
    return db_platform

@app.delete("/social-media-platforms/{platform_id}", response_model=schemas.SocialMediaPlatform)
def delete_platform(platform_id: int, db: Session = Depends(get_db)):
    db_platform = crud.delete_social_media_platform(db=db, platform_id=platform_id)
    if db_platform is None:
        raise HTTPException(status_code=404, detail="Platform not found")
    return db_platform


@app.post("/overview_counts/")
def add_overview_count(name: str, db: Session = Depends(get_db)):
    # Assuming you have a function to get the count based on your requirement
    count = db.execute("SELECT COUNT(type_name) FROM tbl_card_types").scalar()
    return crud.create_overview_count(db=db, name=name, count=count)

@app.put("/overview_counts/")
def edit_overview_count(name: str, db: Session = Depends(get_db)):
    # Assuming you have a way to get the new count
    count = db.execute("SELECT COUNT(type_name) FROM tbl_card_types").scalar()
    updated_count = crud.update_overview_count(db=db, name=name, count=count)
    if updated_count is None:
        raise HTTPException(status_code=404, detail="Overview count not found")
    return updated_count

# "active"

# # AddCard endpoints
# @app.post("/add-cards/", response_model=schemas.AddCard)
# def create_add_card(add_card: schemas.AddCardCreate, db: Session = Depends(get_db)):
#     return crud.create_add_card(db=db, add_card=add_card)

# @app.put("/add-cards/{tapcard_serial}", response_model=schemas.AddCard)
# def update_add_card(tapcard_serial: str, active_status: str, db: Session = Depends(get_db)):
#     db_add_card = crud.update_add_card_active(db=db, tapcard_serial=tapcard_serial, active_status=active_status)
#     if db_add_card is None:
#         raise HTTPException(status_code=404, detail="AddCard not found")
#     return db_add_card

# @app.delete("/add-cards/{tapcard_serial}", response_model=schemas.AddCard)
# def delete_add_card(tapcard_serial: str, db: Session = Depends(get_db)):
#     db_add_card = crud.delete_add_card(db=db, tapcard_serial=tapcard_serial)
#     if db_add_card is None:
#         raise HTTPException(status_code=404, detail="AddCard not found")
#     return db_add_card


"active"

# AddCard endpoints
@app.post("/add-cards/", response_model=schemas.AddCard)
def create_add_card(add_card: schemas.AddCardCreate, db: Session = Depends(get_db)):
    return crud.create_add_card(db=db, add_card=add_card)

@app.put("/add-cards/{tapcard_serial}", response_model=schemas.AddCard)
def update_add_card(tapcard_serial: str, active_status: str, db: Session = Depends(get_db)):
    db_add_card = crud.update_add_card_active(db=db, tapcard_serial=tapcard_serial, active_status=active_status)
    if db_add_card is None:
        raise HTTPException(status_code=404, detail="AddCard not found")
    return db_add_card

@app.delete("/add-cards/{tapcard_serial}", response_model=schemas.AddCard)
def delete_add_card(tapcard_serial: str, db: Session = Depends(get_db)):
    db_add_card = crud.delete_add_card(db=db, tapcard_serial=tapcard_serial)
    if db_add_card is None:
        raise HTTPException(status_code=404, detail="AddCard not found")
    return db_add_card


# Example: Retrieve all Card Types
@app.get("/card_types/", response_model=List[schemas.CardType])
def read_card_types(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return db.query(CardType).offset(skip).limit(limit).all()

# Example: Retrieve all Card Items
@app.get("/card_items/", response_model=List[schemas.CardItems])
def read_card_items(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return db.query(CardItems).offset(skip).limit(limit).all()

# Example: Retrieve all Active Cards
@app.get("/active_cards/", response_model=List[schemas.ActiveCardBase])
def read_active_cards(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return db.query(ActiveCard).offset(skip).limit(limit).all()

# Example: Retrieve all Added Cards
@app.get("/add_cards/")
def read_add_cards( db: Session = Depends(get_db)):
    return db.query(AddCard).all()



# Example: Retrieve all Customer Types
@app.get("/customer_types/", response_model=List[schemas.CustomerType])
def read_customer_types(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return db.query(CustomerType).offset(skip).limit(limit).all()

# Example: Retrieve all State Lookups
@app.get("/states/", response_model=List[schemas.StateLookup])
def read_states(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return db.query(StateLookup).offset(skip).limit(limit).all()

# Example: Retrieve all Tap Cards
@app.get("/tap_cards/", response_model=List[schemas.TapCard])
def read_tap_cards(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return db.query(TapCard).offset(skip).limit(limit).all()

# Example: Retrieve all Tap Events
@app.get("/tap_events/", response_model=List[schemas.TapEvent])
def read_tap_events(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return db.query(TapEvent).offset(skip).limit(limit).all()

# Example: Retrieve all Social Media Platforms
@app.get("/social_media_platforms/", response_model=List[schemas.SocialMediaPlatform])
def read_social_media_platforms(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return db.query(SocialMediaPlatform).offset(skip).limit(limit).all()

@app.get("/customers/", response_model=List[schemas.CustomerBase])
def read_customers(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    customers = db.query(Customer).offset(skip).limit(limit).all()
    
    if not customers:
        raise HTTPException(status_code=404, detail="No customers found")
    
    return customers
