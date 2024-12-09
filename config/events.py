# events.py
from sqlalchemy import event
from sqlalchemy.orm import Session
from datetime import datetime
from models.productmodels import AddCard, ActiveCard  # Import the relevant models
@event.listens_for(AddCard, "after_update")
def handle_active_status_change(mapper, connection, target):
    """Add or remove card from ActiveCard based on the 'active' column in AddCard."""
    print("updates is work")
    with Session(bind=connection) as session:
        if target.active == "no":
            print("update if is work")
            # Remove the card from ActiveCard if 'active' is set to 'no'
            session.query(ActiveCard).filter(ActiveCard.tapcard_serial == target.tapcard_serial).delete()
        elif target.active == "yes":
            print("update elif is work")
            # Add the card to ActiveCard if 'active' is set to 'yes'
            existing_card = session.query(ActiveCard).filter(ActiveCard.tapcard_serial == target.tapcard_serial).first()
            if not existing_card:
                new_active_card = ActiveCard(
                    customer_id=target.customer_id,
                    tapcard_serial=target.tapcard_serial,
                    card_type=target.card_type,
                    card_data=target.card_data,
                    card_item=target.card_item,
                    timestamp=datetime.utcnow()  # Set timestamp for the new record
                )
                session.add(new_active_card)
        session.commit()



@event.listens_for(AddCard, "after_insert")
def handle_active_status_insert(mapper, connection, target):
    """Add card to ActiveCard based on the 'active' column in AddCard on insert."""
    if target.active == "yes":
        with Session(bind=connection) as session:
            # Check if card already exists in ActiveCard
            existing_card = session.query(ActiveCard).filter(ActiveCard.tapcard_serial == target.tapcard_serial).first()
            if not existing_card:
                # Add to ActiveCard
                new_active_card = ActiveCard(
                    customer_id=target.customer_id,
                    tapcard_serial=target.tapcard_serial,
                    card_type=target.card_type,
                    card_data=target.card_data,
                    card_item=target.card_item,
                    timestamp=datetime.utcnow()  # Set timestamp for the new record
                )
                session.add(new_active_card)
            session.commit()


# @event.listens_for(AddCard, "after_update")
# def handle_active_status_change(mapper, connection, target):
#     """Add or remove card from ActiveCard based on the 'active' column in AddCard."""
#     with Session(bind=connection) as session:
#         if target.active == "no":
#             # Remove the card from ActiveCard if 'active' is set to 'no'
#             session.query(ActiveCard).filter(ActiveCard.tapcard_serial == target.tapcard_serial).delete()
#         elif target.active == "yes":
#             # Add the card to ActiveCard if 'active' is set to 'yes'
#             existing_card = session.query(ActiveCard).filter(ActiveCard.tapcard_serial == target.tapcard_serial).first()
#             if not existing_card:
#                 new_active_card = ActiveCard(
#                     customer_id=target.customer_id,
#                     tapcard_serial=target.tapcard_serial,
#                     card_type=target.card_type,
#                     card_data=target.card_data,
#                     card_item=target.card_item,
#                     timestamp=datetime.utcnow()  # Set timestamp for the new record
#                 )
#                 session.add(new_active_card)
#         session.commit()



# @event.listens_for(AddCard, "after_insert")
# def handle_active_status_insert(mapper, connection, target):
#     """Add card to ActiveCard based on the 'active' column in AddCard on insert."""
#     if target.active == "yes":
#         with Session(bind=connection) as session:
#             # Check if card already exists in ActiveCard
#             existing_card = session.query(ActiveCard).filter(ActiveCard.tapcard_serial == target.tapcard_serial).first()
#             if not existing_card:
#                 # Add to ActiveCard
#                 new_active_card = ActiveCard(
#                     customer_id=target.customer_id,
#                     tapcard_serial=target.tapcard_serial,
#                     card_type=target.card_type,
#                     card_data=target.card_data,
#                     card_item=target.card_item,
#                     timestamp=datetime.utcnow()  # Set timestamp for the new record
#                 )
#                 session.add(new_active_card)
#             session.commit()
