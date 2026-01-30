from fastapi import FastAPI, APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import pytz
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

# Models
class UserCreate(BaseModel):
    name: str
    fingerprint: str
    timezone: str

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    fingerprint: str
    timezone: str
    is_admin: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

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

# User routes
@api_router.post("/users/register", response_model=User)
async def register_user(user_data: UserCreate):
    # Check if fingerprint already exists
    existing = await db.users.find_one({"fingerprint": user_data.fingerprint}, {"_id": 0})
    if existing:
        # Convert ISO string timestamps back to datetime
        if isinstance(existing['created_at'], str):
            existing['created_at'] = datetime.fromisoformat(existing['created_at'])
        return User(**existing)
    
    # Check if user should be admin (name is "rutvik", case-insensitive)
    is_admin = user_data.name.lower().strip() == "rutvik"
    
    user = User(
        name=user_data.name,
        fingerprint=user_data.fingerprint,
        timezone=user_data.timezone,
        is_admin=is_admin
    )
    
    doc = user.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.users.insert_one(doc)
    return user

@api_router.get("/users/by-fingerprint/{fingerprint}", response_model=User)
async def get_user_by_fingerprint(fingerprint: str):
    user = await db.users.find_one({"fingerprint": fingerprint}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if isinstance(user['created_at'], str):
        user['created_at'] = datetime.fromisoformat(user['created_at'])
    
    return User(**user)

@api_router.put("/users/{user_id}/timezone")
async def update_user_timezone(user_id: str, timezone: str):
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": {"timezone": timezone}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"success": True}

@api_router.get("/users", response_model=List[User])
async def get_all_users():
    users = await db.users.find({}, {"_id": 0}).to_list(1000)
    
    for user in users:
        if isinstance(user['created_at'], str):
            user['created_at'] = datetime.fromisoformat(user['created_at'])
    
    return users

# Booking routes
@api_router.post("/bookings", response_model=Booking)
async def create_booking(booking_data: BookingCreate, user_id: str):
    # Get user info
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
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
        user_id=user_id,
        user_name=user['name'],
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
            user2_id=user_id,
            user1_name=conflict['user_name'],
            user2_name=user['name'],
            conflict_start=max(booking_data.start_time, conflict['start_time']),
            conflict_end=min(booking_data.end_time, conflict['end_time'])
        )
        
        conflict_doc = conflict_notif.model_dump()
        conflict_doc['created_at'] = conflict_doc['created_at'].isoformat()
        
        await db.conflicts.insert_one(conflict_doc)
    
    # Broadcast to all connected clients
    await manager.broadcast({
        "type": "booking_created",
        "booking": doc,
        "has_conflicts": len(conflicts) > 0
    })
    
    return booking

@api_router.get("/bookings", response_model=List[Booking])
async def get_bookings():
    bookings = await db.bookings.find({}, {"_id": 0}).to_list(1000)
    
    for booking in bookings:
        if isinstance(booking['created_at'], str):
            booking['created_at'] = datetime.fromisoformat(booking['created_at'])
    
    return bookings

@api_router.delete("/bookings/{booking_id}")
async def delete_booking(booking_id: str, user_id: str):
    # Get user to check if admin
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get booking
    booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Check if user owns the booking or is admin
    if booking['user_id'] != user_id and not user.get('is_admin', False):
        raise HTTPException(status_code=403, detail="Not authorized to delete this booking")
    
    result = await db.bookings.delete_one({"id": booking_id})
    
    # Delete related conflicts
    await db.conflicts.delete_many({
        "$or": [
            {"booking1_id": booking_id},
            {"booking2_id": booking_id}
        ]
    })
    
    # Broadcast deletion
    await manager.broadcast({
        "type": "booking_deleted",
        "booking_id": booking_id
    })
    
    return {"success": True}

# Conflict routes
@api_router.get("/conflicts", response_model=List[ConflictNotification])
async def get_conflicts():
    conflicts = await db.conflicts.find({"resolved": False}, {"_id": 0}).to_list(1000)
    
    for conflict in conflicts:
        if isinstance(conflict['created_at'], str):
            conflict['created_at'] = datetime.fromisoformat(conflict['created_at'])
    
    return conflicts

@api_router.get("/conflicts/user/{user_id}", response_model=List[ConflictNotification])
async def get_user_conflicts(user_id: str):
    conflicts = await db.conflicts.find({
        "$or": [
            {"user1_id": user_id},
            {"user2_id": user_id}
        ],
        "resolved": False
    }, {"_id": 0}).to_list(1000)
    
    for conflict in conflicts:
        if isinstance(conflict['created_at'], str):
            conflict['created_at'] = datetime.fromisoformat(conflict['created_at'])
    
    return conflicts

@api_router.put("/conflicts/{conflict_id}/resolve")
async def resolve_conflict(conflict_id: str):
    result = await db.conflicts.update_one(
        {"id": conflict_id},
        {"$set": {"resolved": True}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Conflict not found")
    
    # Broadcast conflict resolution
    await manager.broadcast({
        "type": "conflict_resolved",
        "conflict_id": conflict_id
    })
    
    return {"success": True}

# Timezone utility endpoint
@api_router.get("/timezones")
async def get_timezones():
    return {"timezones": pytz.all_timezones}

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

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