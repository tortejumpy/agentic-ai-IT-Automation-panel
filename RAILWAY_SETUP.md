# 🚀 Railway Deployment Guide

## ✅ Prerequisites

- GitHub account with the repo pushed
- Railway account (free tier: https://railway.app)

---

## 📋 Step 1: Connect Repository to Railway

1. Go to [Railway Dashboard](https://railway.app/dashboard)
2. Create a new **Empty Project**
3. Click **+ New** → **GitHub Repo**
4. Select your `tortejumpy/agentic-ai-IT-Automation-panel` repository
5. Click **Deploy** (it auto-detects the Dockerfile)

**Expected:** Railway builds the Docker image and deploys. ⏳ Takes 3-5 minutes.

---

## 🔑 Step 2: Set Environment Variables

**CRITICAL:** The app needs `GROQ_API_KEY` to function.

### In Railway Dashboard:

1. Click your **project** → **Variables** tab
2. Add these environment variables:

| Variable | Value | Required? |
|----------|-------|-----------|
| `GROQ_API_KEY` | Your Groq API key from https://console.groq.com/keys | **YES** ✅ |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Optional (default) |
| `PORT` | `8000` | Auto-set by Railway |

3. Click **Save** after each addition

⚠️ **If GROQ_API_KEY is missing, the app will crash on startup.**

---

## ✨ Step 3: Trigger a Fresh Deploy

Once environment variables are set, force a redeploy:

1. Go to **Deployments** tab
2. Click the latest deployment
3. Click **Redeploy**
4. Wait for the build + deployment to complete ✅

---

## 🧪 Step 4: Test the Deployment

Once the green **Success** checkmark appears:

### Test 1: Check if app is running
```
Navigate to: https://your-railway-domain.railway.app/dashboard
Expected: Login page with "admin / admin123" form
```

### Test 2: Login
```
Username: admin
Password: admin123
Expected: Dashboard showing user stats
```

### Test 3: Run automation
```
1. Go to: https://your-railway-domain.railway.app/automation
2. Click "Create User" template
3. Click "Execute"
4. Expected: Real-time log streaming (no "Executable doesn't exist" error)
```

---

## 🐛 Troubleshooting

### ❌ "Application failed to respond"

**Cause:** Usually means the app crashed during startup.

**Fix:**
1. Check Railway **Logs** tab
2. Look for errors (commonly missing `GROQ_API_KEY`)
3. Set the environment variable and redeploy

### ❌ "Executable doesn't exist at .../headless_shell"

**Cause:** Docker build didn't complete Playwright installation.

**Fix:**
1. In Railway, click **Redeploy** on the latest deployment
2. Watch the logs - should see:
   ```
   RUN playwright install --with-deps chromium
   Downloading Chromium...
   ```

### ❌ Task fails "Playwright crashed"

**Cause:** Container memory too low for Playwright + LLM.

**Fix in Railway:**
1. Go to **Settings** → **Scale** tab
2. Set **Memory** to at least **512 MB** (or 1 GB for stability)
3. Click **Save** and redeploy

### ✅ All tests pass but tasks still fail

Check the **Logs** tab in Railway for the actual error message. Common issues:
- Playwright taking too long (increase timeout in `agent/tools.py`)
- Network connectivity (Railway → Groq API)
- Admin panel page selectors changed

---

## 📊 Viewing Logs in Railway

To debug deployment issues:

1. Click your **project** in Railway Dashboard
2. Select the **Logs** tab
3. Real-time logs show as tasks execute
4. Errors appear in RED

### Key Log Patterns:

- ✅ `INFO: Uvicorn running on 0.0.0.0:8000` — App started successfully
- ⚠️ `Skipping data after last boundary` — Minor multipart parsing issue (harmless)
- ❌ `BrowserType.launch: Executable doesn't exist` — Playwright not installed
- ❌ `GROQ_API_KEY not found` — Missing environment variable

---

## 🔄 Redeploying After Code Changes

After pushing new code to GitHub:

1. Railway automatically detects the push
2. Builds Dockerfile
3. Deploys automatically ✅

**No manual action needed!**

---

## 📁 What's in the Docker Build?

The Dockerfile does this on each build:

```
1. Base image: python:3.11-slim
2. Install system libraries (Chromium dependencies)
3. Install Python packages (requirements.txt)
4. RUN playwright install --with-deps chromium ← KEY STEP
5. Copy your code
6. Expose port 8000
7. Start: uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

---

## 🆘 Getting Help

- Railway Docs: https://docs.railway.app
- Railway Help Station: https://help.railway.app
- Playwright Docker Docs: https://playwright.dev/python/docs/docker

---

## ✅ Success Checklist

- [ ] Repository pushed to GitHub
- [ ] Railway project created + connected to repo
- [ ] `GROQ_API_KEY` environment variable set in Railway
- [ ] Fresh deployment completed (green checkmark)
- [ ] App is responding at `https://your-domain.railway.app/dashboard`
- [ ] Automation console works at `/automation`
- [ ] Sample task execution completes successfully

Once all checked, you're live! 🎉
