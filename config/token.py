

from fastapi import HTTPException
import requests
import datetime
from datetime import timedelta
import jwt
from jwt import PyJWTError,decode
from sqlalchemy.orm import Session
from config.database import get_db
from users.usersservice import UserService
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
import os
from dotenv import load_dotenv
from models.usermodels import ForgotPassword,Signup
from utils.otp import generate_otp
import httpx
# Load environment variables
load_dotenv()

# Constants
SECRET_KEY = os.getenv("SECRET_KEY", "default_secret")  # Environment variable for secret key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_MINUTES = 1440  # 1 day
REMEMBER_ME_EXPIRE_MINUTES = 2880  # 2 days

# OAuth2PasswordBearer is a class that returns a token from the request
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

def verify_admin(token: str, db: Session):
    try:
        payload = verify_token(token)
        email = payload.get("sub")  # Extract the email from the payload
        
        user = db.query(Signup).filter(Signup.email == email).first()
        if not user or user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required",
            )
        return email  # Return the verified email if the user is an admin
    except Exception as e:
        print("Error verifying admin:", e)  # Debugging line
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print("Decoded token payload:", payload)  # Debugging line
        return payload  # Return decoded token payload (e.g., including user data like `role`)
    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def create_access_token(data: dict, expires_delta: datetime.timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(hours=6)  # Default expiration to 6 hours
    
    to_encode.update({"exp": expire})
    
    # Ensure 'role' is included in the payload
    if "role" not in to_encode:
        to_encode["role"] = "user"  # Default to "user" if not present

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: datetime.timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:

        expire = datetime.datetime.utcnow() + datetime.timedelta(days=7)  # 7 days default expiration for refresh tokens
    
    # Add expiration and other claims to the token
    to_encode.update({
        "exp": expire,
        "role": data.get("role", "user")  # Include the role, default to "user" if not provided
    })
    
    # Create the JWT token
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
# Token creation functions
# def create_access_token(data: dict, expires_delta: datetime.timedelta = None):
#     to_encode = data.copy()
#     if expires_delta:
#         expire = datetime.datetime.utcnow() + expires_delta
#     else:
#         expire = datetime.datetime.utcnow() + datetime.timedelta(hours=6)  # Set expiration to 6 hours
#     to_encode.update({"exp": expire})
#     return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def fetch_linkedin_email(access_token: str) -> str:
    async with httpx.AsyncClient() as client:
        try:
            # Make an API call to LinkedIn to get the user's email address
            email_response = await client.get(
                "https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))",
                headers={'Authorization': f'Bearer {access_token}'}
            )
            email_response.raise_for_status()  # Raise an error for bad responses
            
            email_data = email_response.json()  # Parse the JSON response
            
            print(email_data)
            return email_data  # Return the user's email
        except httpx.HTTPStatusError as e:
            print(f"Error fetching LinkedIn email: {e.response.text}")
            return None  # Return None if there was an error
        except (IndexError, KeyError) as e:
            print(f"Error processing email data: {e}")
            return None  # Return None if email data structure is unexpected

PROVIDERS_CONFIG = {
    "google": {
        "public_key_url": "https://www.googleapis.com/oauth2/v3/certs",
        "userinfo_url": "https://www.googleapis.com/oauth2/v3/userinfo",
        "algorithm": "RS256",
    },
    "apple": {
        "public_key_url": "https://appleid.apple.com/auth/keys",
        "userinfo_url": "https://appleid.apple.com/auth/keys",  # Update as needed for user info
        "algorithm": "ES256",
    },
    "linkedin": {
        "public_key": None,  # LinkedIn verification will be done via API call
        "userinfo_url": "https://api.linkedin.com/v2/me",  # User info endpoint for LinkedIn
        "algorithm": None,
    },
    "facebook": {
        "public_key": None,  # Facebook verification will be done via API call
        "userinfo_url": "https://graph.facebook.com/me?fields=id,name,email,picture",  # User info endpoint for Facebook
        "algorithm": None,
    },
}

async def verify_oauth_token(token: str, provider: str, credentials_exception, db: Session):
    async with httpx.AsyncClient() as client:
        # Handle other providers (Google, LinkedIn, Facebook)
        userinfo_response = await client.get(
            PROVIDERS_CONFIG[provider]["userinfo_url"],
            headers={'Authorization': f'Bearer {token}'}
        )

        if userinfo_response.status_code != 200:
            print(f"Error: {userinfo_response.status_code}, {userinfo_response.text}")
            raise credentials_exception

        user_info = userinfo_response.json()
        
        # Extract email based on the provider
        if provider == "linkedin":
            email = await fetch_linkedin_email(token)  # Use the new function to fetch email
            if not email:
                raise credentials_exception  # Raise exception if email is not found
        elif provider == "facebook":
            email = user_info.get('email')
            if email is None:
                print("Email not found in Facebook user info response.")
                raise credentials_exception
        else:  # Default handling for Google and others
            email = user_info.get('email')

        if email is None:
            print("Email not found in user info response.")
            raise credentials_exception
        
        return email

# def verify_token(token: str, credentials_exception, db: Session):
#     """Verify the JWT token and return only the email."""
#     try:
#         print("token is come here ")
#         # Decode the JWT token
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         email: str = payload.get("sub")  # Get the email from the "sub" field
#         print("Decoded email:", email)
        
#         if email is None:
#             raise credentials_exception

#     except PyJWTError as e:
#         print("JWT error:", e)
#         raise credentials_exception
#     except Exception as e:
#         print("General error in verify_token:", e)
#         raise credentials_exception

#     # Check if the user exists (optional for email-only return)
#     try:
#         if not UserService.get_user(email=email, db=db):  # Assuming get_user checks the database
#             print("User not found in the database.")
#             raise credentials_exception
#     except Exception as e:
#         print("Error checking user in database:", e)
#         raise credentials_exception

#     # Return only the email
#     return email
 


def is_jwt_token(token: str) -> bool:
    """Check if the token is in JWT format (basic check)."""
    try:
        # A basic check for JWT structure (3 parts separated by '.')
        return len(token.split('.')) == 3
    except Exception:
        return False
# Retrieve the current user using OAuth2 scheme
def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    """Get the current logged-in user from the JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    return verify_token(token=token, credentials_exception=credentials_exception, db=db)




ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Or whatever your access token expiry time is
OTP_EXPIRE_SECONDS = 300  # Set OTP to expire in 10 seconds

# Create password reset token for a user
def create_user_password_reset_token(user_id: int, db: Session, email: str):
    print("I get the user id", user_id)
    
    # Set JWT token expiration
    token_expires_at = datetime.datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = jwt.encode({"sub": str(user_id), "exp": token_expires_at}, SECRET_KEY, algorithm="HS256")
    print("This is token expiration time:", token_expires_at)
    
    # Generate OTP and set its expiration
    otp = generate_otp()
    otp_expires_at = datetime.datetime.utcnow() + timedelta(seconds=OTP_EXPIRE_SECONDS)  # Short OTP expiration time
    print("Generated OTP:", otp)
    print("OTP expires at:", otp_expires_at)
    
    # Store in the ForgotPassword table
    reset_token = ForgotPassword(user_id=user_id, email=email, token=token, expires_at=otp_expires_at, otp=otp)
    db.add(reset_token)
    db.commit()
    db.refresh(reset_token)
    
    return reset_token

# Verify the password reset token
def verify_password_reset_token(token: str, db: Session):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token"
            )
        reset_token = db.query(ForgotPassword).filter_by(token=token).first()
        if reset_token is None or reset_token.expires_at < datetime.datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token expired or invalid"
            )
        return reset_token
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")

# Reset user's password
def reset_user_password(user_id: int, new_password: str, db: Session):
    user = db.query(Signup).filter_by(id=user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    user.password = new_password  # Assume password hashing is done before saving
    db.commit()
    return user