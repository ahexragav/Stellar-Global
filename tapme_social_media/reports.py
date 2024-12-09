
from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer
from config.token import verify_token
from models.productmodels import ActiveCard, Customer, TapEvent, AddCard
from config.database import get_db, Session
from sqlalchemy import desc
from sqlalchemy.exc import SQLAlchemyError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")
router = APIRouter()

@router.get("/reports", tags=["my cards"])
async def get_my_cards1(token: str, db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:

        email = verify_token(token, credentials_exception, db)

        print(email, "this is a user email (verified via OAuth)")

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")

    try:
        if not email:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid authentication credentials")

        customer_data = db.query(Customer).filter(Customer.email_address == email).first()
        if not customer_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

        cus_id = customer_data.customer_id

        # Fetch all cards associated with this customer
        cards = db.query(AddCard).filter(AddCard.customer_id == cus_id).all()
        if not cards:
            return {"message": "No cards found for this customer."}

        card_details = []

        for card in cards:
            tapcard_serial = card.tapcard_serial
            card_type = card.card_type

            # Get total tap count for the current card serial
            tap_count = db.query(TapEvent).filter(TapEvent.tapcard_serial == tapcard_serial).count()

            if tap_count > 0:
                # Get the last tap event details if taps are available
                last_event = (
                    db.query(TapEvent)
                    .filter(TapEvent.tapcard_serial == tapcard_serial)
                    .order_by(desc(TapEvent.timestamp))
                    .first()
                )
                last_tap_time = last_event.timestamp if last_event else None
                last_ip = last_event.ip_address if last_event else None
                last_user_agent = last_event.user_agent if last_event else None
            else:
                # No tap events for this card
                last_tap_time = None
                last_ip = None
                last_user_agent = None

            card_details.append({
                "card_serial_id": tapcard_serial,
                "card_type": card_type,
                "tap_total_count": tap_count,
                "last_tap_time": last_tap_time,
                "last_ip": last_ip,
                "last_user_agent": last_user_agent,
            })

        return {"card_details": card_details}

    except SQLAlchemyError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error") from e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred") from e
