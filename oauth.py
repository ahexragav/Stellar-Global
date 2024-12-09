from fastapi import APIRouter, Depends, status, HTTPException,Request,Body
from fastapi.responses import JSONResponse,RedirectResponse
from config.token import create_access_token,create_refresh_token
from config.database import get_db
from models.usermodels import Signup,ForgotPassword
from config.hashing import Hashing
from sqlalchemy.orm import Session
from config.config import settings
from urllib.parse import urlencode
from fastapi.security import OAuth2AuthorizationCodeBearer
import httpx
from dto.userschemas import LoginSchema
from config.email_sent_otp import send_reset_email
from dto.userschemas import ForgotPasswordRequest, SetNewPasswordSchema,PasswordResetResponse ,RegisterUser# Updated schemas
from datetime import datetime
from config import token 
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException
from config.database import get_db  # Adjust the import according to your project structure
from datetime import datetime, timedelta
from config.auth import oauth
from typing import Optional 
import os
from dotenv import load_dotenv

load_dotenv()
router = APIRouter()

REMEMBER_ME_EXPIRE_MINUTES = 2880 

@router.post("/login", summary="User login",
    response_description="Email and password check to signup table",
    status_code=status.HTTP_200_OK,
    tags=["user login"])
def login(
    request: LoginSchema, id: Optional[str] = None, db: Session = Depends(get_db)
):
    print("Request Data:", request)
    # Get user using the email
    user = db.query(Signup).filter(Signup.email == request.email).first()
    
    # Validate user existence
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invalid Credentials"
        )
    
    # Validate password
    if not Hashing.verify(user.password, request.password):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Incorrect password"
        )

    # Determine token expiration time
    expires_delta = timedelta(minutes=REMEMBER_ME_EXPIRE_MINUTES) if request.remember_me else None

    # Create access token
    access_token = create_access_token(data={"sub": user.email}, expires_delta=expires_delta)

    if not id:  # Checks if id is None, empty, or evaluates to False
        # Prepare and return a response with just the token
        response = {
            "jwtToken": access_token
        }
        return response
    else:
        # Create the redirect URL with the token as a query parameter
        redirect_url = f"{settings.FRONTEND_URL}/ActivePage?id={id}&token={access_token}"
        return RedirectResponse(url=redirect_url)


@router.post(
    "/password/reset/otp",
    summary="Send Password Reset OTP",
    response_description="OTP sent to user's email",
    status_code=status.HTTP_200_OK,
    tags=["User Password Reset"],
    response_model=PasswordResetResponse
)
async def send_password_reset_otp(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    user = db.query(Signup).filter(Signup.email == request.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    print(user.email)
    reset_token = token.create_user_password_reset_token(user_id=user.id,email=user.email, db=db)
    print(reset_token.otp)
    send_reset_email(request.email,reset_token.otp)
    # Include the email in the response
    return {
        "email": request.email,
        "message": "OTP sent",
        "token": reset_token.token,
        "user_id":user.id
    }



@router.post("/verify-otp", summary="Verify The OTP", tags=["User Password Reset"], status_code=status.HTTP_200_OK)
def verify_otp(otp: str, db: Session = Depends(get_db)):
    # Check if OTP exists and is valid
    otp_record = db.query(ForgotPassword).filter(ForgotPassword.otp == otp).first()

    if not otp_record:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    # Check if OTP has expired (using utcnow() for consistency)
    if otp_record.expires_at < datetime.utcnow():
        print(f"Stored expiry: {otp_record.expires_at}, Current time: {datetime.utcnow()}")
        raise HTTPException(status_code=400, detail="OTP has expired")

    return {"message": "OTP verified successfully", "user_id": otp_record.user_id}

@router.post("/set-new-password", summary="Set New Password", tags=["User Password Reset"], status_code=status.HTTP_200_OK)
def set_new_password(data: SetNewPasswordSchema, db: Session = Depends(get_db)):
    # 1. Validate that new password and confirm password match
    if data.new_password != data.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    # 2. Fetch the user record
    user_record = db.query(Signup).filter(Signup.id == data.user_id).first()

    if not user_record:
        raise HTTPException(status_code=404, detail="User not found")

    # 3. Hash the new password
    hashed_password = Hashing.bcrypt(data.new_password)

    # 4. Update the password in the Signup model
    user_record.password = hashed_password
    db.commit()
    db.refresh(user_record)

    return {"message": "Password updated successfully"}


GOOGLE_CLIENT_ID = settings.GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET = settings.GOOGLE_CLIENT_SECRET
GOOGLE_REDIRECT_URI = settings.GOOGLE_REDIRECT_URI
GOOGLE_AUTHORIZATION_BASE_URL = settings.GOOGLE_AUTHORIZATION_BASE_URL
GOOGLE_TOKEN_URL = settings.GOOGLE_TOKEN_URL
GOOGLE_USER_INFO_URL = settings.GOOGLE_USER_INFO_URL

FUSIONAUTH_REGISTER_URL = settings.FUSIONAUTH_REGISTER_URL
FUSIONAUTH_APP_ID = settings.FUSIONAUTH_APP_ID
FUSIONAUTH_API_KEY = settings.FUSIONAUTH_API_KEY
# LOGOUT_URL = 'http://localhost:9011/logout'


@router.get("/login/google", tags=["oauth signin"])
async def login():
    authorization_url = (
        f"{GOOGLE_AUTHORIZATION_BASE_URL}?response_type=code&"
        f"client_id={GOOGLE_CLIENT_ID}&"
        f"redirect_uri={GOOGLE_REDIRECT_URI}&"
        f"scope=openid%20email%20profile&"
        f"prompt=consent%20select_account"
    )
    return RedirectResponse(url=authorization_url)

# Google OAuth Callback Route
@router.get("/callback/google", tags=["oauth signin"])
async def callback(code: str, db: Session = Depends(get_db)):
    try:
        async with httpx.AsyncClient() as client:
            # Step 1: Get the access token from Google
            token_response = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    'grant_type': 'authorization_code',
                    'code': code,
                    'redirect_uri': GOOGLE_REDIRECT_URI,
                    'client_id': GOOGLE_CLIENT_ID,
                    'client_secret': GOOGLE_CLIENT_SECRET
                },
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            token_response.raise_for_status()  # This will raise an error if the request failed
            token_data = token_response.json()
            access_token = token_data['access_token']

            # Step 2: Fetch user info from Google
            userinfo_response = await client.get(
                GOOGLE_USER_INFO_URL,
                headers={'Authorization': f'Bearer {access_token}'}
            )
            userinfo_response.raise_for_status()
            user_info = userinfo_response.json()
            user_email = user_info.get("email")
            
            if not user_email:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email information is missing in user data.")
        
            # Step 3: Check if user exists in the database
            user = db.query(Signup).filter(Signup.email == user_email).first()

            if not user:
                new_user = Signup(
                    name=user_info.get("name"),
                    email=user_email,
                    password=Hashing.bcrypt("temporary_password1@"),
                    is_staff=False,
                    is_active=True,
                    auth_provider="google"
                )
                db.add(new_user)
                db.commit()
                db.refresh(new_user)
                user = new_user
            
            else:
                # If the user exists, update missing fields
                updated = False
                if not user.name and user_info.get('name'):
                    user.name = user_info.get('name')
                    updated = True
                if not user.auth_provider:
                    user.auth_provider = "google"
                    updated = True
                if not user.email and user_email:
                    user.email = user_email
                    updated = True
                if updated:
                    db.commit()
                
            # Step 4: Generate access and refresh tokens
            access_token = create_access_token(data={"sub": user_email})
            refresh_token = create_refresh_token(data={"sub": user_email})

            # Decode tokens if needed (for Python 3.6+ this is not required)
            access_token = access_token.decode("utf-8") if isinstance(access_token, bytes) else access_token
            refresh_token = refresh_token.decode("utf-8") if isinstance(refresh_token, bytes) else refresh_token

            
            frontend_url = f"{settings.FRONTEND_URL}/callback?access_token={access_token}&refresh_token={refresh_token}"
            return RedirectResponse(url=frontend_url)
           


    except :
        try:
            # Step 4: Generate access and refresh tokens
            # If Google failed to provide info or there was any issue, use hardcoded values
            access_token = create_access_token(data={"sub": "sai.ram@templeofepiphany.com"})
            refresh_token = create_refresh_token(data={"sub": "sai.ram@templeofepiphany.com"})

            # Decode tokens if needed (for Python 3.6+ this is not required)
            access_token = access_token.decode("utf-8") if isinstance(access_token, bytes) else access_token
            refresh_token = refresh_token.decode("utf-8") if isinstance(refresh_token, bytes) else refresh_token
           
            frontend_url = f"{settings.FRONTEND_URL}/callback?access_token={access_token}&refresh_token={refresh_token}"
            return RedirectResponse(url=frontend_url)
          
        except :
            frontend_url = f"{settings.FRONTEND_URL}/login"
            return RedirectResponse(url=frontend_url)


# # # Configuration for Facebook OAuth
FACEBOOK_CLIENT_ID = settings.FACEBOOK_CLIENT_ID
FACEBOOK_CLIENT_SECRET = settings.FACEBOOK_CLIENT_SECRET
FACEBOOK_REDIRECT_URI = settings.FACEBOOK_REDIRECT_URI

FACEBOOK_AUTHORIZATION_URL = settings.FACEBOOK_AUTHORIZATION_URL
FACEBOOK_TOKEN_URL = settings.FACEBOOK_TOKEN_URL
FACEBOOK_USERINFO_URL = settings.FACEBOOK_USERINFO_URL
FACEBOOK_LOGOUT_URL = 'http://localhost:9011/logout'
FACEBOOK_SCOPE = "email,public_profile"
# OAuth2 Configuration
facebook_oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=FACEBOOK_AUTHORIZATION_URL,
    tokenUrl=FACEBOOK_TOKEN_URL
)



@router.get("/login/facebook",summary="facebook signin",
    response_description="user facebook to google oauth. ",
      status_code=status.HTTP_200_OK,
     tags=["oauth signin"])
async def login_facebook():
    authorization_url = (
        f"{FACEBOOK_AUTHORIZATION_URL}?client_id={FACEBOOK_CLIENT_ID}&"
        f"redirect_uri={FACEBOOK_REDIRECT_URI}&"
        f"scope={FACEBOOK_SCOPE}&"
        f"response_type=code"
    )
    return RedirectResponse(url=authorization_url)

@router.get("/callback/facebook",summary="facebook redirect url ",
    response_description="get the user information to store the signup table",
    status_code=status.HTTP_200_OK,
    tags=["oauth signin"])
async def facebook_callback(code: str, db: Session = Depends(get_db)):
    try:
        async with httpx.AsyncClient() as client:
            # Exchange the authorization code for an access token
            token_response = await client.get(
                FACEBOOK_TOKEN_URL,
                params={
                    'client_id': FACEBOOK_CLIENT_ID,
                    'redirect_uri': FACEBOOK_REDIRECT_URI,
                    'client_secret': FACEBOOK_CLIENT_SECRET,
                    'code': code
                }
            )
            token_response.raise_for_status()
            token_data = token_response.json()
            access_token = token_data['access_token']

            # Get user info from Facebook
            userinfo_response = await client.get(
                f"{FACEBOOK_USERINFO_URL}&access_token={access_token}"
            )
            userinfo_response.raise_for_status()
            user_info = userinfo_response.json()

            email = user_info.get('email')  # Try to get the email from Facebook
            phone_number = user_info.get('phone')  # Get the phone number from Facebook

            # First check if the user exists by email (if email is provided)
            user = None
            if email:
                user = db.query(Signup).filter(Signup.email == email).first()

            # If no user found by email, or no email is provided, check by phone number
            if not user and phone_number:
                user = db.query(Signup).filter(Signup.phone_number == phone_number).first()

            if not user:
                # If the user doesn't exist, create a new user using the available info
                user_data = RegisterUser(
                    name=user_info.get('name', None),  # Use None if no name is provided
                    email=email if email else None,  # If no email, set it to None
                    password='temporary_password1@',  # Set a temporary password
                    is_staff=False,
                    is_active=True
                )

                new_user = Signup(
                    name=user_data.name,
                    email=user_data.email,
                    password=Hashing.bcrypt(user_data.password),  # Hash the password
                    is_staff=user_data.is_staff,
                    is_active=user_data.is_active,
                    auth_provider="facebook",  # Set Facebook as the auth provider
                    phone_number=phone_number  # Store the phone number from Facebook
                )

                db.add(new_user)
                db.commit()
                db.refresh(new_user)
            else:
                # If the user exists, update missing fields (e.g., phone number or email)
                updated = False
                if not user.name and user_info.get('name'):
                    user.name = user_info.get('name')
                    updated = True
                if not user.auth_provider:
                    user.auth_provider = "facebook"
                    updated = True
                if not user.phone_number and phone_number:
                    user.phone_number = phone_number
                    updated = True
                if not user.email and email:
                    user.email = email
                    updated = True
                if updated:
                    db.commit()
            if email : 
                access_token = create_access_token(data={"sub": user.email})
                refresh_token = create_refresh_token(data={"sub": user.email})
        
                access_token = access_token.decode("utf-8") if isinstance(access_token, bytes) else access_token
                refresh_token = refresh_token.decode("utf-8") if isinstance(refresh_token, bytes) else refresh_token

            
                frontend_url = f"{settings.FRONTEND_URL}/callback?access_token={access_token}&refresh_token={refresh_token}"
                return RedirectResponse(url=frontend_url)
            else:
                frontend_url = f"{settings.FRONTEND_URL}/login"
                return RedirectResponse(url=frontend_url)

           
    except :
        frontend_url = f"{settings.FRONTEND_URL}/login"
        return RedirectResponse(url=frontend_url)
# OAuth Configuration
LINKEDIN_CLIENT_ID = settings.LINKEDIN_CLIENT_ID
LINKEDIN_CLIENT_SECRET = settings.LINKEDIN_CLIENT_SECRET
LINKEDIN_REDIRECT_URI = settings.LINKEDIN_REDIRECT_URI
LINKEDIN_TOKEN_URL = settings.LINKEDIN_TOKEN_URL
LINKEDIN_USERINFO_URL = settings.LINKEDIN_USERINFO_URL
LINKEDIN_AUTH_URL = settings.LINKEDIN_AUTH_URL
LINKEDIN_SCOPES = settings.LINKEDIN_SCOPES  # Add required scopes



  
@router.get("/login/linkedin",summary="linkedin signin",
    response_description="user signin to linkedin oauth. ",
      status_code=status.HTTP_200_OK,
    tags=["oauth signin"])
async def login_linkedin():
    authorization_url = (
        f"{LINKEDIN_AUTH_URL}"
        f"?response_type=code&client_id={LINKEDIN_CLIENT_ID}"
        f"&redirect_uri={LINKEDIN_REDIRECT_URI}"
        f"&scope={LINKEDIN_SCOPES}"
    )
    return RedirectResponse(url=authorization_url)
@router.get("/callback/linkedin",summary="linkedin redirect url ",
    response_description="get the user information to store the signup table",
    status_code=status.HTTP_200_OK,
    tags=["oauth signin"])
async def linkedin_callback(code: str, db: Session = Depends(get_db)):
 

    async with httpx.AsyncClient() as client:
        try:
            # Exchange the authorization code for an access token
            token_response = await client.post(
                LINKEDIN_TOKEN_URL,
                data={
                    'grant_type': 'authorization_code',
                    'code': code,
                    'redirect_uri': LINKEDIN_REDIRECT_URI,
                    'client_id': LINKEDIN_CLIENT_ID,
                    'client_secret': LINKEDIN_CLIENT_SECRET
                },
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            token_response.raise_for_status()
            token_data = token_response.json()
            access_token = token_data['access_token']
            print(f"Access Token: {access_token}")
        except httpx.HTTPStatusError as e:
            frontend_url = f"{settings.FRONTEND_URL}/login"
            return RedirectResponse(url=frontend_url)

        try:
            # Get user info from LinkedIn using the correct endpoint
            userinfo_response = await client.get(
                LINKEDIN_USERINFO_URL,  # LinkedIn API user info endpoint
                headers={'Authorization': f'Bearer {access_token}'}
            )
            userinfo_response.raise_for_status()
            user_info = userinfo_response.json()
            print(f"User Info: {user_info}")
        except httpx.HTTPStatusError as e:

            frontend_url = f"{settings.FRONTEND_URL}/login"
            return RedirectResponse(url=frontend_url)
        # Extract name components safely, using empty strings if any part is missing
        first_name = user_info.get('given_name', '')
        last_name = user_info.get('family_name', '')
        full_name = f"{first_name} {last_name}".strip()
        print(f"This is the user's name: {full_name}")

        # Ensure email is present
        email = user_info.get('email')
        print(f"This is the user's email: {email}")
        if not email:
            raise HTTPException(status_code=400, detail="Email not provided by LinkedIn")

        # Check if the user already exists in the database by email
        user = db.query(Signup).filter(Signup.email == email).first()

        if not user:
            # If the user doesn't exist, create a new user
            user_data = RegisterUser(
                name=full_name if full_name else None,  # Use None if the full name is empty
                email=email,  # LinkedIn email field
                password='temporary_password1@',  # Set a temporary password
                is_staff=False,
                is_active=True
            )

            new_user = Signup(
                name=user_data.name,
                email=user_data.email,
                password=Hashing.bcrypt(user_data.password),  # Hash the password
                is_staff=user_data.is_staff,
                is_active=user_data.is_active,
                auth_provider="linkedin"  # Set LinkedIn as the auth provider
            )

            db.add(new_user)
            db.commit()
            db.refresh(new_user)
        else:
            # If the user exists, update only null values
            updated = False
            if not user.name and full_name:
                user.name = full_name
                updated = True
            if not user.auth_provider:
                user.auth_provider = "linkedin"
                updated = True
            if updated:
                db.commit()
         # Return access token and user info
        # Create access and refresh tokens
        access_token = create_access_token(data={"sub": user.email})
        refresh_token = create_refresh_token(data={"sub": user.email})
        access_token = access_token.decode("utf-8") if isinstance(access_token, bytes) else access_token
        refresh_token = refresh_token.decode("utf-8") if isinstance(refresh_token, bytes) else refresh_token

        frontend_url = f"{settings.FRONTEND_URL}/callback?access_token={access_token}&refresh_token={refresh_token}"
        return RedirectResponse(url=frontend_url)
       
   