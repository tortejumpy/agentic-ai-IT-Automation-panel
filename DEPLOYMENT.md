# Railway Deployment Guide

This guide provides step-by-step instructions to deploy the **Agentic AI IT Support Automation System** to Railway.

---

## 📋 Prerequisites

Before deploying to Railway, ensure you have:

1. **GitHub Account** - Project is already pushed to: `https://github.com/tortejumpy/agentic-ai-IT-Automation-panel`
2. **Railway Account** - Sign up at https://railway.app (free tier available)
3. **Groq API Key** - Get it from https://console.groq.com/keys (free tier available)
4. **Environment Variables** ready:
   - `GROQ_API_KEY`: Your Groq API key
   - `BACKEND_URL`: Your Railway app URL (generated after deployment)

---

## 🚀 Step-by-Step Deployment

### **Step 1: Connect GitHub Repository to Railway**

1. Go to [Railway Dashboard](https://railway.app/dashboard)
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. **Authorize Railway** to access your GitHub account (if not already done)
5. Search for and select the repository: `tortejumpy/agentic-ai-IT-Automation-panel`
6. Click **"Deploy Now"**

Railway will automatically:
- Detect the Python project
- Read `requirements.txt` for dependencies
- Read `Procfile` for the start command
- Read `runtime.txt` for Python version

**Expected Output:**
```
✓ Source connected
✓ Build started
✓ Dependencies installing...
```

---

### **Step 2: Configure Environment Variables**

1. In the Railway dashboard, go to **Variables** tab
2. Add the following environment variables:

| Variable Name | Value | Description |
|---|---|---|
| `GROQ_API_KEY` | `gsk_xxxxxxxxxxxxx...` | Your Groq API key from https://console.groq.com/keys |
| `BACKEND_URL` | `https://your-railway-app.railway.app` | Will be auto-generated, update after first deployment |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | (Optional) Change model if needed |

**Steps:**
1. Click **"Add Variable"**
2. Enter `GROQ_API_KEY` as the name
3. Paste your Groq API key as the value
4. Click **"Add"**
5. Repeat for `BACKEND_URL` (use placeholder initially)

---

### **Step 3: Deploy & Monitor Build**

1. Railway will automatically start building after you add variables
2. Monitor the build in the **Deployments** tab
3. You should see:

```
Building...
Step 1/5: Installing Python 3.11.7
Step 2/5: Installing dependencies from requirements.txt
Step 3/5: Setting up Playwright browsers (if needed)
Step 4/5: Complete
Deploying...
✓ Deployment successful
```

**If build fails:**
- Check logs in the **Logs** tab
- Verify `requirements.txt` has all dependencies
- Ensure `Procfile` syntax is correct

---

### **Step 4: Get Your Deployment URL**

1. Go to the **Settings** tab
2. Copy the **Domain** (format: `your-app-name.railway.app`)
3. Update `BACKEND_URL` variable with the full URL:
   ```
   https://your-app-name.railway.app
   ```

**Your API is now live at:**
```
https://your-app-name.railway.app
https://your-app-name.railway.app/login  ← Admin panel
https://your-app-name.railway.app/docs    ← API documentation (auto-generated)
```

---

### **Step 5: Test the Deployment**

#### **Option A: Test via Browser**
1. Visit: `https://your-app-name.railway.app/login`
2. Login with:
   - **Username**: `admin`
   - **Password**: `admin123`
3. Navigate: 
   - `/dashboard` - Stats & overview
   - `/users` - View all users
   - `/create-user` - Create new user
   - `/reset-password` - Reset user password
   - `/assign-license` - Assign license to user

#### **Option B: Test via API**
```bash
# Get API docs
curl https://your-app-name.railway.app/docs

# Test login (example)
curl -X POST https://your-app-name.railway.app/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

---

## 🤖 Running the AI Agent (Optional - From Local Machine)

The Agentic AI agent **cannot run directly in Railway** (browser automation isn't supported in Railway's containerized environment), but you can run it locally while the backend is deployed in Railway.

### **To run the agent against Railway backend:**

1. **Clone the repo locally:**
   ```bash
   git clone https://github.com/tortejumpy/agentic-ai-IT-Automation-panel.git
   cd agentic-ai-IT-Automation-panel
   ```

2. **Set up local environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: .\venv\Scripts\activate
   pip install -r requirements.txt
   playwright install chromium
   ```

3. **Create `.env` file:**
   ```bash
   cp .env.example .env
   # Edit .env and add:
   # GROQ_API_KEY=your_key_here
   # BACKEND_URL=https://your-railway-app.railway.app
   ```

4. **Run the agent against Railway backend:**
   ```bash
   python run_agent.py "reset password for john@company.com"
   python run_agent.py "create user alice@company.com with name Alice Johnson"
   ```

---

## 📊 Architecture on Railway

```
┌─────────────────────────────────────────┐
│  Railway Container (your-app.railway.app) │
├─────────────────────────────────────────┤
│  FastAPI Backend                         │
│  - /login (POST)                         │
│  - /users (GET)                          │
│  - /create-user (POST)                   │
│  - /reset-password (POST)                │
│  - /assign-license (POST)                │
├─────────────────────────────────────────┤
│  Database: In-memory (SQLite in-memory) │
│  Port: $PORT (Railway auto-assigned)    │
└─────────────────────────────────────────┘
         ↑
         │ REST API calls
         │
    (Local Machine)
    AI Agent (Playwright + Groq LLM)
```

---

## 🔧 Logs & Debugging

### **View Deployment Logs:**

1. Go to Railway **Deployments** tab
2. Click the deployment to view detailed logs
3. Check sections:
   - **Build Logs** - Docker build output
   - **Runtime Logs** - Application output

### **Common Issues & Solutions:**

| Issue | Cause | Solution |
|-------|-------|----------|
| `ModuleNotFoundError: No module named 'fastapi'` | Missing dependencies | Ensure all packages in `requirements.txt` are listed |
| `GROQ_API_KEY not found` | Missing env variable | Add `GROQ_API_KEY` to Variables tab |
| `Connection refused on port 8000` | Procfile syntax error | Verify `Procfile` uses `$PORT` variable |
| `Build timeout (15 min)` | Long dependency installation | Reduce number of dependencies or use binary wheels |
| `Application crashes after deploy` | Python version mismatch | Check `runtime.txt` matches project requirements (3.11+) |

---

## 🔄 Continuous Deployment

Railway **automatically redeploys** when you:
1. Push new code to the connected GitHub branch
2. Update environment variables
3. Manually trigger redeploy via Dashboard

**To disable auto-deploy:**
1. Go to **Settings** → **Autodeploy**
2. Toggle **off**

---

## 💾 Database & State Management

⚠️ **Important:** The current implementation uses **in-memory storage**. This means:

- **Data is lost on every redeploy**
- Data is lost on Railway automatic restarts
- Perfect for testing/demo purposes
- **Not suitable for production**

### **For Production:**
To persist data, integrate:
- **PostgreSQL** - Railway provides database service
- **MongoDB** - NoSQL alternative
- **MySQL** - Another relational option

---

## 📈 Scaling & Performance

### **Railway Tier Recommendations:**

| Use Case | Tier | CPU | Memory | Cost/Month |
|----------|------|-----|--------|-----------|
| Testing/Demo | Free | Shared | 512 MB | $0 (with credits) |
| Light Production | Basic | 1 vCPU | 2 GB | $5-10 |
| Heavy Load | Standard | 2 vCPU | 4 GB | $20+ |

### **Monitor Performance:**
1. **Railway Dashboard** → **Metrics** tab
2. View:
   - CPU usage
   - Memory consumption
   - Network I/O
   - Request count

---

## ✅ Deployment Checklist

- [ ] GitHub repo pushed to `tortejumpy/agentic-ai-IT-Automation-panel`
- [ ] Railway account created
- [ ] Groq API key obtained
- [ ] GitHub connected to Railway
- [ ] `Procfile` in root directory with correct start command
- [ ] `runtime.txt` specifies Python 3.11+
- [ ] `requirements.txt` has all dependencies
- [ ] `.gitignore` excludes `.env`
- [ ] Environment variables added to Railway:
  - [ ] `GROQ_API_KEY`
  - [ ] `BACKEND_URL`
- [ ] Deployment successful (Status: "Running")
- [ ] Login page accessible at `https://your-app.railway.app/login`
- [ ] Can login with `admin/admin123`

---

## 🔐 Security Notes for Production

Before deploying to production:

1. **Change default credentials** - Update `admin/admin123` in `backend/models/database.py`
2. **Use encrypted sessions** - Replace cookie-based sessions with JWT + DB storage
3. **Add HTTPS** - Railway auto-provides HTTPS
4. **Rate limiting** - Add to prevent brute force attacks
5. **Input validation** - Sanitize all form inputs
6. **Database security** - Move to persistent database with encryption
7. **API authentication** - Add API key or OAuth2 protection
8. **Secrets management** - Never hardcode secrets; use environment variables

---

## 📞 Support & Resources

- **Railway Docs**: https://docs.railway.app
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **Groq API Docs**: https://console.groq.com/docs
- **Playwright Docs**: https://playwright.dev/python

---

## 🎉 Next Steps

After successful deployment:

1. **Share the URL** - Send `https://your-app.railway.app` to users
2. **Monitor performance** - Check Railway metrics regularly
3. **Update backend code** - Push changes to GitHub; Railway auto-redeploys
4. **For agent tasks** - Run `run_agent.py` locally with `BACKEND_URL` set to Railway URL
5. **Integrate database** - Add PostgreSQL for production use

---

**Deployment Date**: [Fill with your deployment date]  
**Railway App URL**: `https://your-app-name.railway.app`  
**Status**: Production Ready ✅
