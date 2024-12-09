from typing import Annotated

from fastapi import Depends,HTTPException,status
from .database import Session,get_db
from app.guardian import models, selectors
import jwt
class TokenGenerator:
    """
    This class is used to generate and verify JWT tokens.

    Args:
        secret_key (str): The secret key to use for encoding and decoding the token.
    """

    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.settings = get_settings()

    def generate_token(
        self, token_type: Literal["access", "refresh"], sub: str, expire_in: int
    ) -> str:
        """This method generates a JWT token.

        Args:
            token_type (Literal["access", "refresh"]): The type of token to generate.
            sub (str): The subject of the token, typically the user's ID.
            expire_in (int): The time in minutes for access token or hours for refresh token to expire.

        Returns:
            str: The generated token.
        """
        if token_type not in ["access", "refresh"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error: Session Expired, Please Login again Type",
            )

        # Check if sub is valid
        if "-" not in sub:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error: Session Expired, Please Login again sub",
            )
        iat = datetime.now()
        if token_type == "access":
            expire = datetime.now() + timedelta(minutes=expire_in)
        else:
            expire = datetime.now() + timedelta(hours=expire_in)

        data = {
            "type": token_type,
            "sub": sub,
            "iat": iat.timestamp(),
            "exp": expire.timestamp(),
            "iss": "ibloom.io",
        }
        return jwt.encode(
            payload=data,
            key=self.secret_key,
            algorithm=self.settings.HASHING_ALGORITHM,
        )

    def verify_refresh_token(self, token: str, sub_head: str) -> str:
        """This method verifies the refresh token.

        Args:
            token (str): The refresh token.
            sub_head (str): The sub head of the token

        Returns:
            str: The user's ID.
        """
        try:
            payload = jwt.decode(
                jwt=token,
                key=self.secret_key,
                algorithms=self.settings.HASHING_ALGORITHM,
            )
            sub: str = payload.get("sub")
            if payload.get("type") != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Session Expired, Please Login again"
                )
            if sub is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Session Expired, Please Login again"
                )
            if sub.split("-")[0] != sub_head:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Session Expired, Please Login again"
                )
            return sub.split("-")[1]
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Session Expired, Please Login again"
            )
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Session Expired, Please Login again"
            )

    def verify_access_token(
        self, token: str, sub_head: str, raise_exception: bool = True
    ) -> str:
        """This method verifies an access token.

        Args:
            token (str): The access token.
            raise_exception (bool, optional): Whether to raise an exception if the token is invalid. Defaults to True.
            sub_head (str): The sub head of the token

        Returns:
            str: The user's ID.
        """
        try:
            payload = jwt.decode(
                jwt=token,
                key=self.secret_key,
                algorithms=self.settings.HASHING_ALGORITHM,
            )
            sub: str = payload.get("sub")
            if payload.get("type") != "access":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Session Expired, Please Login again"
                )
            if sub is None:
                if raise_exception:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED, detail="Session Expired, Please Login again"
                    )
                return None
            if sub.split("-")[0] != sub_head:
                if raise_exception:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED, detail="Session Expired, Please Login again"
                    )
                return None
            return sub.split("-")[1]
        except jwt.ExpiredSignatureError:
            if raise_exception:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Session Expired, Please Login again"
                )
            return None
        except jwt.PyJWTError:
            if raise_exception:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Session Expired, Please Login again"
                )
            return None
async def get_current_teacher(
    token: str = Header(alias="Authorization"), db: Session = Depends(get_db)
):
    """This function returns the current teacher based on the token provided"""
    try:
        token_type, token = token.split(" ")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session Expired, Please Login again",
        )
    if token_type != "Bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session Expired, Please Login again",
        )
    guardian_id = int(security.verify_guardian_access_token(token=token))
    if guardian := await get_guardian_by_id(
        guardian_id=guardian_id, db=db, raise_exception=False
    ):
        if guardian.account_type == "TEACHER":
            return guardian
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can access this endpoint",
        )
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Session Expired, Please Login again type",
    )
async def get_current_admin(
    token: str = Header(alias="Authorization"), db: Session = Depends(get_db)
):
    """This function returns the current admin

    Args:
        token (str, optional): The Authorization header. Defaults to Header(alias="Authorization
        db (Session): The database session

    Returns:
        models.Admin: The current admin
    """
    try:
        token_type, token = token.split(" ")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session Expired, Please Login again",
        )
    if token_type != "Bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session Expired, Please Login again",
        )
    admin_id = int(security.verify_admin_access_token(token=token))
    if admin := await get_admin_by_id(admin_id=admin_id, db=db, raise_exception=False):
        return admin
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Session Expired, Please Login again",
    )
CurrentGuardian = Annotated[models.Guardian, Depends(get_current_admin)]
CurrentTeacher = Annotated[models.Guardian, Depends(get_current_teacher)]

@router.get(
    "/guardian_subjects",
    summary="Get guardian subjects",
    response_description="Get guardian subjects",
    status_code=status.HTTP_200_OK
)
async def get_guardian_subjects(
    current_guardian: CurrentGuardian,
    db: DatabaseSession,
):
    # Retrieve guardian subjects from the database
    guardian_subjects = db.query(models.Guardian_Subjects).filter(
        models.Guardian_Subjects.guardian_id == current_guardian.id
    ).first()

    if guardian_subjects:
        # Parse the guardian_subjects JSON string into a Python dictionary
        guardian_subjects_data = json.loads(guardian_subjects.guardian_subjects)

        # Prepare the result list with grade names, is_active status, and subject details
        result = []
        for item in guardian_subjects_data:
            grade_id = item["grade"]
            subject_ids = item["subject"]

            # Fetch the grade name and is_active status
            grade_data = db.query(
                classroom_models.Grade.name, classroom_models.Grade.is_active
            ).filter(classroom_models.Grade.id == grade_id).first()
            grade_name = grade_data[0] if grade_data else None
            grade_is_active = grade_data[1] if grade_data else None
            
            # Fetch the subject details (name and is_active)
            subjects = db.query(
                classroom_models.Subject.name, classroom_models.Subject.is_active
            ).filter(classroom_models.Subject.id.in_(subject_ids)).all()
            subject_details = [{"name": subject[0], "is_active": subject[1]} for subject in subjects]
