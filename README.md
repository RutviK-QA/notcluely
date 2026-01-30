# NotCluely - Shared Calendar Scheduler

A modern, full-stack calendar/booking scheduler with real-time conflict detection and role-based access control.

## 🎯 Features

✅ **User Authentication**
- Secure registration & login with bcrypt hashing
- JWT-based session management (7-day expiration)
- Admin role detection (username "rutvik" = admin)

✅ **Booking Management**
- Create, view, and delete bookings
- Timezone support for each user
- Real-time conflict detection across all users

✅ **Admin Dashboard** (for admins only)
- View all bookings across all users
- Delete any booking
- Manage conflicts

✅ **Conflict Resolution**
- Automatic detection of booking overlaps
- Notification system for conflicting bookings
- Mark conflicts as resolved

✅ **Free Deployment**
- SQLite database (no external DB needed)
- Runs on Render.com, Railway, or any Python-capable host
- Vercel or Netlify for frontend

## 🛠️ Tech Stack

**Frontend:**
- React 19 with React Router
- TailwindCSS + Shadcn UI
- Luxon for timezone handling

**Backend:**
- FastAPI (async Python framework)
- SQLite (embedded database)
- JWT + Passlib for authentication

## 🚀 Quick Start (Local)

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
uvicorn server:app --reload --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install
npm start
```

## 🌍 Deployment (FREE)

**See [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) for detailed steps.**

Recommended:
- Backend: Render.com or Railway.app
- Frontend: Vercel or Netlify
- Database: SQLite (embedded)

**Cost: $0/month** ✨

## 🔐 Authentication

- Register with username `rutvik` → Auto-admin
- Passwords hashed with bcrypt
- JWT tokens (7-day expiration)
- Server-side authorization checks

## 📊 Key Features

- User registration & login
- Booking creation with timezone support
- Real-time conflict detection
- Admin can view/delete all bookings
- Users see only their own bookings
- Conflict resolution tracking

## 🛡️ Security

✅ Passwords hashed with bcrypt
✅ JWT authentication
✅ Server-side role checks
✅ CORS protection
✅ Input validation

## 📖 API Docs

- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login
- `GET /api/auth/me` - Get current user
- `GET /api/bookings` - Get bookings (filtered by role)
- `POST /api/bookings` - Create booking
- `DELETE /api/bookings/{id}` - Delete booking
- `GET /api/conflicts` - Get conflicts
- `GET /api/users` - Get all users
- `GET /api/timezones` - Get timezones

## 🐛 Troubleshooting

See [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) for detailed troubleshooting.

---

**Made for collaborative scheduling** ❤️
