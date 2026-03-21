"""Authentication and authorization system (Updated Version)."""
from __future__ import annotations

import os
import bcrypt
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from core.config import get_settings

settings = get_settings()
security = HTTPBearer()


class TokenData(BaseModel):
    """Token data model."""
    user_id: Optional[str] = None
    exp: Optional[datetime] = None


class UserCreate(BaseModel):
    """User creation model."""
    email: str
    password: str
    name: str


class UserLogin(BaseModel):
    """User login model."""
    email: str
    password: str


class Token(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str
    expires_in: int


class User(BaseModel):
    """User model."""
    id: str
    email: str
    name: str
    created_at: datetime
    is_active: bool = True


class AuthService:
    """Authentication service."""
    
    def __init__(self):
        self.secret_key = settings.secret_key
        self.algorithm = settings.jwt_algorithm
        self.jwt_expiration = settings.jwt_expiration
    
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify a password against its hash."""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(seconds=self.jwt_expiration)
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(
            to_encode, 
            self.secret_key, 
            algorithm=self.algorithm
        )
        return encoded_jwt
    
    def verify_token(self, token: str) -> TokenData:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm]
            )
            user_id: str = payload.get("sub")
            exp: int = payload.get("exp")
            
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            return TokenData(user_id=user_id, exp=datetime.fromtimestamp(exp))
        
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    async def get_current_user(self, token: str) -> User:
        """Get current user from token."""
        # In a real implementation, this would query the database
        # For now, we'll create a mock user
        
        token_data = self.verify_token(token)
        
        # Mock user - in production, query from database
        user = User(
            id=token_data.user_id,
            email=f"user_{token_data.user_id}@example.com",
            name=f"User {token_data.user_id}",
            created_at=datetime.utcnow(),
            is_active=True
        )
        
        return user


# Global auth service instance
auth_service = AuthService()


async def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """FastAPI dependency to get current user from token."""
    token = credentials.credentials
    user = await auth_service.get_current_user(token)
    return user


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """FastAPI dependency to get optional current user."""
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        user = await auth_service.get_current_user(token)
        return user
    except HTTPException:
        return None


# Mock user database (in production, use real database)
MOCK_USERS = {
    "admin@calculo.com": {
        "id": "admin",
        "email": "admin@calculo.com",
        "password": auth_service.hash_password("admin123"),
        "name": "Administrator",
        "created_at": datetime.utcnow(),
        "is_active": True,
        "is_admin": True
    },
    "user@calculo.com": {
        "id": "user",
        "email": "user@calculo.com",
        "password": auth_service.hash_password("user123"),
        "name": "Regular User",
        "created_at": datetime.utcnow(),
        "is_active": True,
        "is_admin": False
    }
}


async def authenticate_user(email: str, password: str) -> Optional[User]:
    """Authenticate a user."""
    user_data = MOCK_USERS.get(email)
    
    if not user_data:
        return None
    
    if not auth_service.verify_password(password, user_data["password"]):
        return None
    
    return User(
        id=user_data["id"],
        email=user_data["email"],
        name=user_data["name"],
        created_at=user_data["created_at"],
        is_active=user_data["is_active"]
    )


async def create_user(user_create: UserCreate) -> User:
    """Create a new user."""
    if user_create.email in MOCK_USERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    hashed_password = auth_service.hash_password(user_create.password)
    
    new_user = {
        "id": str(UUID()),
        "email": user_create.email,
        "password": hashed_password,
        "name": user_create.name,
        "created_at": datetime.utcnow(),
        "is_active": True,
        "is_admin": False
    }
    
    MOCK_USERS[user_create.email] = new_user
    
    return User(
        id=new_user["id"],
        email=new_user["email"],
        name=new_user["name"],
        created_at=new_user["created_at"],
        is_active=new_user["is_active"]
    )


async def login_for_access_token(user_login: UserLogin) -> Token:
    """Login user and return access token."""
    user = await authenticate_user(user_login.email, user_login.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    access_token_expires = timedelta(seconds=settings.jwt_expiration)
    access_token = auth_service.create_access_token(
        data={"sub": user.id}
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.jwt_expiration
    )


# Rate limiting (simple in-memory implementation)
LOGIN_ATTEMPTS = {}


async def check_rate_limit(email: str, max_attempts: int = 5, window_minutes: int = 15):
    """Check if user has exceeded rate limit."""
    now = datetime.utcnow()
    window_start = now - timedelta(minutes=window_minutes)
    
    # Clean old attempts
    if email in LOGIN_ATTEMPTS:
        LOGIN_ATTEMPTS[email] = [
            attempt_time for attempt_time in LOGIN_ATTEMPTS[email]
            if attempt_time > window_start
        ]
    else:
        LOGIN_ATTEMPTS[email] = []
    
    # Check current attempts
    if len(LOGIN_ATTEMPTS[email]) >= max_attempts:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many login attempts. Try again in {window_minutes} minutes."
        )
    
    # Add current attempt
    LOGIN_ATTEMPTS[email].append(now)
