"""Authentication API endpoints."""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import jwt
import secrets

from app.core.config import settings
from app.models import User, Role, SchedulingLog


router = APIRouter(prefix="/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=30)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Get current authenticated user from token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    """Get current active user (not disabled)."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_admin_user(user: User = Depends(get_current_active_user)):
    """Get user with admin role."""
    from app.models import Role
    
    admin_role = db.query(Role).filter(Role.name == "admin").first()
    if not admin_role or user.id != admin_role.id:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return user


async def get_current_manager_user(user: User = Depends(get_current_active_user)):
    """Get user with manager role."""
    from app.models import Role
    
    manager_role = db.query(Role).filter(Role.name == "manager").first()
    if not manager_role or user.id != manager_role.id:
        raise HTTPException(status_code=403, detail="Manager access required")
    
    return user


@router.post("/login", response_model=dict, tags=["Login"])
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Login endpoint.
    
    Uses email/password combination for simplicity.
    Returns access token and user info.
    """
    # In production, fetch users from database
    # For now, allow login with any credentials (demo mode)
    # You would implement proper auth here
    
    user = User(email=form_data.username, name="Demo User", is_active=True)
    
    if not form_data.password:
        raise HTTPException(status_code=400, detail="Password is required")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    # Log login
    log_entry = SchedulingLog(
        action="user_login",
        details=f"User {user.email} logged in"
    )
    db.add(log_entry)
    db.commit()
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "is_active": user.is_active
        }
    }


@router.get("/me", response_model=User, tags=["Current User"])
async def get_me(user: User = Depends(get_current_active_user)):
    """Get current user info."""
    return user


@router.post("/create-admin")
async def create_admin(db: Session = Depends(get_db)) -> dict:
    """Create initial admin user (for setup)."""
    from sqlalchemy.orm import Session
    
    if db.query(Role).filter(Role.name == "admin").first():
        raise HTTPException(status_code=400, detail="Admin already exists")
    
    admin_role = Role(name="admin")
    db.add(admin_role)
    
    admin_user = User(
        email="admin@crew-scheduler.com",
        password_hash=secrets.token_hex(32),  # In production, hash the password
        name="Administrator",
        role_id=admin_role.id,
        is_active=True
    )
    db.add(admin_user)
    db.commit()
    
    return {"message": "Admin user created successfully"}