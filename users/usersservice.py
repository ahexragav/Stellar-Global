from fastapi import Depends
from config.database import get_db

from models.usermodels import Signup
from sqlalchemy.orm import Session
from dto.userschemas import RegisterUser
from config.hashing import Hashing
from fastapi import HTTPException
class UserService:
    @staticmethod
    def get_all_users(db: Session):
        return db.query(Signup).all()

    @staticmethod
    def get_user(email: str, db: Session):
        return db.query(Signup).filter(Signup.email == email).first()
    @staticmethod
    def create_user(user: RegisterUser, db: Session):
        # Ensure auth_provider is set, default to 'normal' for standard signup
        auth_provider = user.auth_provider if user.auth_provider else "normal"

        # Create a new user
        db_user = Signup(
            name=user.name,
            email=user.email,
            password=Hashing.bcrypt(user.password),
            is_staff=user.is_staff,
            is_active=user.is_active,
            auth_provider=auth_provider,  # Ensure this is set
            phone_number=user.phone_number
        )

        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        # Set password to None when returning user info
        db_user.password = None

        return db_user

    @staticmethod
    def update_password(user_id: int, new_password: str, db: Session):
        # Fetch user by ID and update password
        db_user = db.query(Signup).filter(Signup.id == user_id).first()

        if db_user:
            db_user.password = Hashing.bcrypt(new_password)
            db.commit()
            return db_user
        else:
            raise HTTPException(status_code=404, detail="User not found")

    @staticmethod
    def deleteUser(userid: int, db: Session):
        db_userid = db.query(Signup).filter(Signup.id == userid).first()

        db.delete(db_userid)

        db.commit()

        return db_userid
