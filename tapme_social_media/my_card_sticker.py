from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer
from config.token import verify_token
from models.productmodels import Customer, TapEvent, TapCard, AddCard, CardType
from config.database import get_db, Session
from sqlalchemy import desc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")
router = APIRouter()

@router.get("/mycards/stickers", tags=["my cards"])
async def get_my_cards1(token: str, db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    print("mycard page is work ")
    try:
       
        email = verify_token(token, credentials_exception, db)

        # Get customer data by email
        customer_data = db.query(Customer).filter(Customer.email_address == email).first()
        if not customer_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

        customer_id = customer_data.customer_id

        # Count total cards for the customer
        total_cards = db.query(AddCard).filter(AddCard.customer_id == customer_id).count()

        if total_cards == 0:
            # No cards found for customer, return default response
            return {
                "total_card": 0,
                "card_details": []
            }

        # Query all card details for the customer, joining with CardType to get images
        customer_cards = db.query(AddCard).options(joinedload(AddCard.card_type_rel)).filter(
            AddCard.customer_id == customer_id
        ).all()

        card_details = []
        for card in customer_cards:
            card_details.append({
                "card_serial": card.tapcard_serial,
                "type": card.card_type,
                "card_items": card.card_item,
                "create_card_time": card.timestamp,
                "image_url": card.card_type_rel.image if card.card_type_rel else None,
                "card_type": card.card_type,
                "customer_id": customer_id
            })

        # Return the card details for the specific customer
        return {
            "total_card": total_cards,
            "card_details": card_details
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")
