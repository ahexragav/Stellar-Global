from fastapi import Depends, HTTPException, status,APIRouter
from fastapi.security import OAuth2PasswordBearer
from config.token import verify_token
from models.productmodels import ActiveCard,Customer,TapEvent,TapCard,AddCard
from config.database import get_db,Session
from sqlalchemy import desc
from sqlalchemy.exc import SQLAlchemyError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")
router=APIRouter(tags=["my cards"])

@router.get("/mycards", tags=["my cards"])
async def get_my_cards1(token: str,db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Handle OAuth token verification
    try:

        email = verify_token(token, credentials_exception, db)

        print(email, "this is a user email (verified via OAuth)")
        # Add your logic to fetch user cards from the database here

    except HTTPException as e:
        # Re-raise known exceptions
        raise e
    except Exception as e:
        # Handle unexpected errors
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")


    try:
        # Verify email and fetch customer data
        if not email:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid authentication credentials")

        # Fetch customer data using the provided email
        customer_data = db.query(Customer).filter(Customer.email_address == email).first()
        if not customer_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

        cus_id = customer_data.customer_id
        print
        # Check the total number of cards for the customer
        total_card = db.query(AddCard).filter(AddCard.customer_id == cus_id).count()

        if total_card == 0:
            # If no cards, return total card as 0 and null values for card serial and other details
            return {
                "total_active_card": 0,
                "tapcard_serial": None,
                "total_taps": 0,
                "total_uniq_ip": 0,
                "history": [],
                "recent_tap_card": None
            }

        # If cards are found, get the first card serial
        tapcard_record = db.query(AddCard).filter(AddCard.customer_id == cus_id).first()
        tapcard_serial = tapcard_record.tapcard_serial if tapcard_record else None

        # Fetch all tap events for this tap card serial
        tap_events = db.query(TapEvent).filter(TapEvent.tapcard_serial == tapcard_serial).all()
        if tap_events:
            # Get recent card type if tap events exist
            recent_card = db.query(TapEvent.tapcard_serial).filter(TapEvent.customer_id == cus_id).order_by(desc(TapEvent.timestamp)).first()
            recent_card_type = None
            if recent_card:
                # Query for the card type and card item associated with the recent card
                recent_card_info = (
                    db.query(ActiveCard.card_type, ActiveCard.card_item)
                    .filter(ActiveCard.tapcard_serial == recent_card[0])
                    .first()
                )
                
                # Extract values
                recent_card_type = recent_card_info[0] if recent_card_info else None  # Get card type
                recent_card_items = recent_card_info[1] if recent_card_info else None  # Get card items
            # Count only the customer's tap events for the specific tap card serial

            # Count only the customer's tap events for the specific tap card serial
            total_tap = db.query(TapEvent).filter(
                TapEvent.customer_id == cus_id,
                
            ).count()
            total_active_cards = db.query(AddCard).filter(AddCard.active == "yes", AddCard.customer_id == cus_id).count()
            total_non_active_cards= db.query(AddCard).filter(AddCard.active == "no", AddCard.customer_id == cus_id).count()
            # Retrieve the last added card for the specified customer
            last_card = db.query(AddCard).filter(AddCard.customer_id == cus_id).order_by(desc(AddCard.timestamp)).first()

            if last_card:
                last_card_time = last_card.timestamp  # Get the last added time
                last_card_type = last_card.card_type  # Get the last added card type
                last_item_type = last_card.card_item  # Get the last added item type
            else:
                last_card_time = None
                last_card_type = None
                last_item_type = None

            # Compile detailed report and calculate unique IPs
            detailed_report = []
            unique_ips = set()

            for event in tap_events:
                unique_ips.add(event.ip_address)
                detailed_report.append({
                    "timestamp": event.timestamp,
                    "ip_address": event.ip_address,
                    "user_agent": event.user_agent,
                    "user_location": event.location
                })

            total_uniq_ip = len(unique_ips)
            # Get the last event based on timestamp
            if detailed_report:  # Check if detailed_report is not empty
                last_event_history = max(detailed_report, key=lambda x: x["timestamp"])
            else:
                last_event_history = None  # Handle case where there are no events

            return {
                "total_active_card": total_active_cards,
                "total_taps": total_tap,
                "tapcard_serial": tapcard_serial,
                "total_uniq_ip": total_uniq_ip,
                "history": last_event_history,
                "recent_tap_card": recent_card_type,
                "recent_card_items":recent_card_items,
                "total_non_active_card":total_non_active_cards,
                "total_card":total_card,
                "last_card_time":last_card_time,
                "last_item_time":last_card_time,
                "last_card_type":last_card_type,
                "last_item_type":last_item_type
                
            }
        else:
            # No taps recorded yet, return only card details
            return {
                "total_active_card": total_active_cards,
                "tapcard_serial": tapcard_serial,
                "total_taps": 0,
                "total_uniq_ip": 0,
                "history": [],
                "recent_tap_card": None,
                "total_card":total_card,
                "last_card_time":last_card_time,
                "last_item_time":last_card_time,
                "last_card_type":last_card_type,
                "last_item_type":last_item_type
            }

    except SQLAlchemyError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error") from e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred") from e

