# Pre-Deployment Checklist

## ✅ Code Quality

- [ ] No syntax errors: `python -m py_compile backend/server.py`
- [ ] Backend imports work: `python -c "from server import app; print('OK')"`
- [ ] Database initializes: `python -c "from server import init_db; init_db()"`
- [ ] Frontend builds: `cd frontend && npm run build`
- [ ] No TypeScript errors
- [ ] No console errors in browser
- [ ] All routes tested locally

## ✅ Security

- [ ] `.env` files are in `.gitignore`
- [ ] JWT_SECRET_KEY is NOT in code (only in .env)
- [ ] Database passwords (if any) in .env
- [ ] CORS_ORIGINS configured properly
- [ ] No hardcoded API URLs (using environment variables)
- [ ] Authentication tests pass
- [ ] Authorization tests pass (admin checks work)

## ✅ Environment Configuration

### Backend
- [ ] Create `.env` with:
  - `DATABASE_URL=sqlite:///notcluely.db`
  - `JWT_SECRET_KEY=<secure-random-key-32+chars>`
  - `CORS_ORIGINS=https://yourdomain.vercel.app,https://yourdomain.com`
- [ ] `.env` is NOT committed to git

### Frontend
- [ ] Create `.env.production` with:
  - `REACT_APP_BACKEND_URL=https://yourdomain-api.onrender.com`
- [ ] `.env.local` is NOT committed to git

## ✅ Dependencies

- [ ] `backend/requirements.txt` is up to date
- [ ] All packages in requirements.txt are installed locally
- [ ] `npm install` completes without errors
- [ ] No deprecation warnings

## ✅ Database

- [ ] SQLite database initializes automatically
- [ ] All tables created (users, bookings, conflicts)
- [ ] Can insert test data
- [ ] Foreign keys work
- [ ] Timestamps are ISO format

## ✅ Testing

### Authentication
- [ ] Register new user works
- [ ] Login with correct credentials works
- [ ] Login with wrong password fails
- [ ] Username "rutvik" becomes admin
- [ ] Logout clears token
- [ ] Session persists on refresh
- [ ] Expired token triggers re-login

### Bookings
- [ ] Create booking works
- [ ] Get bookings returns filtered list (user sees only own)
- [ ] Admin sees all bookings
- [ ] Delete own booking works for user
- [ ] User cannot delete others' bookings
- [ ] Admin can delete any booking
- [ ] Conflict detection works

### API
- [ ] All endpoints respond with correct status codes
- [ ] Error messages are user-friendly
- [ ] CORS headers present
- [ ] JWT validation works

## ✅ Documentation

- [ ] README.md is complete and accurate
- [ ] DEPLOYMENT_GUIDE.md has step-by-step instructions
- [ ] QUICK_REFERENCE.md is helpful
- [ ] Comments in code explain complex logic
- [ ] API endpoints documented

## ✅ Git

- [ ] Repository initialized: `git init`
- [ ] Remote added: `git remote add origin <url>`
- [ ] All files committed: `git add . && git commit -m "..."`
- [ ] Branch pushed: `git push origin main`
- [ ] `.env` files NOT committed

## ✅ Deployment Preparation

### Render.com (Backend)
- [ ] Render account created
- [ ] GitHub connected to Render
- [ ] Environment variables set on Render dashboard
- [ ] Build command configured
- [ ] Start command configured
- [ ] Database path correct
- [ ] Test endpoint returns 200 OK

### Vercel (Frontend)
- [ ] Vercel account created
- [ ] GitHub repo connected
- [ ] Environment variables set
- [ ] Build settings configured
- [ ] Output directory set to `frontend/build`
- [ ] Root directory set to `frontend/`

## ✅ Production Verification

After deployment, verify:
- [ ] Backend API is accessible: `https://api-url/api/`
- [ ] Frontend loads: `https://frontend-url`
- [ ] Registration works on production
- [ ] Login works on production
- [ ] Bookings can be created
- [ ] Admin user "rutvik" is admin on production
- [ ] No CORS errors in browser console
- [ ] No 404 errors for static assets
- [ ] HTTPS certificate is valid
- [ ] Database is persisting data (not creating new on each load)

## 📋 Final Steps

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Production ready: SQLite + free deployment"
   git push origin main
   ```

2. **Deploy Backend**
   - Render.com: New Web Service → Select repo → Configure
   - Railway.app: New Project → Connect GitHub → Deploy

3. **Deploy Frontend**
   - Vercel: Import repo → Configure → Deploy
   - Netlify: Connect GitHub → Configure → Deploy

4. **Update Environment Variables**
   - Backend: Set on Render/Railway dashboard
   - Frontend: Set on Vercel/Netlify dashboard
   - CORS_ORIGINS: Include deployed frontend URL
   - REACT_APP_BACKEND_URL: Use deployed backend URL

5. **Test Production**
   - Register new account
   - Login
   - Create booking
   - Verify database persistence
   - Check admin user works

6. **Share**
   - Your app URL: https://yourdomain.vercel.app
   - You're live! 🎉

## 🐛 If Something Fails

### Backend won't start
- Check logs on deployment platform
- Verify database.url format
- Check JWT_SECRET_KEY is set
- Ensure port defaults to 8000

### Frontend won't load
- Check REACT_APP_BACKEND_URL in environment
- Verify backend is running and accessible
- Check browser console for CORS errors
- Clear browser cache

### Database errors
- Delete local `notcluely.db` and redeploy (fresh database)
- Check SQLite path in DATABASE_URL
- Verify file permissions

### 401 Unauthorized
- Check JWT_SECRET_KEY matches on backend
- Verify token is sent in Authorization header
- Check token hasn't expired (7 days)

---

**Ready to Deploy!** ✨

Check off each item above, then push to GitHub and deploy.

Your app will be live in < 10 minutes!

**Cost: $0/month** 🎉
