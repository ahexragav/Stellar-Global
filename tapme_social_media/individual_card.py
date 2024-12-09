from fastapi import Depends, APIRouter, HTTPException
from sqlalchemy.orm import Session
from models.productmodels import TapEvent, AddCard
from config.database import get_db
from sqlalchemy import desc

router = APIRouter(tags=["my cards"])

@router.get("/individual_card/{tapcard_serial}")
def individual_card(tapcard_serial: str, db: Session = Depends(get_db)):
    try:
        # Check if the card exists in AddCard table
        add_card = db.query(AddCard).filter(AddCard.tapcard_serial == tapcard_serial).first()
        if not add_card:
            # If no card found, return default values with total active cards as 0
            return {
                "total_active_card": 0,
                "tapcard_serial": None,
                "total_taps": 0,
                "total_uniq_ip": 0,
                "history": [],
                "recent_tap_card": None,
                "recent_card_items": None,
                "card_status": "no",
                "card_added_time": None
            }

        # Check if there are any tap events associated with this card
        tap_events = db.query(TapEvent).filter(TapEvent.tapcard_serial == tapcard_serial).all()
        total_tap = len(tap_events)
        
        # Get card details from AddCard table
        card_status = "yes" if add_card.active == "yes" else "no"
        card_added_time = add_card.timestamp
        recent_card_type = add_card.card_type
        recent_card_items = add_card.card_item

        # Initialize variables for tap details and unique IP count
        recent_tap_timestamp = None
        detailed_report = []
        unique_ips = set()

        if tap_events:
            # If tap events exist, get the most recent event timestamp
            recent_tap_timestamp = db.query(TapEvent.timestamp).filter(TapEvent.tapcard_serial == tapcard_serial).order_by(desc(TapEvent.timestamp)).first()[0]

            # Compile detailed report and calculate unique IPs from TapEvent
            for event in tap_events:
                unique_ips.add(event.ip_address)
                detailed_report.append({
                    "timestamp": event.timestamp,
                    "ip_address": event.ip_address,
                    "user_agent": event.user_agent,
                    "user_location": event.location
                })

            # Get the last event history
            last_event_history = max(detailed_report, key=lambda x: x["timestamp"]) if detailed_report else None
        else:
            # No tap events recorded yet
            last_event_history = None

        # Return final details
        return {
            "recent_tap_timestamp": recent_tap_timestamp,
            "total_taps": total_tap,
            "tapcard_serial": tapcard_serial,
            "total_uniq_ip": len(unique_ips),
            "history": last_event_history,
            "recent_tap_card": recent_card_type,
            "recent_card_items": recent_card_items,
            "card_status": card_status,
            "card_added_time": card_added_time
        }
    
    except Exception as e:
        # Log the exception details if needed and return an error response
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

# from fastapi import Depends, APIRouter, HTTPException
# from sqlalchemy.orm import Session
# from models.productmodels import ActiveCard, TapEvent, AddCard
# from config.database import get_db
# from sqlalchemy import desc


# router = APIRouter( tags=["my cards"])

# @router.get("/individual_card/{tapcard_serial}")
# def individual_card(tapcard_serial: str, db: Session = Depends(get_db)):
#     try:
#         # Check if the card exists in AddCard table
#         add_card = db.query(AddCard).filter(AddCard.tapcard_serial == tapcard_serial).first()
#         if not add_card:
#             # If no card found, return default values with total active cards as 0
#             return {
#                 "total_active_card": 0,
#                 "tapcard_serial": None,
#                 "total_taps": 0,
#                 "total_uniq_ip": 0,
#                 "history": [],
#                 "recent_tap_card": None,
#                 "recent_card_items": None,
#                 "card_status": "no",
#                 "card_added_time": None
#             }

#         # Check if there are any tap events associated with this card
#         tap_events = db.query(TapEvent).filter(TapEvent.tapcard_serial == tapcard_serial).all()
#         total_tap = len(tap_events)
        
#         # Get card details from AddCard table
#         card_status = "yes" if add_card.active == "yes" else "no"
#         card_added_time = add_card.timestamp

#         # Initialize variables for recent tap details and unique IP count
#         recent_tap_timestamp = None
#         recent_card_type = None
#         recent_card_items = None
#         detailed_report = []
#         unique_ips = set()

#         if tap_events:
#             # If tap events exist, get the most recent event timestamp
#             recent_tap_timestamp = db.query(TapEvent.timestamp).filter(TapEvent.tapcard_serial == tapcard_serial).order_by(desc(TapEvent.timestamp)).first()[0]

#             # Get the recent card type and items from ActiveCard
#             recent_card_info = (
#                 db.query(ActiveCard.card_type, ActiveCard.card_item)
#                 .filter(ActiveCard.tapcard_serial == tapcard_serial)
#                 .order_by(desc(ActiveCard.timestamp))
#                 .first()
#             )
#             recent_card_type = recent_card_info.card_type if recent_card_info else None
#             recent_card_items = recent_card_info.card_item if recent_card_info else None

#             # Compile detailed report and calculate unique IPs from TapEvent
#             for event in tap_events:
#                 unique_ips.add(event.ip_address)
#                 detailed_report.append({
#                     "timestamp": event.timestamp,
#                     "ip_address": event.ip_address,
#                     "user_agent": event.user_agent,
#                     "user_location": event.location
#                 })

#             # Get the last event history
#             last_event_history = max(detailed_report, key=lambda x: x["timestamp"]) if detailed_report else None
#         else:
#             # No tap events recorded yet
#             last_event_history = None

#         # Return final details
#         return {
#             "recent_tap_timestamp": recent_tap_timestamp,
#             "total_taps": total_tap,
#             "tapcard_serial": tapcard_serial,
#             "total_uniq_ip": len(unique_ips),
#             "history": last_event_history,
#             "recent_tap_card": recent_card_type,
#             "recent_card_items": recent_card_items,
#             "card_status": card_status,
#             "card_added_time": card_added_time
#         }
    
#     except Exception as e:
#         # Log the exception details if needed and return an error response
#         raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
