from fastapi import Depends,HTTPException,status
from .database import get_db,Session
from .token import verify_token
from typing import Annotated
from models import usermodels
def get_current_admin(token: str, db: Session = Depends(get_db)):
    user_data = verify_token(token)  # Decodes the token and verifies the user

    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if the user has an "admin" role
    if user_data.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action",
        )
    
    return user_data

def get_current_user(token: str, db: Session = Depends(get_db)):
    user_data = verify_token(token)  # Decodes the token and verifies the user

    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if the user has an "admin" role
    if user_data.get("role") == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action",
        )
    
    return user_data


CurrentUser = Annotated[usermodels.Signup, Depends(get_current_user)]
CurrentAdmin = Annotated[usermodels.Signup, Depends(get_current_admin)]