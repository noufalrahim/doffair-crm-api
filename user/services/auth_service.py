from odmantic import AIOEngine
from fastapi import HTTPException
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from bson import ObjectId

from user.models.user import User
from user.schemas.auth import UserSignupRequest, UserLoginRequest
from core.config import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Create JWT token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=7)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm="HS256")
    return encoded_jwt


async def signup_user(engine: AIOEngine, payload: UserSignupRequest) -> User:
    """
    Create a new user account
    """
    # Check if email already exists
    existing_email = await engine.find_one(User, User.email == payload.email)
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Check if phone already exists
    existing_phone = await engine.find_one(User, User.phone == payload.phone)
    if existing_phone:
        raise HTTPException(status_code=400, detail="Phone number already registered")
    
    # Create user
    user = User(
        name=payload.name,
        phone=payload.phone,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    
    await engine.save(user)
    return user


async def login_user(engine: AIOEngine, payload: UserLoginRequest) -> tuple[User, str]:
    """
    Login user and return user object + JWT token
    """
    # Find user
    user = await engine.find_one(User, User.email == payload.email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Verify password
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Check if active
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")
    
    # Create token
    access_token = create_access_token(
        data={
            "user_id": str(user.id),
            "email": user.email,
            "role": "user",
        }
    )
    
    return user, access_token
