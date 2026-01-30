from fastapi import FastAPI, APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import pytz
from passlib.context import CryptContext
from jose import JWTError, jwt

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Security
security = HTTPBearer()

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Your session expired. Please log in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if user is None:
        raise credentials_exception
    
    # Convert ISO string timestamps back to datetime
    if isinstance(user.get('created_at'), str):
        user['created_at'] = datetime.fromisoformat(user['created_at'])
    
    return user

# Models
class UserRegister(BaseModel):
    username: str
    password: str
    timezone: str = "UTC"

class UserLogin(BaseModel):
    username: str
    password: str

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    password_hash: str
    timezone: str
    is_admin: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    username: str
    timezone: str
    is_admin: bool
    created_at: datetime

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class BookingCreate(BaseModel):
    title: str
    start_time: str  # ISO string in UTC
    end_time: str    # ISO string in UTC
    notes: Optional[str] = None
    user_timezone: str  # Original timezone for reference

class Booking(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    user_name: str
    title: str
    start_time: str  # ISO string in UTC
    end_time: str    # ISO string in UTC
    notes: Optional[str] = None
    user_timezone: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ConflictNotification(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    booking1_id: str
    booking2_id: str
    user1_id: str
    user2_id: str
    user1_name: str
    user2_name: str
    conflict_start: str
    conflict_end: str
    resolved: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Routes
@api_router.get("/")
async def root():
    return {"message": "NotCluely API"}

# Auth routes
@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserRegister):
    # Validate input
    username = user_data.username.strip().lower()
    
    if len(username) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username must be at least 3 characters"
        )
    
    if len(user_data.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters"
        )
    
    # Check if username already exists (case-insensitive)
    existing = await db.users.find_one({"username": username})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Check if user should be admin (username is "rutvik", case-insensitive)
    is_admin = username == "rutvik"
    
    # Create user
    user = User(
        username=username,
        password_hash=get_password_hash(user_data.password),
        timezone=user_data.timezone,
        is_admin=is_admin
    )
    
    doc = user.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.users.insert_one(doc)
    
    # Create access token
    access_token = create_access_token(data={"sub": user.id})
    
    user_response = UserResponse(
        id=user.id,
        username=user.username,
        timezone=user.timezone,
        is_admin=user.is_admin,
        created_at=user.created_at
    )
    
    return TokenResponse(access_token=access_token, user=user_response)

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(user_data: UserLogin):
    # Find user (case-insensitive username)
    username = user_data.username.strip().lower()
    user = await db.users.find_one({"username": username}, {"_id": 0})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Verify password
    if not verify_password(user_data.password, user['password_hash']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Update admin status on every login (in case username changes)
    is_admin = username == "rutvik"
    if user.get('is_admin') != is_admin:
        await db.users.update_one(
            {"id": user['id']},
            {"$set": {"is_admin": is_admin}}
        )
        user['is_admin'] = is_admin
    
    # Create access token
    access_token = create_access_token(data={"sub": user['id']})
    
    # Convert ISO string timestamps
    if isinstance(user.get('created_at'), str):
        user['created_at'] = datetime.fromisoformat(user['created_at'])
    
    user_response = UserResponse(
        id=user['id'],
        username=user['username'],
        timezone=user['timezone'],
        is_admin=user['is_admin'],
        created_at=user['created_at']
    )
    
    return TokenResponse(access_token=access_token, user=user_response)

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(
        id=current_user['id'],
        username=current_user['username'],
        timezone=current_user['timezone'],
        is_admin=current_user['is_admin'],
        created_at=current_user['created_at']
    )

@api_router.post("/auth/logout")
async def logout():
    # In JWT, logout is handled client-side by removing the token
    return {"message": "Logged out successfully"}

# User routes
@api_router.put("/users/timezone")
async def update_user_timezone(timezone: str, current_user: dict = Depends(get_current_user)):
    result = await db.users.update_one(
        {"id": current_user['id']},
        {"$set": {"timezone": timezone}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"success": True}

@api_router.get("/users", response_model=List[UserResponse])
async def get_all_users(current_user: dict = Depends(get_current_user)):
    users = await db.users.find({}, {"_id": 0, "password_hash": 0}).to_list(1000)
    
    result = []
    for user in users:
        if isinstance(user['created_at'], str):
            user['created_at'] = datetime.fromisoformat(user['created_at'])
        result.append(UserResponse(**user))
    
    return result

# Booking routes
@api_router.post("/bookings", response_model=Booking)
async def create_booking(booking_data: BookingCreate, current_user: dict = Depends(get_current_user)):
    # Check for conflicts
    start_dt = datetime.fromisoformat(booking_data.start_time.replace('Z', '+00:00'))
    end_dt = datetime.fromisoformat(booking_data.end_time.replace('Z', '+00:00'))
    
    existing_bookings = await db.bookings.find({}, {"_id": 0}).to_list(1000)
    
    conflicts = []
    for existing in existing_bookings:
        existing_start = datetime.fromisoformat(existing['start_time'].replace('Z', '+00:00'))
        existing_end = datetime.fromisoformat(existing['end_time'].replace('Z', '+00:00'))
        
        # Check for overlap
        if (start_dt < existing_end and end_dt > existing_start):
            conflicts.append(existing)
    
    booking = Booking(
        user_id=current_user['id'],
        user_name=current_user['username'],
        title=booking_data.title,
        start_time=booking_data.start_time,
        end_time=booking_data.end_time,
        notes=booking_data.notes,
        user_timezone=booking_data.user_timezone
    )
    
    doc = booking.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.bookings.insert_one(doc)
    
    # Create conflict notifications if there are conflicts
    for conflict in conflicts:
        conflict_notif = ConflictNotification(
            booking1_id=conflict['id'],
            booking2_id=booking.id,
            user1_id=conflict['user_id'],
            user2_id=current_user['id'],
            user1_name=conflict['user_name'],
            user2_name=current_user['username'],
            conflict_start=max(booking_data.start_time, conflict['start_time']),
            conflict_end=min(booking_data.end_time, conflict['end_time'])
        )
        
        conflict_doc = conflict_notif.model_dump()
        conflict_doc['created_at'] = conflict_doc['created_at'].isoformat()
        
        await db.conflicts.insert_one(conflict_doc)
    
    return booking

@api_router.get("/bookings", response_model=List[Booking])
async def get_bookings(current_user: dict = Depends(get_current_user)):
    bookings = await db.bookings.find({}, {"_id": 0}).to_list(1000)
    
    for booking in bookings:
        if isinstance(booking['created_at'], str):
            booking['created_at'] = datetime.fromisoformat(booking['created_at'])
    
    return bookings

@api_router.delete("/bookings/{booking_id}")
async def delete_booking(booking_id: str, current_user: dict = Depends(get_current_user)):
    # Get booking
    booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Check if user owns the booking or is admin
    if booking['user_id'] != current_user['id'] and not current_user.get('is_admin', False):
        raise HTTPException(
            status_code=403, 
            detail="You do not have permission to delete this booking"
        )
    
    await db.bookings.delete_one({"id": booking_id})
    
    # Delete related conflicts
    await db.conflicts.delete_many({
        "$or": [
            {"booking1_id": booking_id},
            {"booking2_id": booking_id}
        ]
    })
    
    return {"success": True}

# Conflict routes
@api_router.get("/conflicts", response_model=List[ConflictNotification])
async def get_conflicts(current_user: dict = Depends(get_current_user)):
    conflicts = await db.conflicts.find({"resolved": False}, {"_id": 0}).to_list(1000)
    
    for conflict in conflicts:
        if isinstance(conflict['created_at'], str):
            conflict['created_at'] = datetime.fromisoformat(conflict['created_at'])
    
    return conflicts

@api_router.get("/conflicts/user", response_model=List[ConflictNotification])
async def get_user_conflicts(current_user: dict = Depends(get_current_user)):
    conflicts = await db.conflicts.find({
        "$or": [
            {"user1_id": current_user['id']},
            {"user2_id": current_user['id']}
        ],
        "resolved": False
    }, {"_id": 0}).to_list(1000)
    
    for conflict in conflicts:
        if isinstance(conflict['created_at'], str):
            conflict['created_at'] = datetime.fromisoformat(conflict['created_at'])
    
    return conflicts

@api_router.put("/conflicts/{conflict_id}/resolve")
async def resolve_conflict(conflict_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.conflicts.update_one(
        {"id": conflict_id},
        {"$set": {"resolved": True}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Conflict not found")
    
    return {"success": True}

# Timezone utility endpoint
@api_router.get("/timezones")
async def get_timezones():
    return {"timezones": pytz.all_timezones}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()