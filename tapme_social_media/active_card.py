from fastapi import APIRouter,Depends,HTTPException,status
from fastapi.responses import RedirectResponse,JSONResponse
from config.database import get_db
from sqlalchemy.orm import Session
from models.productmodels import TapCard,AddCard,Customer
from product.product_service import update_add_card_active,update_add_card_data
from config.config import settings
from config.token import verify_token
from dto import productschemas
from typing import Optional
import requests
router=APIRouter(tags=["tap events"])


@router.post("/active_status/{id}")
async def active(token:str,id:str, card_pin: productschemas.ActiveStatusBase, db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
       
        email = verify_token(token, credentials_exception, db)

        # Get customer data by email
        customer_data = db.query(Customer).filter(Customer.email_address == email).first()
        if not customer_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")  
            
        # Get the card serial for the provided pin
        card_serial = db.query(TapCard).filter(TapCard.pin == card_pin.pin).first()
        if not card_serial:
            return {"error": "Invalid pin or card not found"}

        print(f"Card Serial: {card_serial.serial}")

        # Check if the card serial is found and retrieve its active status
        active_status = db.query(AddCard).filter(AddCard.tapcard_serial == card_serial.serial).first()

        if active_status:
            print(f"Current Active Status: {active_status.active}")

            # Update active status if inactive
            if active_status.active == "no":
                active_status.active = "yes"
                db.commit()
            # response_data = {"url": f"{settings.FRONTEND_URL}/add_items?id={id}"}
            # return JSONResponse(content=response_data)
           
            return RedirectResponse(url=f"{settings.FRONTEND_URL}/add_items?id={id}")
        # If active_status is not found, return an error
        return {"error": "Card status not found"}
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")


@router.post("/add_items")
async def add_items(
    token: str,
    AddCardData: productschemas.AddCardRequestSchema,
    db: Session = Depends(get_db),
    id: Optional[str] = None
): 
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    # Same logic as before...
    try:
        email = verify_token(token, credentials_exception, db)
        print(f"Verified email: {email}")

        id = id if id else AddCardData.id
        if not id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Card serial number must be provided either in the URL or the request body.",
            )

        print(f"Using Card Serial Number: {id}")
        print(f"Card Data: {AddCardData.card_data}, Card Item: {AddCardData.card_item}")

        customer_data = db.query(Customer).filter(Customer.email_address == email).first()
        if not customer_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

        active_status = db.query(AddCard).filter(AddCard.tapcard_serial == id).first()
        if not active_status:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")

        if active_status.active == "no":
            # response_data = {"url": f"{settings.FRONTEND_URL}/active_status?id={id}"}
            # return JSONResponse(content=response_data)
            return RedirectResponse(url=f"{settings.FRONTEND_URL}/active_status?id={id}")

        # Corrected function call
        card = update_add_card_data(
            db, id, AddCardData.card_data, AddCardData.card_item
        )
        if card:
            # response_data = {"url": f"{settings.FRONTEND_URL}/tap?id={id}"}
            # return JSONResponse(content=response_data)
            return RedirectResponse(url=f"{settings.FRONTEND_URL}/tap?id={id}")
        else:
            return {"error": "Failed to update card data"}

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")


# @router.post("/add_items/{id}")
# async def add_items(token:str,id: str, AddCardData: productschemas.AddCardData, db: Session = Depends(get_db)):
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Could not validate credentials",
#         headers={"WWW-Authenticate": "Bearer"},
#     )
#     try:
       
#         email = verify_token(token, credentials_exception, db)

#         # Get customer data by email
#         customer_data = db.query(Customer).filter(Customer.email_address == email).first()
#         if not customer_data:
#             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")  

        
#         active_status = db.query(AddCard).filter(AddCard.tapcard_serial == id).first()

#         if active_status=="no":
#             # return "active_status"
#             # return RedirectResponse(url=f"{settings.FRONTEND_URL}/active_status/{id}")
#             response_data = {"url": f"{settings.FRONTEND_URL}/active_status?id={id}"}
#             return JSONResponse(content=response_data)
#         card = update_add_card_data(db, id, AddCardData.card_data)
#         if card:
#             # return "tap"
#             response_data = {"url": f"{settings.FRONTEND_URL}/tap?id={id}"}
#             return JSONResponse(content=response_data)
#             # return RedirectResponse(url=f"{settings.FRONTEND_URL}/tap/{id}")
                
#         else:
#             return {"error": "Failed to update item data"}
#     except HTTPException as e:
#         raise e
#     except Exception as e:
#         print(f"An unexpected error occurred: {e}")
#         raise HTTPException(status_code=500, detail="Internal server error.")

