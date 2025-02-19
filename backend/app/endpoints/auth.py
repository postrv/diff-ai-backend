# backend/app/endpoints/auth.py
from datetime import datetime, timedelta, UTC
from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel

from backend.app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

# Security scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


# Models
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


# For demonstration purposes, a dummy user is defined here.
# In production, use a proper user database with password hashing
fake_user = {
    "username": "testuser",
    "password": "testpassword"  # In production, store hashed passwords!
}


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a new JWT access token.

    Args:
        data: The data to encode in the token
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    expire = datetime.now(UTC) + (
        expires_delta if expires_delta else timedelta(minutes=settings.access_token_expire_minutes))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Dependency that validates the current user from the token.

    Args:
        token: JWT token from request

    Returns:
        User data if valid

    Raises:
        HTTPException: If token is invalid
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    # In production, retrieve user from database
    if token_data.username != fake_user["username"]:
        raise credentials_exception

    return {"username": token_data.username}


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticate user and provide access token.

    Args:
        form_data: Username and password from form

    Returns:
        JWT access token

    Raises:
        HTTPException: If authentication fails
    """
    if form_data.username != fake_user["username"] or form_data.password != fake_user["password"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    access_token = create_access_token(data={"sub": fake_user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me")
async def read_users_me(current_user: dict = Depends(get_current_user)):
    """
    Get information about the currently authenticated user.

    Args:
        current_user: User data from token validation

    Returns:
        Current user information
    """
    return current_user