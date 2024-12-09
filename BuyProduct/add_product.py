from fastapi import APIRouter, Depends,HTTPException,status
from sqlalchemy.orm import Session
from config.database import get_db
from models.productmodels import *
from models.usermodels import *
from  dto import productschemas as schemas
from sqlalchemy.orm import Session
from config.database import get_db
from fastapi import Depends, HTTPException
from fastapi.routing import APIRouter
from typing import List
from sqlalchemy.sql import func
from config.token import verify_token
from datetime import datetime
router = APIRouter(tags=["add product"])
@router.get("/add_product/")
def get_cart_items(token: str, db: Session = Depends(get_db)):
    """
    Retrieves all items in the cart for a specific user based on the JWT token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    print("mycard page is work ")
    try:
       
        email = verify_token(token, credentials_exception, db)
        user=db.query(Signup).filter(Signup.email==email).first()
        
        
        # Get cart items for the user
        cart_items = db.query(AddProduct).filter(AddProduct.user_id == user.id).all()
        if not cart_items:
            raise HTTPException(status_code=404, detail="No items in cart")

        return cart_items
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")
    
@router.post("/add_product/", response_model=dict)
def add_to_cart(item: schemas.AddProductCreate, token: str, db: Session = Depends(get_db)):
    """
    Adds a product to the cart for a specific user based on JWT token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    print("mycard page is work ")
    try:
       
        email = verify_token(token, credentials_exception, db)
        user=db.query(Signup).filter(Signup.email==email).first()
        # Check if the product is already in the cart for this user
        existing_item = (
            db.query(AddProduct)
            .filter(AddProduct.product_id == item.product_id, AddProduct.user_id == user.id)
            .first()
        )
        if existing_item:
            # Update the quantity if the product is already in the cart
            existing_item.quantity += item.quantity
            db.commit()
            db.refresh(existing_item)
            return {"message": "Quantity updated in cart", "data": existing_item}

        # Add a new cart item
        new_cart_item = AddProduct(
            product_id=item.product_id,
            category_id=item.category_id,
            product_name=item.product_name,
            product_image=item.product_image,
            product_price=item.product_price,
            quantity=item.quantity,
            user_id=user.id , # Use user_id from the decoded token
            attributes=item.attributes
        )
        db.add(new_cart_item)
        db.commit()
        db.refresh(new_cart_item)

        return {"message": "Product added to cart", "data": new_cart_item}
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")

@router.delete("/remove_add_product/{product_id}", response_model=dict)
def remove_from_cart(product_id: int, token: str, db: Session = Depends(get_db)):
    """
    Removes a product from the cart for a specific user based on JWT token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode token and get user details (email, user_id)
        email = verify_token(token, credentials_exception, db)

        user=db.query(Signup).filter(Signup.email==email).first()
        # Check if the product exists in the user's cart
        cart_item = db.query(AddProduct).filter(
            AddProduct.product_id == product_id,
            AddProduct.user_id == user.id
        ).first()

        if not cart_item:
            raise HTTPException(status_code=404, detail="Product not found in cart")

        # Remove the product from the cart
        db.delete(cart_item)
        db.commit()

        return {"message": "Product removed from cart", "data": cart_item}

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")



@router.post("/address", response_model=dict)
def add_customer_address(
    customer: schemas.AddressBase,
    token: str,
    db: Session = Depends(get_db)
):
    """
    Creates a new customer record based on the provided address and user token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode token to get the user's email
        email = verify_token(token, credentials_exception, db)

        # Check if the user exists
        user = db.query(Signup).filter(Signup.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        customer_data=db.query(Customer).filter(Customer.email_address==email).first()
        # Validate state lookup
        if customer_data:
            return {"message":"user is already add a address"}
        state = (
            db.query(StateLookup)
            .filter(StateLookup.state_name == customer.state)
            .first()
        )
        if not state:
            raise HTTPException(status_code=404, detail="Invalid state name")
        state_id = state.state_id

        # Generate a unique customer ID
        customer_id = f"CUS{user.id:03}"

        # Create the new customer object
        new_customer = Customer(
            customer_id=customer_id,
            first_name=customer.first_name,
            last_name=customer.last_name,
            email_address=email,
            recovery_email=customer.recovery_email,
            phone_number=customer.phone_number,
            title=customer.title,
            address_1=customer.address_1,
            address_2=customer.address_2,
            city=customer.city,
            state_abv=state_id,
            zip=customer.zip,
            zip_4=customer.zip_4,
            country=customer.country,
            account_creation_date=datetime.now(),
            last_login_date=datetime.now(),
            account_status="Active",
            preferred_contact_method=customer.preferred_contact_method,
            marketing_opt_in=customer.marketing_opt_in,
            created_by=email,
            creation_date=datetime.now(),
            last_modified_by=email,
            last_modified_date=datetime.now(),
            notes=None,
        )

        # Add the new customer to the database
        db.add(new_customer)
        db.commit()
        db.refresh(new_customer)

        return {"message": "Customer created successfully", "customer_id": new_customer.customer_id}

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")

@router.put("/address/", response_model=dict)
def update_address( 
    updated_address: schemas.AddressBase, 
    token: str, 
    db: Session = Depends(get_db)
):
    """
    Updates a customer's address.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode token and get user email
        email = verify_token(token, credentials_exception, db)

        # Retrieve the customer using customer_id and email
        customer = db.query(Customer).filter(
            Customer.email_address == email
        ).first()

        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        # Handle state separately if it's being updated
        if updated_address.state:
            state = db.query(StateLookup).filter(
                StateLookup.state_name == updated_address.state
            ).first()
            if not state:
                raise HTTPException(status_code=404, detail="Invalid state name")
            customer.state_abv = state.state_id  # Assign the correct ID

        # Update other customer details
        for key, value in updated_address.dict(exclude_unset=True).items():
            if key != "state":  # Skip "state" as it has been handled
                setattr(customer, key, value)

        # Update last_modified fields
        customer.last_modified_by = email
        customer.last_modified_date = datetime.now()

        # Commit the changes
        db.commit()
        db.refresh(customer)

        return {"message": "Customer address updated successfully", "data": customer}

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")


@router.delete("/address/", response_model=dict)
def delete_address( 
    token: str, 
    db: Session = Depends(get_db)
):
    """
    Deletes a customer's address.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode token and get user email
        email = verify_token(token, credentials_exception, db)

        # Retrieve the customer using customer_id and email
        customer = db.query(Customer).filter(
            Customer.email_address == email
        ).first()

        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        # Delete the customer
        db.delete(customer)
        db.commit()

        return {"message": "Customer address deleted successfully"}

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")



@router.get("/address", response_model=dict)
def get_customer_address(token: str, db: Session = Depends(get_db)):
    """
    Retrieve a customer's address based on the provided token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode token to get user's email
        email = verify_token(token, credentials_exception, db)

        # Check if the customer exists
        customer = db.query(Customer).filter(
            Customer.email_address == email
        ).first()

        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        state = (
            db.query(StateLookup)
            .filter(StateLookup.state_id == customer.state_abv)
            .first()
        )
        if not state:
            raise HTTPException(status_code=404, detail="Invalid state name")
        # Format the response data
        address_data = {
            "customer_id": customer.customer_id,
            "first_name": customer.first_name,
            "last_name": customer.last_name,
            "email_address": customer.email_address,
            "recovery_email": customer.recovery_email,
            "phone_number": customer.phone_number,
            "title": customer.title,
            "address_1": customer.address_1,
            "address_2": customer.address_2,
            "city": customer.city,
            "state_abv": state.state_name,
            "zip": customer.zip,
            "zip_4": customer.zip_4,
            "country": customer.country,
            "account_status": customer.account_status,
            "preferred_contact_method": customer.preferred_contact_method,
            "marketing_opt_in": customer.marketing_opt_in,
            "creation_date": customer.creation_date,
            "last_modified_date": customer.last_modified_date,
        }

        return {"message": "Customer address retrieved successfully", "data": address_data}

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")