from fastapi import APIRouter, HTTPException, Depends, Header
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from typing import Dict, Optional
import json
from pathlib import Path
import jwt
from passlib.context import CryptContext

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Security configurations
SECRET_KEY = "your-secret-key-here"  # In production, use env variables
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserAuth(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# File paths
DATA_DIR = Path("data")
USERS_FILE = DATA_DIR / "users.json"
BLACKLIST_FILE = DATA_DIR / "token_blacklist.json"

def load_users() -> Dict:
    """Load users from JSON file"""
    if not USERS_FILE.exists():
        return {}
    with open(USERS_FILE, 'r') as f:
        return json.load(f)

def save_users(users: Dict) -> None:
    """Save users to JSON file"""
    DATA_DIR.mkdir(exist_ok=True)
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

def load_blacklist() -> Dict:
    """Load token blacklist"""
    if not BLACKLIST_FILE.exists():
        return {}
    with open(BLACKLIST_FILE, 'r') as f:
        return json.load(f)

def save_blacklist(blacklist: Dict) -> None:
    """Save token blacklist"""
    DATA_DIR.mkdir(exist_ok=True)
    with open(BLACKLIST_FILE, 'w') as f:
        json.dump(blacklist, f, indent=4)

def create_access_token(data: dict):
    """Create JWT token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Validate JWT token and return current user"""
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Check if token is blacklisted
    blacklist = load_blacklist()
    if token in blacklist:
        raise credentials_exception

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    users = load_users()
    if email not in users:
        raise credentials_exception
    return email

@router.post("/signup", response_model=Token)
async def signup(user: UserAuth):
    try:
        users = load_users()
        
        if user.email in users:
            raise HTTPException(
                status_code=400,
                detail="User already exists"
            )
        
        # Hash the password
        hashed_password = pwd_context.hash(user.password)
        
        users[user.email] = {
            "email": user.email,
            "password": hashed_password,
            "created_at": datetime.now().isoformat()
        }
        
        save_users(users)
        
        # Create access token
        access_token = create_access_token({"sub": user.email})
        return {"access_token": access_token, "token_type": "bearer"}
    
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=400,
            detail="Could not create account"
        )

@router.post("/login", response_model=Token)
async def login(user: UserAuth):
    try:
        users = load_users()
        
        if user.email not in users:
            raise HTTPException(
                status_code=401,
                detail="Invalid credentials"
            )
        
        stored_user = users[user.email]
        if not pwd_context.verify(user.password, stored_user["password"]):
            raise HTTPException(
                status_code=401,
                detail="Invalid credentials"
            )
        
        # Create access token
        access_token = create_access_token({"sub": user.email})
        return {"access_token": access_token, "token_type": "bearer"}
    
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

@router.post("/logout")
async def logout(current_user: str = Depends(get_current_user),
                authorization: str = Header(...)):
    try:
        token = authorization.split(" ")[1]
        blacklist = load_blacklist()
        blacklist[token] = datetime.now().isoformat()
        save_blacklist(blacklist)
        return {"message": "Logout successful"}
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail="Logout failed"
        )