

import stripe
from fastapi import APIRouter, HTTPException, Request,Depends,status
from pydantic import BaseModel
from config.config import settings
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from config.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import func  # Make sure this line is included
from dto.productschemas import PaymentRequest
from config.token import verify_token
from models import usermodels
from models.productmodels import AddProduct, AddCard, TapCard, Customer,PaymentDetails,ProductCategory
from config.validate import validate_payment
from starlette.responses import JSONResponse
from config.email_sent_otp import send_invoice_email
# Configure Stripe API key
stripe.api_key = settings.STRIPE_SECRET_KEY

# Webhook secret from Stripe
WEBHOOK_SECRET = settings.STRIPE_WEBHOOK_SECRET

router = APIRouter(tags=["buying products"])

templates = Jinja2Templates(directory="templates")

# Request model for checkout session
class CheckoutRequest(BaseModel):
    token: str  # Ensure this matches the frontend payload

@router.get("/login1", response_class=HTMLResponse)
async def login_page(request: Request):
    """
    Render the login.html page.
    """
    return templates.TemplateResponse("login.html", {"request": request})
# Endpoint to serve the index.html page for the payment interface
@router.get("/payment", response_class=HTMLResponse)
async def payment(request: Request):
    """
    Render the index.html page for the payment interface.
    """
    return templates.TemplateResponse("index.html", {"request": request})

@router.post("/create-checkout-session")
async def create_checkout_session(request: CheckoutRequest, db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    """
    Create a Stripe Checkout session to handle payment.
    """
    print("token:",request.token)
    try:
        # Verify the token and get user details
        email = verify_token(request.token, credentials_exception, db)

        print(email, "this is a user email (verified via OAuth)")
        print(55)
        print("this is my mail",email)
        user = db.query(usermodels.Signup).filter(usermodels.Signup.email == email).first()
      
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Fetch cart items for the user
        cart_items = db.query(AddProduct).filter(AddProduct.user_id == user.id).all()

        if not cart_items:
            raise HTTPException(status_code=404, detail="No items in cart")

        # Prepare the line items for Stripe checkout
        # Prepare the line items for Stripe checkout
        line_items = []
        for item in cart_items:
            line_items.append({
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": item.product_name,  # Name of the product
                    },
                    "unit_amount": int(item.product_price * 100),  # Convert to integer cents
                },
                "quantity": item.quantity,
            })

        # Create a Stripe checkout session
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=line_items,
            mode="payment",
            success_url=f"http://127.0.0.1:8000/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.FRONTEND_URL}/cancel",
        )

        # Return session ID to frontend
        return {"id": session.id}
    
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=f"Stripe error: {e.user_message}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
@router.get("/success",response_class=HTMLResponse)
async def success_page(request:Request):
    return templates.TemplateResponse("success.html",{"request": request})



@router.post("/pay")
def process_payment(data: PaymentRequest, db: Session = Depends(get_db)):

    # Step 1: Verify token and get the user's email
    email = verify_token(data.token, credentials_exception=None, db=db)
    print("Token Verified for Email:", email)

    # Step 2: Fetch user details and customer ID
    user = db.query(usermodels.Signup).filter(usermodels.Signup.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    customer = db.query(Customer).filter(Customer.email_address == email).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Step 3: Insert payment details into the database
    session = stripe.checkout.Session.retrieve(data.session_id)
    payment_id = session.payment_intent
    payment_amount = session.amount_total

    if payment_amount <= 0 or not validate_payment(data.payment_details):
        raise HTTPException(status_code=400, detail="Invalid payment details")

    # Check if payment already exists
    existing_payment = db.query(PaymentDetails).filter(PaymentDetails.payment_id == payment_id).first()
    if not existing_payment:
        payment_record = PaymentDetails(
            customer_id=customer.customer_id,
            payment_id=payment_id,
            amount=payment_amount,
            status="success",
            method=data.payment_details.get("method", "card"),
        )
        db.add(payment_record)
        db.commit()

    # Step 4: Get all product records for the user to get category IDs and quantities
    purchased_products = db.query(AddProduct.category_id, AddProduct.quantity).filter(AddProduct.user_id == user.id).all()

    # Step 5: Calculate total quantity for all products
    total_quantity = sum(quantity for _, quantity in purchased_products)

    # Step 6: Retrieve unallocated cards from the database
    unassigned_cards = db.query(TapCard).filter(TapCard.allocated.is_(None)).limit(total_quantity).all()
    if len(unassigned_cards) < total_quantity:
        raise HTTPException(status_code=400, detail="Not enough unallocated cards available")

    # Step 7: Iterate over purchased products and allocate cards
    card_index = 0
    for category_id, quantity in purchased_products:
        category = db.query(ProductCategory).filter(ProductCategory.category_id == category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found for product")

        # Allocate the required number of cards for this category
        for _ in range(quantity):
            if card_index >= len(unassigned_cards):
                raise HTTPException(status_code=400, detail="Mismatch in available card numbers.")

            serial_number = unassigned_cards[card_index].serial
            card_index += 1

            # Create and insert a record for each allocated card
            new_add_card = AddCard(
                customer_id=customer.customer_id,
                tapcard_serial=serial_number,
                card_type=category.category_name,
                card_data=None,  # Populate if needed
                card_item=None,  # Replace with actual card item logic if necessary
                active="yes"
            )
            db.add(new_add_card)

    # Step 8: Update the `allocated` column in the TapCard table
    for card in unassigned_cards:
        card.allocated = "yes"

    # Step 9: Delete processed products from the AddProduct table
    db.query(AddProduct).filter(AddProduct.user_id == user.id).delete()

    db.commit()

    return { 
        "message": "Payment successful",
        "payment_id": payment_id,
        "card_serial": unassigned_cards[-1].serial if unassigned_cards else None,  # Last card's serial
        "user_id": customer.customer_id,
    }

@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    print("webhook is work ")
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature")

    try:
        # Verify the webhook signature
        event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)

        # Handle the event type
        if event["type"] == "payment_intent.succeeded":
            print("payment success hook is call")
            payment_intent = event["data"]["object"]
            payment_id = payment_intent["id"]
            payment_amount = payment_intent["amount_received"]  # Amount in cents

            print(f"PaymentIntent {payment_id} was successful!")

            # Retrieve the session associated with the payment
            session = stripe.checkout.Session.retrieve(payment_intent["checkout_session"])

            # Step 1: Retrieve the user from the session
            email = session["customer_email"]
            user = db.query(usermodels.Signup).filter(usermodels.Signup.email == email).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            customer = db.query(Customer).filter(Customer.email_address == email).first()
            if not customer:
                raise HTTPException(status_code=404, detail="Customer not found")

            # Step 2: Insert payment details into the database if not already present
            existing_payment = db.query(PaymentDetails).filter(PaymentDetails.payment_id == payment_id).first()
            if not existing_payment:
                payment_record = PaymentDetails(
                    customer_id=customer.customer_id,
                    payment_id=payment_id,
                    amount=payment_amount,
                    status="success",
                    method="card",  # Assuming 'card' as the default method; adjust as needed
                )
                db.add(payment_record)
                db.commit()

            # Step 3: Get all purchased product records for the user
            purchased_products = db.query(AddProduct.category_id, AddProduct.quantity).filter(AddProduct.user_id == user.id).all()

            # Step 4: Calculate the total quantity needed and verify unallocated cards
            total_quantity = sum(quantity for _, quantity in purchased_products)
            unassigned_cards = db.query(TapCard).filter(TapCard.allocated.is_(None)).limit(total_quantity).all()
            if len(unassigned_cards) < total_quantity:
                raise HTTPException(status_code=400, detail="Not enough unallocated cards available")

            # Step 5: Allocate the cards to the user
            card_index = 0
            for category_id, quantity in purchased_products:
                category = db.query(ProductCategory).filter(ProductCategory.category_id == category_id).first()
                if not category:
                    raise HTTPException(status_code=404, detail="Category not found for product")

                for _ in range(quantity):
                    if card_index >= len(unassigned_cards):
                        raise HTTPException(status_code=400, detail="Mismatch in available card numbers.")

                    serial_number = unassigned_cards[card_index].serial
                    card_index += 1

                    # Create and insert a record for each allocated card
                    new_add_card = AddCard(
                        customer_id=customer.customer_id,
                        tapcard_serial=serial_number,
                        card_type=category.category_name,
                        card_data=None,
                        card_item=None,
                        active="yes"
                    )
                    db.add(new_add_card)

            # Step 6: Mark cards as allocated
            for card in unassigned_cards:
                card.allocated = "yes"

            # Step 7: Delete processed products from AddProduct table
            db.query(AddProduct).filter(AddProduct.user_id == user.id).delete()
            db.commit()

            print(f"Cards successfully allocated for user {user.id}")

            # Step 8: Send an email notification with the invoice details
            invoice_details = {
                'full_name': f"{user.name}",
                'invoice_number': payment_id,  # or generate a custom invoice number
                'amount_paid': payment_amount / 100,  # Convert cents to dollars
                'payment_date': payment_intent["created"],
                'payment_method': "Card"  # Adjust if other payment methods are possible
            }

            # Call the function to send the email
            await send_invoice_email(email, invoice_details)

        elif event["type"] == "payment_intent.payment_failed":
            payment_intent = event["data"]["object"]
            print(f"PaymentIntent {payment_intent['id']} failed.")
            # Add logic for handling failed payments, if needed

        return JSONResponse(status_code=200, content={"status": "success"})

    except stripe.error.SignatureVerificationError:
        print("Invalid signature.")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        print("Webhook error:", e)
        raise HTTPException(status_code=400, detail=f"Webhook error: {str(e)}")
# @router.post("/webhook")
# async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
#     payload = await request.body()
#     sig_header = request.headers.get("Stripe-Signature")

#     try:
#         # Verify the webhook signature
#         event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)

#         # Handle the event type
#         if event["type"] == "payment_intent.succeeded":
#             payment_intent = event["data"]["object"]
#             payment_id = payment_intent["id"]
#             payment_amount = payment_intent["amount_received"]  # Amount in cents

#             print(f"PaymentIntent {payment_id} was successful!")

#             # Retrieve the session associated with the payment
#             session = stripe.checkout.Session.retrieve(payment_intent["checkout_session"])

#             # Step 1: Retrieve the user from the session (you can customize this)
#             email = session["customer_email"]
#             user = db.query(usermodels.Signup).filter(usermodels.Signup.email == email).first()
#             if not user:
#                 raise HTTPException(status_code=404, detail="User not found")
#             customer = db.query(Customer).filter(Customer.email_address == email).first()
#             if not customer:
#                 raise HTTPException(status_code=404, detail="Customer not found")

#             # Step 2: Insert payment details into the database if not already present
#             existing_payment = db.query(PaymentDetails).filter(PaymentDetails.payment_id == payment_id).first()
#             if not existing_payment:
#                 payment_record = PaymentDetails(
#                     customer_id=customer.customer_id,
#                     payment_id=payment_id,
#                     amount=payment_amount,
#                     status="success",
#                     method="card",  # Assuming 'card' as the default method; adjust as needed
#                 )
#                 db.add(payment_record)
#                 db.commit()

#             # Step 3: Get all purchased product records for the user
#             purchased_products = db.query(AddProduct.category_id, AddProduct.quantity).filter(AddProduct.user_id == user.id).all()

#             # Step 4: Calculate the total quantity needed and verify unallocated cards
#             total_quantity = sum(quantity for _, quantity in purchased_products)
#             unassigned_cards = db.query(TapCard).filter(TapCard.allocated.is_(None)).limit(total_quantity).all()
#             if len(unassigned_cards) < total_quantity:
#                 raise HTTPException(status_code=400, detail="Not enough unallocated cards available")

#             # Step 5: Allocate the cards to the user
#             card_index = 0
#             for category_id, quantity in purchased_products:
#                 category = db.query(ProductCategory).filter(ProductCategory.category_id == category_id).first()
#                 if not category:
#                     raise HTTPException(status_code=404, detail="Category not found for product")

#                 for _ in range(quantity):
#                     if card_index >= len(unassigned_cards):
#                         raise HTTPException(status_code=400, detail="Mismatch in available card numbers.")

#                     serial_number = unassigned_cards[card_index].serial
#                     card_index += 1

#                     # Create and insert a record for each allocated card
#                     new_add_card = AddCard(
#                         customer_id=customer.customer_id,
#                         tapcard_serial=serial_number,
#                         card_type=category.category_name,
#                         card_data=None,
#                         card_item=None,
#                         active="yes"
#                     )
#                     db.add(new_add_card)

#             # Step 6: Mark cards as allocated
#             for card in unassigned_cards:
#                 card.allocated = "yes"

#             # Step 7: Delete processed products from AddProduct table
#             db.query(AddProduct).filter(AddProduct.user_id == user.id).delete()
#             db.commit()
            

#             print(f"Cards successfully allocated for user {user.id}")

#         elif event["type"] == "payment_intent.payment_failed":
#             payment_intent = event["data"]["object"]
#             print(f"PaymentIntent {payment_intent['id']} failed.")
#             # Add logic for handling failed payments, if needed

#         return JSONResponse(status_code=200, content={"status": "success"})

#     except stripe.error.SignatureVerificationError:
#         print("Invalid signature.")
#         raise HTTPException(status_code=400, detail="Invalid signature")
#     except Exception as e:
#         print("Webhook error:", e)
#         raise HTTPException(status_code=400, detail=f"Webhook error: {str(e)}")

@router.get("/payment1", response_class=HTMLResponse)
async def payment(request: Request):
    """
    Render the index.html page for the payment interface.
    """
    return templates.TemplateResponse("pay.html", {"request": request})
@router.post("/create-payment-intent")
async def create_payment_intent(request: Request, db: Session = Depends(get_db)):
    try:
        # Parse the request body
        body = await request.json()
        amount = body.get('amount')

        if amount is None or not isinstance(amount, int):
            raise HTTPException(status_code=400, detail="Invalid or missing amount")

        # Create a PaymentIntent
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency='usd',
            payment_method_types=['card'],
        )
        return {"paymentIntentClientSecret": intent.client_secret}
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=500, detail="Payment error occurred")




# # New PaymentIntent Request Model
# class PaymentIntentRequest(BaseModel):
#     token: str
#     amount: int  # Total amount in the smallest currency unit (e.g., cents for USD)
#     currency: str = "usd"  # Currency code, default is "usd"

# # API to Create PaymentIntent and Return Client Secret
# @router.post("/create-payment-intent")
# async def create_payment_intent(data: PaymentIntentRequest, db: Session = Depends(get_db)):
#     """
#     Create a PaymentIntent and return client secret along with saved cards.
#     """
#     try:
#         # Verify token and fetch user details
#         email = verify_token(data.token, credentials_exception=None, db=db)
#         user = db.query(usermodels.Signup).filter(usermodels.Signup.email == email).first()
#         if not user:
#             raise HTTPException(status_code=404, detail="User not found")
        
#         # Retrieve Stripe customer
#         customer = db.query(Customer).filter(Customer.email_address == email).first()
#         if not customer:
#             raise HTTPException(status_code=404, detail="Customer not found")

#         # Create PaymentIntent
#         intent = stripe.PaymentIntent.create(
#             amount=data.amount,
#             currency=data.currency,
#             customer=customer.customer_id,
#         )

#         # Fetch saved cards
#         payment_methods = stripe.PaymentMethod.list(
#             customer=customer.customer_id,
#             type="card",
#         )
#         saved_cards = [
#             {"id": pm.id, "last4": pm.card.last4, "brand": pm.card.brand}
#             for pm in payment_methods.data
#         ]

#         return {
#             "client_secret": intent.client_secret,
#             "saved_cards": saved_cards,
#         }

#     except stripe.error.StripeError as e:
#         raise HTTPException(status_code=400, detail=f"Stripe error: {e.user_message}")
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# # Endpoint to create a Stripe checkout session

# @router.get("/get-payment-details/{user_id}")
# def get_payment_details(user_id: int, db: Session = Depends(get_db)):
#     # Fetch user's order or subscription details
#     user = db.query(usermodels.Signup).filter(usermodels.Signup.id == user_id).first()
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")

#     # Calculate the total amount (example logic)
#     order_total = calculate_order_total(user_id, db)  # Implement your own logic
#     if order_total <= 0:
#         raise HTTPException(status_code=400, detail="Invalid order total")

#     return {
#         "user_id": user_id,
#         "amount": order_total,  # Total in smallest currency unit (e.g., cents for USD)
#         "currency": "usd",
#     }










