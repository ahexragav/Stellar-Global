from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Signup(Base):
    __tablename__ = "signup"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=True)  # Nullable for OAuth users
    is_staff = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)  # Active status, set to true by default
    auth_provider = Column(String(50), nullable=False)  # e.g., 'normal', 'google', 'facebook'
    phone_number = Column(String(15), nullable=True)  # For Facebook users using phone numbers
    role = Column(String(50), nullable=False, default="user")  # User role, e.g., "admin", "user"

    # Relationship with ForgotPassword model
    password_reset_tokens = relationship("ForgotPassword", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Signup {self.email} | Role: {self.role}>"

class ForgotPassword(Base):
    __tablename__ = "forgot_password"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("signup.id", ondelete="CASCADE"), nullable=False)  # Updated foreign key reference
    email = Column(String(100), nullable=False)
    token = Column(String(255), unique=True, nullable=False)  # Added a max length for token
    expires_at = Column(DateTime, nullable=False)
    otp = Column(String(10), nullable=False)  # Assuming a fixed length OTP
    
    # Relationship with Signup model
    user = relationship("Signup", back_populates="password_reset_tokens")

    def __repr__(self):
        return f"<ResetToken for user {self.user.email}>"

