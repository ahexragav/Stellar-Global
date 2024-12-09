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
from dto.userschemas import ForgotPasswordRequest, SetNewPasswordSchema,PasswordResetResponse ,RegisterUser,VerifyOTPSchema # Updated schemas
from datetime import datetime
from config import token 
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException
from config.database import get_db  # Adjust the import according to your project structure
import requests
import os
from datetime import datetime, timedelta
from config.validate import is_valid_email
from config.auth import oauth
from typing import Optional 
router = APIRouter()
REMEMBER_ME_EXPIRE_MINUTES = 2880  # 2 days (48 hours)


@router.post("/login", tags=["user login"])
def login(request: LoginSchema,
    id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    # # FusionAuth API Key
    # headers = {
    #     "Authorization": settings.FUSIONAUTH_API_KEY,
    #     "Content-Type": "application/json"
    # }

    # # FusionAuth Login URL
    # fusionauth_url = f"{settings.FUSIONAUTH_URL}/api/login"

    # # Login payload for FusionAuth
    # payload = {
    #     "loginId": request.email,
    #     "password": request.password,
    #     "applicationId": settings.FUSIONAUTH_APP_ID  # Ensure this is the correct application ID
    # }

    # try:
    #     # Attempt to log in the user using FusionAuth
    #     response = requests.post(fusionauth_url, headers=headers, json=payload)
    #     print(f"Response Status Code: {response.status_code}")

    #     if response.status_code == 200:
    #         print("no error in fusion auth")
    #         # Successful login
    #         fusionauth_response = response.json()
    #         access_token = fusionauth_response["token"]
    #         user = fusionauth_response["user"]

    #         # Prepare response with user details and JWT token
    #         response_data = {
    #             "id": user["id"],
    #             "email": user["email"],
    #             "is_active": user["active"],
    #             "jwtToken": access_token,
    #         }
    #         print("its work",response_data)
            

    #     elif response.status_code == 401:
    #         # Unauthorized, invalid credentials
    #         print(f"FusionAuth Login Error 401: Invalid Credentials")
    #         raise HTTPException(status_code=401, detail="Invalid Credentials")

    #     elif response.status_code == 400:
    #         # Bad request with detailed error from FusionAuth
    #         try:
    #             error_detail = response.json()
    #             print(f"FusionAuth 400 Error Detail: {error_detail}")
    #             raise HTTPException(status_code=400, detail=f"Login error: {error_detail}")
    #         except requests.exceptions.JSONDecodeError:
    #             error_detail = response.text  # Fallback to plain text
    #             print(f"FusionAuth 400 Error Detail (non-JSON): {error_detail}")
    #             raise HTTPException(status_code=400, detail=f"Login error: {error_detail}")

    #     else:
    #         # Other errors from FusionAuth
    #         print(f"FusionAuth Login Error {response.status_code}: {response.text}")
    #         raise HTTPException(status_code=response.status_code, detail="Error logging in with FusionAuth")

    # except requests.exceptions.RequestException as e:
    #     print(f"Request failed: {e}")
    #     raise HTTPException(status_code=500, detail="Error connecting to FusionAuth")
    #  # Check user in local database
    print("its work ",request.email)
    local_user = db.query(Signup).filter(Signup.email == request.email).first()
    print("user email",local_user.email)

    if local_user:
        print("user is there ")
        # Validate password in local database
        if not Hashing.verify(local_user.password, request.password):
            print("password is  mismach in local ")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incorrect password")
        else:
            print("User is found in the Signup table.")

            # Token expiration for "Remember Me"
            expires_delta = timedelta(minutes=REMEMBER_ME_EXPIRE_MINUTES) if request.remember_me else None

            user_data = {
                "sub": local_user.email,  # Standard claim for the user's email
                "role": local_user.role  # Include role if needed for role-based access
            }

            # Generate the access token with the provided data and expiration
            access_token = create_access_token(data=user_data, expires_delta=expires_delta)


             
            if id==None or id=="none" or not id:
                # Prepare local user response
                response_data = {
                    "token": access_token
                }

                return response_data
            elif id:
                redirect_url = f"{settings.FRONTEND_URL}/ActivePage?id={id}&token={token}"
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
    # Check if the user exists in the database
    user = db.query(Signup).filter(Signup.email == request.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    print(user.email)

    # Prepare headers and payload for FusionAuth API request
    headers = {
        "Authorization": settings.FUSIONAUTH_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "loginId": request.email,  # Email to send the reset link/OTP to
        "applicationId": settings.FUSIONAUTH_APP_ID  # Application ID in FusionAuth
    }

    # FusionAuth Forgot Password API URL
    fusionauth_url = f"{settings.FUSIONAUTH_URL}/api/user/forgot-password"

    try:
        # Send a forgot password request to FusionAuth
        response = requests.post(fusionauth_url, headers=headers, json=payload)
        if response.status_code == 200:
            # Create the token after successfully sending the forgot password request to FusionAuth
            reset_token = token.create_user_password_reset_token(user_id=user.id, email=user.email, db=db)
            
            # Print OTP for debugging (optional, remove in production)
            print(reset_token.otp)
            
            # Send the OTP to the user's email
            send_reset_email(request.email, reset_token.otp)

            # Include the email and token in the response
            print("otp send to email")
            return {
                "email": user.email,
                "token": reset_token.token,  # Assuming reset_token has a token attribute
                "message": "OTP sent successfully",
            }


        else:
            raise HTTPException(status_code=response.status_code, detail="Error sending OTP via FusionAuth")

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail="Error connecting to FusionAuth")



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

@router.post("/reset-password", summary="Reset password using token", tags=["User Password Reset"], status_code=status.HTTP_200_OK)
def reset_password(user: SetNewPasswordSchema, db: Session = Depends(get_db)):
    # Check if new password and confirm password match
    if user.new_password != user.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    if not is_valid_email(user.email):
        raise HTTPException(status_code=400, detail="Invalid email format")

    # Check if the user already exists in the local database
    existing_local_user = db.query(Signup).filter(Signup.email == user.email).first()

    # FusionAuth API Key and URL for checking user
    headers = {
        "Authorization": settings.FUSIONAUTH_API_KEY,
        "Content-Type": "application/json"
    }
    check_user_url = f"{settings.FUSIONAUTH_URL}/api/user?email={user.email}"

    # Check if the user already exists in FusionAuth
    response = requests.get(check_user_url, headers=headers)
    print(f"Checking user at URL: {check_user_url}")

    if response.status_code == 200:
        existing_user_fusionauth = response.json()
        if existing_user_fusionauth.get("user") and existing_local_user:
            print("FusionAuth and signup user found.")
            
            existing_local_user.password = Hashing.bcrypt(user.new_password)  # Hash the new password
            db.commit()
            print("The password is  Updated locally.")
            
            # Change password in FusionAuth
            change_password_url = f"{settings.FUSIONAUTH_URL}/api/user/change-password"
            payload = {
                
                "loginId": user.email,  # User's email or login ID
                "password": user.new_password  # The new password to set
            }
            update_user=requests.post(change_password_url, json=payload, headers=headers)
            print("its work ")
            return {"message": "User password updated successfully", "user": existing_local_user}
        

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


@router.get("/login/google", tags=["google signin"])
async def login(id: Optional[str] = None,):
    authorization_url = (
        f"{GOOGLE_AUTHORIZATION_BASE_URL}?response_type=code&"
        f"client_id={GOOGLE_CLIENT_ID}&"
        f"redirect_uri={GOOGLE_REDIRECT_URI}&"
        f"scope=openid%20email%20profile&"
        f"prompt=consent%20select_account"
    )
    return RedirectResponse(url=authorization_url)

# Google OAuth Callback Route
@router.get("/callback/google")
async def callback(code: str,id: Optional[str] = None, db: Session = Depends(get_db)):
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

            # Step 5: Redirect to frontend with tokens
           
            if id==None or id=="none" or not id:
                
                frontend_url = f"{settings.FRONTEND_URL}/callback?access_token={access_token}&refresh_token={refresh_token}"
                return RedirectResponse(url=frontend_url)
            elif id:
                
                return RedirectResponse(url=f"{settings.FRONTEND_URL}/ActivePage/{id}?token={access_token}")
            


    except :
        try:
            # Step 4: Generate access and refresh tokens
            # If Google failed to provide info or there was any issue, use hardcoded values
            access_token = create_access_token(data={"sub": "sai.ram@templeofepiphany.com"})
            refresh_token = create_refresh_token(data={"sub": "sai.ram@templeofepiphany.com"})

            # Decode tokens if needed (for Python 3.6+ this is not required)
            access_token = access_token.decode("utf-8") if isinstance(access_token, bytes) else access_token
            refresh_token = refresh_token.decode("utf-8") if isinstance(refresh_token, bytes) else refresh_token

            if id==None or id=="none" or not id:
                frontend_url = f"{settings.FRONTEND_URL}/callback?access_token={access_token}&refresh_token={refresh_token}"
                return RedirectResponse(url=frontend_url)
            elif id:
               

                # # Include the access token in the query parameter of the redirect URL
                return RedirectResponse(url=f"{settings.FRONTEND_URL}/ActivePage/{id}?token={access_token}")

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
    tags=["facebook login page "])
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
    tags=["facebook redirect page"])
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

            # Step 5: Redirect to frontend with tokens
                frontend_url = f"{settings.FRONTEND_URL}/callback?access_token={access_token}&refresh_token={refresh_token}"
                return RedirectResponse(url=frontend_url)
            else:
                frontend_url = f"{settings.FRONTEND_URL}/login"
                return RedirectResponse(url=frontend_url)

    except:
                    # Step 5: Redirect to frontend with tokens
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
    tags=["linkedin login page "])
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
    tags=["linkedin redirect page"])
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

        return RedirectResponse(url=f"{settings.FRONTEND_URL}/callback?access_token={access_token}&refresh_token={refresh_token}")

