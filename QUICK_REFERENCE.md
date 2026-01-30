# NotCluely - Quick Reference

## 🚀 Start Development

```bash
# Terminal 1 - Backend
cd backend
pip install -r requirements.txt
uvicorn server:app --reload --port 8000

# Terminal 2 - Frontend  
cd frontend
npm install
npm start
```

Visit: http://localhost:3000

---

## 🔐 Test Users

**Regular User:**
- Username: `testuser`
- Password: `Test@123456789`

**Admin User:**
- Username: `rutvik`
- Password: `Admin@123456789`

---

## 📝 API Examples

### Register
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john",
    "password": "SecurePass123",
    "timezone": "America/New_York"
  }'
```

### Login
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john",
    "password": "SecurePass123"
  }'
```

### Get Current User
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/auth/me
```

### Create Booking
```bash
curl -X POST http://localhost:8000/api/bookings \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Team Meeting",
    "start_time": "2026-02-01T14:00:00Z",
    "end_time": "2026-02-01T15:00:00Z",
    "notes": "Discuss Q1 goals",
    "user_timezone": "America/New_York"
  }'
```

### Get Bookings
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/bookings
```

### Delete Booking
```bash
curl -X DELETE http://localhost:8000/api/bookings/BOOKING_ID \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🗂️ Project Structure

```
backend/
├── server.py           # Main FastAPI app
├── requirements.txt    # Dependencies
├── .env                # Config (gitignored)
├── Procfile            # Deploy config
├── notcluely.db        # SQLite database
└── test_auth.py        # Quick tests

frontend/
├── src/
│   ├── pages/          # Login, Register, Calendar
│   ├── components/     # UI components
│   └── App.js          # Router
├── package.json
└── .env.local          # Config (gitignored)
```

---

## 🛠️ Environment Variables

### Backend `.env`
```
DATABASE_URL=sqlite:///notcluely.db
JWT_SECRET_KEY=your-secret-key-min-32-chars
CORS_ORIGINS=http://localhost:3000,http://localhost:5000
```

### Frontend `.env.local`
```
REACT_APP_BACKEND_URL=http://localhost:8000
```

---

## 🌍 Deployment Commands

```bash
# 1. Test local build
npm run build              # Frontend
pip install -r requirements.txt  # Backend

# 2. Push to GitHub
git add .
git commit -m "Deploy changes"
git push origin main

# 3. Deploy Backend (Render.com)
# - New Web Service
# - Build: pip install -r backend/requirements.txt
# - Start: cd backend && uvicorn server:app --host 0.0.0.0 --port 8000

# 4. Deploy Frontend (Vercel)
# - Import repo
# - Root: frontend
# - Build: npm run build
# - Output: build
```

See `DEPLOYMENT_GUIDE.md` for full details.

---

## 🔐 Security Notes

- ✅ Passwords hashed with bcrypt
- ✅ JWT tokens expire in 7 days
- ✅ Admin checks on every request
- ✅ CORS protects against unauthorized domain access
- ✅ SQLite safe from injection (parameterized queries)

**DO NOT:**
- ❌ Commit `.env` files
- ❌ Hardcode secrets in code
- ❌ Use weak JWT secrets (min 32 characters)
- ❌ Log sensitive data

---

## 🐛 Common Issues

### "Module not found"
```bash
cd backend
pip install -r requirements.txt
```

### CORS Error in Browser
Check `CORS_ORIGINS` in `.env` includes your frontend URL.

### Database Locked
SQLite shouldn't lock on free tier. Delete `notcluely.db` and restart.

### Token Invalid
- Check localStorage has `auth_token`
- Token might be expired (7 days)
- Try logging in again

---

## 📊 Database Commands

```bash
# Connect to SQLite
sqlite3 backend/notcluely.db

# List tables
.tables

# View users
SELECT id, username, is_admin, created_at FROM users;

# View bookings
SELECT id, user_name, title, start_time FROM bookings;

# Delete database (fresh start)
rm backend/notcluely.db
# Database auto-recreates on next run
```

---

## 🧪 Test Checklist

- [ ] Register new user
- [ ] Login with credentials
- [ ] View own bookings
- [ ] Create new booking
- [ ] See conflict if booking overlaps
- [ ] Logout (token removed)
- [ ] Login fails with wrong password
- [ ] Register with `rutvik` username (becomes admin)
- [ ] Admin sees all users' bookings
- [ ] Admin can delete other users' bookings
- [ ] Regular user cannot delete others' bookings

---

## 📞 Need Help?

1. **Local issues**: Check `DEPLOYMENT_GUIDE.md` troubleshooting
2. **API questions**: See endpoint docs in README.md
3. **Deployment help**: Follow step-by-step in DEPLOYMENT_GUIDE.md
4. **Code issues**: Check server.py for comments

---

## 🎉 You're Ready!

Everything is configured and tested. 

**Next: Deploy to Render + Vercel** (see DEPLOYMENT_GUIDE.md)

Your free calendar app will be live in < 10 minutes! 🚀

---

Last Updated: Jan 31, 2026
Status: ✅ Production Ready
