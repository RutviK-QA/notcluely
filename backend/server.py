from fastapi import FastAPI, APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
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
import sqlite3
import json
import hashlib

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# SQLite connection
DB_PATH = os.environ.get('DATABASE_URL', 'notcluely.db')
if DB_PATH.startswith('sqlite:///'):
    DB_PATH = DB_PATH.replace('sqlite:///', '')

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with tables"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            timezone TEXT NOT NULL DEFAULT 'UTC',
            is_admin BOOLEAN NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        )
    ''')
    
    # Bookings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            user_name TEXT NOT NULL,
            title TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            notes TEXT,
            user_timezone TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Conflicts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conflicts (
            id TEXT PRIMARY KEY,
            booking1_id TEXT NOT NULL,
            booking2_id TEXT NOT NULL,
            user1_id TEXT NOT NULL,
            user2_id TEXT NOT NULL,
            user1_name TEXT NOT NULL,
            user2_name TEXT NOT NULL,
            conflict_start TEXT NOT NULL,
            conflict_end TEXT NOT NULL,
            resolved BOOLEAN NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY (booking1_id) REFERENCES bookings (id),
            FOREIGN KEY (booking2_id) REFERENCES bookings (id),
            FOREIGN KEY (user1_id) REFERENCES users (id),
            FOREIGN KEY (user2_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# Password hashing - Industry standard configuration
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # NIST recommended round count
)

# JWT settings
SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Security
security = HTTPBearer()
LOGIN_ATTEMPTS = {}  # Track login attempts per username
MAX_LOGIN_ATTEMPTS = 5
LOCK_TIME_MINUTES = 15

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Helper functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a bcrypt hash.
    
    Passlib handles all bcrypt compatibility and truncation internally.
    No manual truncation needed - passlib is the industry standard.
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False

def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt via passlib.
    
    Industry best practice:
    - Passlib handles the 72-byte bcrypt limit internally
    - Uses bcrypt__rounds=12 (NIST recommended)
    - Automatically generates secure salt
    - No manual truncation needed
    """
    try:
        return pwd_context.hash(password)
    except Exception as e:
        logger.error(f"Password hashing error: {e}")
        raise

def create_access_token(data: dict, is_admin: bool = False):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "is_admin": is_admin})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def check_rate_limit(username: str) -> bool:
    """Check if user has exceeded login attempt limit"""
    now = datetime.now(timezone.utc)
    
    if username not in LOGIN_ATTEMPTS:
        LOGIN_ATTEMPTS[username] = []
    
    # Remove old attempts outside lock window
    LOGIN_ATTEMPTS[username] = [
        ts for ts in LOGIN_ATTEMPTS[username]
        if (now - ts).total_seconds() < (LOCK_TIME_MINUTES * 60)
    ]
    
    # Check if locked
    if len(LOGIN_ATTEMPTS[username]) >= MAX_LOGIN_ATTEMPTS:
        return False
    
    return True

def record_login_attempt(username: str):
    """Record a login attempt"""
    if username not in LOGIN_ATTEMPTS:
        LOGIN_ATTEMPTS[username] = []
    LOGIN_ATTEMPTS[username].append(datetime.now(timezone.utc))

def clear_login_attempts(username: str):
    """Clear login attempts on successful login"""
    if username in LOGIN_ATTEMPTS:
        LOGIN_ATTEMPTS[username] = []

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
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
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user_row = cursor.fetchone()
    conn.close()
    
    if user_row is None:
        raise credentials_exception
    
    user = dict(user_row)
    user['is_admin'] = bool(user['is_admin'])
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
    
    # Check for valid username characters (alphanumeric and underscore only)
    if not username.replace('_', '').isalnum():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username can only contain letters, numbers, and underscores"
        )
    
    if len(user_data.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters"
        )
    
    # Check password complexity
    has_upper = any(c.isupper() for c in user_data.password)
    has_lower = any(c.islower() for c in user_data.password)
    has_digit = any(c.isdigit() for c in user_data.password)
    
    if not (has_upper and has_lower and has_digit):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain uppercase, lowercase, and digits"
        )
    
    # Check if username already exists (case-insensitive)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
    existing = cursor.fetchone()
    
    if existing:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Validate timezone
    if not user_data.timezone:
        user_data.timezone = "UTC"
    
    if user_data.timezone not in pytz.all_timezones:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid timezone"
        )
    
    # Check if user should be admin (username is "rutvik", case-insensitive)
    is_admin = username == "rutvik"
    
    # Create user
    user_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    password_hash = get_password_hash(user_data.password)
    
    cursor.execute('''
        INSERT INTO users (id, username, password_hash, timezone, is_admin, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, username, password_hash, user_data.timezone, is_admin, created_at))
    
    conn.commit()
    conn.close()
    
    # Create access token with admin status
    access_token = create_access_token(data={"sub": user_id}, is_admin=is_admin)
    
    user_response = UserResponse(
        id=user_id,
        username=username,
        timezone=user_data.timezone,
        is_admin=is_admin,
        created_at=datetime.fromisoformat(created_at)
    )
    
    return TokenResponse(access_token=access_token, user=user_response)

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(user_data: UserLogin):
    # Find user (case-insensitive username)
    username = user_data.username.strip().lower()
    
    # Check rate limit
    if not check_rate_limit(username):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many login attempts. Please try again in {LOCK_TIME_MINUTES} minutes."
        )
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user_row = cursor.fetchone()
    conn.close()
    
    if not user_row:
        # Record failed attempt without revealing if user exists
        record_login_attempt(username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    user = dict(user_row)
    
    # Verify password
    if not verify_password(user_data.password, user['password_hash']):
        # Record failed attempt
        record_login_attempt(username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Clear rate limit on successful login
    clear_login_attempts(username)
    
    # Update admin status on every login (in case username changes)
    is_admin = username == "rutvik"
    if user.get('is_admin') != is_admin:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET is_admin = ? WHERE id = ?', (is_admin, user['id']))
        conn.commit()
        conn.close()
        user['is_admin'] = is_admin
    
    # Create access token with admin status
    access_token = create_access_token(data={"sub": user['id']}, is_admin=is_admin)
    
    # Convert ISO string timestamps
    if isinstance(user.get('created_at'), str):
        user['created_at'] = datetime.fromisoformat(user['created_at'])
    
    user['is_admin'] = bool(user['is_admin'])
    
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
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET timezone = ? WHERE id = ?', (timezone, current_user['id']))
    conn.commit()
    
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")
    
    conn.close()
    return {"success": True}

@api_router.get("/users", response_model=List[UserResponse])
async def get_all_users(current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, timezone, is_admin, created_at FROM users')
    users_rows = cursor.fetchall()
    conn.close()
    
    result = []
    for user_row in users_rows:
        user = dict(user_row)
        user['is_admin'] = bool(user['is_admin'])
        if isinstance(user['created_at'], str):
            user['created_at'] = datetime.fromisoformat(user['created_at'])
        result.append(UserResponse(**user))
    
    return result

# Booking routes
@api_router.post("/bookings", response_model=Booking)
async def create_booking(booking_data: BookingCreate, current_user: dict = Depends(get_current_user)):
    # Validate booking data
    if not booking_data.title or not booking_data.title.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking title cannot be empty"
        )
    
    if len(booking_data.title.strip()) > 255:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking title too long (max 255 characters)"
        )
    
    # Check for conflicts
    start_dt = datetime.fromisoformat(booking_data.start_time.replace('Z', '+00:00'))
    end_dt = datetime.fromisoformat(booking_data.end_time.replace('Z', '+00:00'))
    
    # Validate date range
    now = datetime.now(timezone.utc)
    if start_dt < now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create bookings in the past"
        )
    
    if start_dt >= end_dt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start time must be before end time"
        )
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM bookings')
    existing_bookings = [dict(row) for row in cursor.fetchall()]
    
    conflicts = []
    for existing in existing_bookings:
        existing_start = datetime.fromisoformat(existing['start_time'].replace('Z', '+00:00'))
        existing_end = datetime.fromisoformat(existing['end_time'].replace('Z', '+00:00'))
        
        # Check for overlap
        if (start_dt < existing_end and end_dt > existing_start):
            conflicts.append(existing)
    
    # Create booking
    booking_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    
    cursor.execute('''
        INSERT INTO bookings (id, user_id, user_name, title, start_time, end_time, notes, user_timezone, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        booking_id, current_user['id'], current_user['username'], 
        booking_data.title, booking_data.start_time, booking_data.end_time, 
        booking_data.notes, booking_data.user_timezone, created_at
    ))
    
    conn.commit()
    
    # Create conflict notifications if there are conflicts
    for conflict in conflicts:
        conflict_id = str(uuid.uuid4())
        conflict_notif_created_at = datetime.now(timezone.utc).isoformat()
        
        cursor.execute('''
            INSERT INTO conflicts (id, booking1_id, booking2_id, user1_id, user2_id, user1_name, user2_name, conflict_start, conflict_end, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            conflict_id, conflict['id'], booking_id, conflict['user_id'], current_user['id'],
            conflict['user_name'], current_user['username'],
            max(booking_data.start_time, conflict['start_time']),
            min(booking_data.end_time, conflict['end_time']),
            conflict_notif_created_at
        ))
    
    conn.commit()
    conn.close()
    
    return Booking(
        id=booking_id,
        user_id=current_user['id'],
        user_name=current_user['username'],
        title=booking_data.title,
        start_time=booking_data.start_time,
        end_time=booking_data.end_time,
        notes=booking_data.notes,
        user_timezone=booking_data.user_timezone,
        created_at=datetime.fromisoformat(created_at)
    )

@api_router.get("/bookings", response_model=List[Booking])
async def get_bookings(current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    
    # If admin, return all bookings. Otherwise, return only their own.
    if current_user.get('is_admin', False):
        cursor.execute('SELECT * FROM bookings')
    else:
        cursor.execute('SELECT * FROM bookings WHERE user_id = ?', (current_user['id'],))
    
    bookings_rows = cursor.fetchall()
    conn.close()
    
    result = []
    for booking_row in bookings_rows:
        booking = dict(booking_row)
        if isinstance(booking['created_at'], str):
            booking['created_at'] = datetime.fromisoformat(booking['created_at'])
        result.append(Booking(**booking))
    
    return result

@api_router.delete("/bookings/{booking_id}")
async def delete_booking(booking_id: str, current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    
    # Get booking
    cursor.execute('SELECT * FROM bookings WHERE id = ?', (booking_id,))
    booking_row = cursor.fetchone()
    
    if not booking_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Booking not found")
    
    booking = dict(booking_row)
    
    # Check if user owns the booking or is admin
    if booking['user_id'] != current_user['id'] and not current_user.get('is_admin', False):
        conn.close()
        raise HTTPException(
            status_code=403, 
            detail="You do not have permission to delete this booking"
        )
    
    cursor.execute('DELETE FROM bookings WHERE id = ?', (booking_id,))
    
    # Delete related conflicts
    cursor.execute('''
        DELETE FROM conflicts 
        WHERE booking1_id = ? OR booking2_id = ?
    ''', (booking_id, booking_id))
    
    conn.commit()
    conn.close()
    
    return {"success": True}

# Conflict routes
@api_router.get("/conflicts", response_model=List[ConflictNotification])
async def get_conflicts(current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    
    if current_user.get('is_admin', False):
        cursor.execute('SELECT * FROM conflicts WHERE resolved = 0')
    else:
        cursor.execute('''
            SELECT * FROM conflicts 
            WHERE resolved = 0 AND (user1_id = ? OR user2_id = ?)
        ''', (current_user['id'], current_user['id']))
    
    conflicts_rows = cursor.fetchall()
    conn.close()
    
    result = []
    for conflict_row in conflicts_rows:
        conflict = dict(conflict_row)
        conflict['resolved'] = bool(conflict['resolved'])
        if isinstance(conflict['created_at'], str):
            conflict['created_at'] = datetime.fromisoformat(conflict['created_at'])
        result.append(ConflictNotification(**conflict))
    
    return result

@api_router.get("/conflicts/user", response_model=List[ConflictNotification])
async def get_user_conflicts(current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM conflicts
        WHERE (user1_id = ? OR user2_id = ?) AND resolved = 0
    ''', (current_user['id'], current_user['id']))
    
    conflicts_rows = cursor.fetchall()
    conn.close()
    
    result = []
    for conflict_row in conflicts_rows:
        conflict = dict(conflict_row)
        conflict['resolved'] = bool(conflict['resolved'])
        if isinstance(conflict['created_at'], str):
            conflict['created_at'] = datetime.fromisoformat(conflict['created_at'])
        result.append(ConflictNotification(**conflict))
    
    return result

@api_router.put("/conflicts/{conflict_id}/resolve")
async def resolve_conflict(conflict_id: str, current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE conflicts SET resolved = 1 WHERE id = ?', (conflict_id,))
    conn.commit()
    
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Conflict not found")
    
    conn.close()
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