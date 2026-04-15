# 🔧 Railway Deployment Troubleshooting

## ❌ "Application failed to respond" Error

This error appears when the app **deploys successfully but fails to start up**. Here's how to fix it:

---

## 🔍 **Step 1: Check Railway Logs**

1. Go to **Railway Dashboard** → Your project
2. Click the **"web"** service (left sidebar)
3. Click the **Logs** tab (top right)
4. Scroll through logs to find the error

**Look for:**
- ❌ Python import errors
- ❌ Missing dependencies  
- ❌ `GROQ_API_KEY` not found
- ❌ Port binding issues
- ✅ `INFO: Uvicorn running on 0.0.0.0:8000` (success message)

---

## ⚠️ **Step 2: Set Required Environment Variables**

**CRITICAL:** If you see this in logs:
```
KeyError: 'GROQ_API_KEY'
```

Or the app just silently crashes → the API key is missing.

### Fix:

1. Go to **Railway Dashboard** → Your project → **Variables** tab
2. Click **+ New Variable**
3. Add:

| Key | Value | Required |
|-----|-------|----------|
| `GROQ_API_KEY` | Your key from https://console.groq.com/keys | YES ✅ |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | No (default) |

4. Click **Save**
5. **Wait 5 seconds** for environment to update

### Step 3: Force App Restart

1. Go to **Deployments** tab
2. Click the latest deployment
3. Click **Redeploy** button
4. Wait 30-60 seconds for startup

---

## Common Issues & Fixes

### Issue: Still says "Application failed to respond"

**Check logs again:**

#### If you see: `KeyError: GROQ_API_KEY`
- ✅ Solution: **Add `GROQ_API_KEY` environment variable** (see Step 2 above)
- Then redeploy

#### If you see: `ImportError: No module named 'playwright'`
- ✅ Solution: Click **Redeploy** (Docker should install it)
- If it persists, check Docker build logs

#### If you see: `Address already in use: ('0.0.0.0', 8000)`
- ✅ Solution: Railway issue - click **Redeploy** again

#### If you see: `Connection timeout` or `500 error`
- ✅ Solution: Check if GROQ_API_KEY is set
- The app may be failing silently

#### If you see: No errors, but health check failing
- ✅ Check if you can access `/` (root) instead of `/dashboard`
- The health check tries `/` which doesn't require auth

---

## ✅ After Redeploy - Verify App is Running

Once you see `Uvicorn running` in logs:

1. **Wait 10 seconds** (startup takes time)
2. Visit: `https://your-domain.railway.app/`
   - Should show **login page** (not error)
3. Login with: `admin` / `admin123`
4. Go to `/automation` to test automation console

---

## 🎯 Full Checklist for Success

- [ ] Deployment shows "Success" (green checkmark) in Railway
- [ ] `GROQ_API_KEY` variable is set in Railway Variables
- [ ] Clicked **Redeploy** after setting variables
- [ ] Logs show `Uvicorn running on 0.0.0.0:8000`
- [ ] Can access `https://your-domain.railway.app/` 
- [ ] Login works: `admin` / `admin123`
- [ ] Can see `/automation` page
- [ ] Automation task submission works

---

## 💾 Checking Logs Step-by-Step

1. **Click "web" service** in left sidebar
2. **Click "Logs" tab** at top
3. **Scroll to bottom** to see latest messages
4. Look for red error messages or startup confirmation

### Success Log Example:
```
INFO:     Started server process
INFO:     Uvicorn running on 0.0.0.0:8000
INFO:     Application startup complete
```

### Error Log Example:
```
KeyError: 'GROQ_API_KEY'
   File "backend/routes/automation.py", line 35
```
→ **Fix: Add GROQ_API_KEY to Variables**

---

## 🆘 Still Not Working?

If after all steps it still fails:

1. **Save these logs:**
   - Copy full logs to notepad
   - Include first error message + last 10 lines

2. **Check Railway docs:** 
   - https://docs.railway.app/troubleshooting
   - https://docs.railway.app/deployment/fixing-common-errors

3. **Contact Railway Support:**
   - Help Station: https://help.railway.app

---

## 🚨 Quick Restart Procedure

If the app was working but stopped:

1. Go to **Deployments** tab
2. Find the **latest deployment** (top of list)
3. Click **Redeploy**
4. Wait 2 minutes
5. Test: `https://your-domain.railway.app/`

---

## 📊 Expected Behavior After Fix

### First Visit
```
Navigate to: https://your-domain.railway.app/
Result: Login page appears
```

### After Login
```
Username: admin
Password: admin123
Result: Dashboard with stats and user list
```

### Automation Console
```
Navigate to: https://your-domain.railway.app/automation
Click: "Create User" template
Click: "Execute"
Result: Real-time logs stream (3-5 minutes)
```

---

## 🔧 If App Keeps Crashing (Advanced)

Check if the issue is with an import:

```python
# In backend/routes/automation.py around line 1-30:
# Make sure these don't throw errors:
- from agent.agent import ITSupportAgent  ← requires agent to exist
- load_dotenv()                            ← requires python-dotenv
- asyncio module load (Windows fix)        ← already handled
```

If you see import errors in logs → the Dockerfile needs to rebuild (click Redeploy)

