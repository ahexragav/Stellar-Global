from fastapi import APIRouter, Depends,HTTPException
from sqlalchemy.orm import Session
from config.database import get_db
from models.usermodels import Signup
from dto.userschemas import RegisterUser
from .usersservice import UserService
from config.token import get_current_user
from config.validate import is_valid_email
import requests
from config.config import settings
from config.database import get_db
from config.hashing import Hashing
router = APIRouter(prefix="/user", tags=["Users"])

@router.get("/name")
def getAllUser():
    return {"message":"ragav"}

@router.get("/all")
def getAllUser(db: Session = Depends(get_db)):
    return UserService.get_all_users(db=db)



@router.post("/")
def signup(user: RegisterUser, db: Session = Depends(get_db)):
    # Validate email format
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
            if Hashing.verify(existing_local_user.password, "temporary_password1@"):
                existing_local_user.password = Hashing.bcrypt(user.password)  # Hash the new password
                db.commit()
                print("The password is temporary_password1@. Updated locally.")
                
                # Change password in FusionAuth
                change_password_url = f"{settings.FUSIONAUTH_URL}/api/user/change-password"
                payload = {
                    "currentPassword": "temporary_password1@",  # The current password in FusionAuth
                    "loginId": user.email,  # User's email or login ID
                    "password": user.password  # The new password to set
                }
                requests.post(change_password_url, json=payload, headers=headers)
                
                return {"message": "User password updated successfully", "user": existing_local_user}

    elif response.status_code == 404:
        # User not found in FusionAuth, proceed with registration
        print("User not found in FusionAuth, proceeding with registration.")
    else:
        raise HTTPException(status_code=response.status_code, detail="Error checking user in FusionAuth")

    # Register new user with FusionAuth
    registration_payload = {
        "user": {
            "email": user.email,
            "password": user.password,
            "active": True
        },
        "registration": {
            "applicationId": settings.FUSIONAUTH_APP_ID
        }
    }
    print(f"Registering user with payload: {registration_payload}")
    response = requests.post(f"{settings.FUSIONAUTH_URL}/api/user/registration", headers=headers, json=registration_payload)

    if response.status_code == 200:
        # Successfully registered in FusionAuth, now add to local database
        local_user = Signup(
            name=user.name,
            email=user.email,
            password=Hashing.bcrypt(user.password),
            is_staff=user.is_staff,
            is_active=True,
            auth_provider="fusionauth",
            role=user.role
        )
        db.add(local_user)
        db.commit()
        db.refresh(local_user)
        print("New user created.")
        return {"message": "User created successfully", "user": local_user}
    else:
        error_detail = response.json() if response.headers.get('Content-Type') == 'application/json' else response.text
        print(f"FusionAuth Registration Error Detail: {error_detail}")
        raise HTTPException(status_code=400, detail=f"Registration error: {error_detail}")


@router.get("/me")
def getMe(current_user: Signup = Depends(get_current_user)):
    return current_user

@router.post("/update/password")
def update_password():

    # Configuration
    api_key = 'EZa_G5HwfE_tH7I019iy9kFDJvH9vanP23RJY8xhloH5ps9ZJmoJzZjY'

    # API endpoint for changing user password
    url = "http://localhost:9011/api/user/change-password"

    # Headers including the API key
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json"
    }

    # Request payload (assuming you have the current password and new password)
    payload = {
        "currentPassword": "string15@",  # User's current password
        "loginId": "user15@example.com",  # User's login identifier (email or username)
        "password": "string11@"  # New password to set
    }

    # Send the request to change the password
    response = requests.post(url, json=payload, headers=headers)

    # Check response status
    if response.status_code == 200:
        print("Password changed successfully!")
    else:
        print(f"Error: {response.status_code} - {response.json()}")



@router.delete("/{userid}")
def deleteUser(userid: int, db: Session = Depends(get_db)):
    return UserService.deleteUser(userid=userid, db=db)