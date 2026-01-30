# Deployment Guide - NotCluely Scheduler

## Overview

NotCluely is now **completely free to deploy** using:
- **Frontend**: Vercel or Netlify (free tier)
- **Backend**: Render or Railway (free tier)
- **Database**: SQLite (embedded, no external DB needed)

## Architecture

```
Frontend (React) → Vercel/Netlify
  ↓
Backend (FastAPI) → Render/Railway
  ↓
SQLite Database (embedded in backend)
```

---

## DEPLOYMENT STEPS

### Option 1: Render.com + Vercel (Recommended)

#### Backend Deployment (Render.com)

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Switch to SQLite for free deployment"
   git push origin main
   ```

2. **Create Render Account**
   - Go to https://render.com
   - Sign up with GitHub

3. **Deploy Backend**
   - Click "New +" → "Web Service"
   - Select your GitHub repo
   - Configure:
     - **Name**: `notcluely-api`
     - **Environment**: Python 3
     - **Build Command**: `pip install -r backend/requirements.txt`
     - **Start Command**: `cd backend && uvicorn server:app --host 0.0.0.0 --port 8000`
     - **Auto-deploy**: Yes
   - Click "Create Web Service"

4. **Set Environment Variables**
   - After service is created, go to "Environment"
   - Add:
     ```
     JWT_SECRET_KEY=<generate-random-secret>
     CORS_ORIGINS=https://yourdomain.vercel.app,https://yourdomain.com
     DATABASE_URL=sqlite:///notcluely.db
     ```

5. **Get Backend URL**
   - Backend will be deployed at: `https://notcluely-api.onrender.com`
   - Save this URL for frontend setup

#### Frontend Deployment (Vercel)

1. **Create `frontend/.env.production`**
   ```
   REACT_APP_BACKEND_URL=https://notcluely-api.onrender.com
   ```

2. **Deploy to Vercel**
   - Go to https://vercel.com
   - Click "Add New..." → "Project"
   - Import your GitHub repo
   - Configure:
     - **Framework**: Create React App
     - **Root Directory**: `frontend`
     - **Build Command**: `npm run build`
     - **Output Directory**: `build`
   - Add Environment Variable:
     ```
     REACT_APP_BACKEND_URL=https://notcluely-api.onrender.com
     ```
   - Click "Deploy"

3. **Live URL**
   - Frontend: `https://notcluely-<random>.vercel.app`
   - Backend: `https://notcluely-api.onrender.com`

---

### Option 2: Railway.app + Netlify

#### Backend Deployment (Railway.app)

1. **Create Railway Account**
   - Go to https://railway.app
   - Sign up with GitHub

2. **Deploy Backend**
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Click "Add Variables"
   - Set:
     ```
     JWT_SECRET_KEY=<generate-random-secret>
     CORS_ORIGINS=https://yourdomain.netlify.app,https://yourdomain.com
     DATABASE_URL=sqlite:///notcluely.db
     ```

3. **Configure Start Command**
   - In Project Settings → Start Command:
     ```
     cd backend && uvicorn server:app --host 0.0.0.0 --port $PORT
     ```

4. **Get Public URL**
   - Railway will assign a domain like: `https://notcluely-prod.up.railway.app`
   - Save this URL

#### Frontend Deployment (Netlify)

1. **Create `frontend/.env.production`**
   ```
   REACT_APP_BACKEND_URL=https://notcluely-prod.up.railway.app
   ```

2. **Deploy to Netlify**
   - Connect GitHub repo
   - Configure Build:
     - **Build command**: `cd frontend && npm run build`
     - **Publish directory**: `frontend/build`
   - Set Environment Variable:
     ```
     REACT_APP_BACKEND_URL=https://notcluely-prod.up.railway.app
     ```
   - Deploy

3. **Live URL**
   - Frontend: `https://notcluely.netlify.app`
   - Backend: `https://notcluely-prod.up.railway.app`

---

## LOCAL TESTING (BEFORE DEPLOYMENT)

### Setup

1. **Install Dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   cd ../frontend
   npm install
   ```

2. **Create Backend .env**
   ```
   DATABASE_URL=sqlite:///notcluely.db
   JWT_SECRET_KEY=your-dev-secret-key
   CORS_ORIGINS=http://localhost:3000,http://localhost:5000
   ```

3. **Create Frontend .env.local**
   ```
   REACT_APP_BACKEND_URL=http://localhost:8000
   ```

### Run Locally

**Terminal 1 - Backend:**
```bash
cd backend
uvicorn server:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
```

- Backend API: http://localhost:8000/api
- Frontend: http://localhost:3000

---

## DATABASE

- **Type**: SQLite (no external service needed)
- **Location**: `backend/notcluely.db` (created automatically)
- **Persistence**: On Render/Railway, persists across deployments
- **Backup**: Commit `notcluely.db` to git if needed, or configure backups in Render/Railway

---

## AUTHENTICATION & SECURITY

### Admin User
- **Username**: `rutvik` (case-insensitive)
- Auto-assigned on registration/login
- Can view/delete all bookings

### Security Features
✅ Passwords hashed with bcrypt
✅ JWT tokens with 7-day expiration
✅ Server-side authorization (admin checks)
✅ CORS configured per environment
✅ Secure session management

### First Login
1. Register with username `rutvik` and any password
2. You'll be marked as admin
3. Log in to access admin dashboard

---

## TROUBLESHOOTING

### Backend Won't Start
- Check `requirements.txt` is installed correctly
- Verify `DATABASE_URL` and `JWT_SECRET_KEY` are set
- Check logs for SQLite connection errors

### CORS Errors
- Update `CORS_ORIGINS` to include your frontend domain
- Format: `https://domain.vercel.app,https://domain.com`

### Database Locked
- SQLite uses file locks; shouldn't occur on free tier
- If frozen, delete `notcluely.db` and redeploy

### Frontend Can't Connect to Backend
- Verify `REACT_APP_BACKEND_URL` matches deployed backend
- Check backend is running and accessible
- Look for CORS errors in browser console

---

## PRICING SUMMARY

| Service | Free Tier | Notes |
|---------|-----------|-------|
| **Render.com** | ✅ Free | 0.5 GB RAM, auto-sleep after 15 min inactivity |
| **Vercel** | ✅ Free | Unlimited deployments, excellent for React |
| **Netlify** | ✅ Free | Similar to Vercel, easy GitHub integration |
| **Railway.app** | ✅ Free | $5/month free credit, then pay-as-you-go |
| **SQLite** | ✅ Free | Embedded, no external DB cost |

**Total Cost: $0/month** ✨

---

## ADVANCED: Custom Domain

Once deployed, you can add a custom domain:

1. **Purchase domain** (Namecheap, GoDaddy, etc.)
2. **Vercel**: Settings → Domains → Add custom domain
3. **Render**: Settings → Custom Domain
4. **Update CORS_ORIGINS** with new domain

---

## NEXT STEPS

1. Test locally first (see Local Testing section)
2. Choose deployment platform (Render + Vercel recommended)
3. Follow exact steps for your chosen platform
4. Test production deployment
5. Share live URL!

**Your App Will Be Live in < 10 minutes!** 🚀
