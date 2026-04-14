# 🤖 Automation Console — Real-Time Task Execution UI

A production-ready web interface for submitting IT automation tasks and watching execution in real-time.

---

## ✨ What's New

The automation console allows users to:

1. **Submit Tasks via Web UI** - No terminal/CLI needed
2. **Select from Templates** - 4 pre-built common tasks
3. **Watch Live Execution** - See each step as it happens
4. **Track Jobs** - View history and status of all executed tasks
5. **Download Logs** - Export execution logs for documentation

---

## 🚀 Quick Start (Local Testing)

### **Step 1: Start the Backend**

```bash
# Terminal 1 — Start FastAPI backend
cd d:\Projects\agentic-ai
.\venv\Scripts\activate
uvicorn backend.main:app --reload
```

You should see:
```
✨ Mock IT Admin Panel is running!
URL: http://localhost:8000
Login: admin / admin123
Routes: /login, /dashboard, /users, /create-user
        /reset-password, /assign-license, /automation
🤖 NEW: /automation — Real-time task automation console
```

### **Step 2: Open in Browser**

1. Visit: `http://localhost:8000/login`
2. Login with:
   - **Username**: `admin`
   - **Password**: `admin123`
3. Click **"🤖 Automation"** nav button (top right, purple button)

---

## 🎮 How to Use the Console

### **Option A: Use Template**

1. Click one of the 4 template buttons:
   - 🔐 **Reset Password** - Reset admin's own password
   - 👤 **Create User** - Create a new user account
   - 👤 + 📦 **Create & License** - Create user AND assign pro license
   - 📦 **Assign License** - Assign license to existing user

2. Button fills the task field with a template
3. Click **"▶ Execute Task"** button

### **Option B: Custom Task**

1. Type your own automation task in the text area:
   ```
   reset password for alice@company.com
   create user bob@company.com with name Bob Smith
   assign enterprise license to charlie@company.com
   ```

2. Click **"▶ Execute Task"**

---

## 📊 Understanding the Console UI

```
┌─────────────────────────────────────────────────────┐
│   🤖 Automation Console                             │
├──────────────────┬──────────────────────────────────┤
│  LEFT PANEL:     │  RIGHT PANEL:                   │
│                  │                                  │
│  📋 Templates    │  📊 Execution Logs              │
│  - Reset Pwd     │  ┌──────────────────┐          │
│  - Create User   │  │ [00:12:34] PLAN  │          │
│  - Create+Lic    │  │ [00:12:35] OPEN  │          │
│  - Assign Lic    │  │ [00:12:36] TYPE  │          │
│                  │  │ [00:12:37] CLICK │          │
│  Custom Task     │  │ ...              │          │
│  ┌────────────┐  │  └──────────────────┘          │
│  │ Type here  │  │                                │
│  └────────────┘  │  📜 Job History                │
│                  │  ┌──────────────────┐          │
│  ▶ Execute Task  │  │ ✅ Task 1        │          │
│                  │  │ 🔄 Task 2        │          │
│  Status:         │  └──────────────────┘          │
│  🔄 Running...   │                                │
│                  │                                │
└──────────────────┴──────────────────────────────────┘
```

---

## 📈 Log Display

### **Color Coding**

- **Blue**: General info messages
- **🟢 Green**: Success messages (✅)
- **🔴 Red**: Error messages (❌)
- **🟡 Yellow**: Warning messages (⚠️)

### **Example Log Output**

```
[00:12:30] 🚀 Starting automation task: reset password for john@company.com
[00:12:30] 📋 Task ID: a1b2c3d4
[00:12:30] ============================================================
[00:12:30] 🔧 Initializing agent...
[00:12:30] ⏳ Planning phase starting...
[00:12:31] 📝 PHASE 1: PLANNING
[00:12:31] ----------------------------------------
[00:12:32] ✅ Plan generated with 8 steps
[00:12:32] ⚡ PHASE 2: EXECUTION (ReAct Loop)
[00:12:33] ──────────────────────────────────────
[00:12:33] STEP 1/8: Opening login page
[00:12:34] ✅ Navigated to http://localhost:8000/login
[00:12:34] STEP 2/8: Entering credentials
[00:12:35] ✅ Filled username: admin
[00:12:35] ✅ Filled password: ****
[00:12:36] STEP 3/8: Submitting login form
[00:12:37] ✅ Clicked submit button
[00:12:38] ✅ Login successful
[00:12:38] STEP 4/8: Navigating to password reset page
...
[00:12:50] ✅ Task completed successfully!
[00:12:50] 📊 Execution summary:
[00:12:50]    - Success: true
[00:12:50]    - Steps: 8
[00:12:50]    - Duration: 20.34s
```

---

## 🔄 Job Status Lifecycle

```
SUBMITTED
   ↓
RUNNING (shown in real-time)
   ├─ Planning phase
   ├─ Browser startup
   ├─ Step execution (1, 2, 3...)
   └─ Cleanup
   ↓
COMPLETED ✅  OR  FAILED ❌
```

### **Status Panel**
- Shows `Job: {id}` - Track by ID
- Updates live: `🔄 Running...` → `✅ Completed` or `❌ Failed`
- Duration measured in seconds

---

## 📥 Downloading Logs

1. Run any automation task
2. Wait for completion
3. Click **"📥 Download Logs"** button
4. File saves as: `automation_{job_id}_{date}.txt`
5. Example: `automation_a1b2c3d4_2026-04-14.txt`

**Use logs for:**
- Debugging failed tasks
- Auditing automation runs
- Documentation
- Sharing with team

---

## 💾 Job History

The **Job History** section at the bottom shows:

| Info | Meaning |
|------|---------|
| **✅** | Task completed successfully |
| **❌** | Task failed |
| **🔄** | Currently running |
| **⏱️** | Pending/queued |
| Task name | First 60 characters of the task |
| Job ID | Unique identifier for tracking |
| Timestamp | When the task was submitted |

**Click any job** to view full details (future enhancement).

---

## 🏗️ Architecture

### **How It Works**

```
User Browser
    ↓
[1. User fills form & clicks Execute]
    ↓
POST /api/automation/submit
    ↓
Backend creates JobExecutor instance
    ├─ Generates unique job_id
    ├─ Starts agent in background (asyncio)
    └─ Returns {job_id, status: "submitted"}
    ↓
User browser receives job_id
    ↓
[2. Browser opens SSE stream]
    ↓
GET /api/automation/{job_id}/logs (Server-Sent Events)
    ↓
Agent executes in background:
    ├─ Initialize (Playwright, Groq)
    ├─ Plan (LLM generates step plan)
    ├─ Execute step 1
    ├─ Observe result
    ├─ Execute step 2
    ├─ ... (repeat)
    └─ Complete
    ↓
Each log message sent immediately to browser via SSE
    ↓
Browser displays logs in real-time
    ↓
[3. When complete, SSE stream closes]
    ↓
Browser shows final status & result
```

### **Components**

| File | Purpose |
|------|---------|
| `backend/routes/automation.py` | API endpoints for task submission & log streaming |
| `backend/templates/automation-console.html` | Interactive web UI |
| `agent/agent.py` | Core execution engine (modified to capture logs) |

### **Key Classes**

- **`JobExecutor`** - Manages one automation job
  - `log()` - Add timestamped log entries
  - `execute()` - Run the agent asynchronously
  - `_setup_log_capture()` - Hook into agent logging

---

## ⚙️ Configuration

### **Environment Variables**

```bash
# .env file
GROQ_MODEL=llama-3.3-70b-versatile  # Default model (can override)
BACKEND_URL=http://localhost:8000   # For Railway deployment
```

### **Agent Settings**

In `backend/routes/automation.py`, line ~70:

```python
self.agent = ITSupportAgent(
    headless=True,      # ✅ Railway: headless=True
    log_dir="logs",     # ✅ Railway: /tmp/logs (auto-created)
    groq_model=GROQ_MODEL
)
```

---

## 🐛 Troubleshooting

### **Issue: "Task failed" immediately**

**Cause:** Agent couldn't initialize or connect to backend

**Solution:**
1. Check backend is running: `http://localhost:8000/dashboard`
2. Check GROQ_API_KEY is set in `.env`
3. Check Playwright is installed: `playwright install chromium`
4. Look at browser console (F12) for network errors

### **Issue: Logs not updating in real-time**

**Cause:** SSE connection issue

**Solution:**
1. Check browser allows streaming (some proxies block it)
2. Disable browser cache: Dev Tools → Settings → Disable cache
3. Try with a different browser
4. Check network tab in Dev Tools for `204 No Content` errors

### **Issue: "ModuleNotFoundError: No module named 'agent'"**

**Cause:** Wrong Python path or venv not activated

**Solution:**
```bash
# Make sure venv is activated
.\venv\Scripts\activate
# Check Python path
python -c "import sys; print(sys.path)"
```

### **Issue: Agent executes but nothing appears in logs**

**Cause:** Log capture handler didn't attach properly

**Solution:**
1. Check browser console for JavaScript errors
2. Check SSE stream headers in Network tab
3. Restart browser and backend

---

## 🚀 Deployment to Railway

### **Step 1: Code is Already Ready**

✅ No special configuration needed! The console:
- Works with `headless=True` in Railway
- Uses in-memory job queue (good for testing)
- Streams logs via SSE (Railway supports it)
- No additional dependencies

### **Step 2: Deploy**

```bash
git push origin master
```

Railway auto-redeploys.

### **Step 3: Access in Production**

```
https://your-railway-app.railway.app/automation
```

Login with: `admin/admin123`

### **Step 4: Use in Production**

Same as local! Click **🤖 Automation** button and submit tasks.

---

## 📝 Production Considerations

### **Current Implementation (Demo)**

- ✅ In-memory job storage (lost on restart)
- ✅ No database persistence
- ✅ Single Railway dyno (can't scale to multiple workers)
- ✅ Logs stored in memory (not persisted)

### **For Production Upgrade**

If you want to persist job history and scale:

**Option 1: Add PostgreSQL + Redis**

```python
# Persist jobs to database
jobs_table.insert({
    job_id, task, status, logs, result, created_at, completed_at
})

# Use Redis for job queue
queue = redis.Queue()
queue.enqueue(execute_automation_task, job_id, task)
```

**Option 2: Add Worker Service**

```
Railway Service 1: Web (frontend + API)
Railway Service 2: Worker (executes jobs)
Railway Service 3: Redis (job queue)
Railway Service 4: PostgreSQL (persistence)
```

---

## 📚 API Reference

### **Submit Task**

```http
POST /api/automation/submit
Content-Type: application/x-www-form-urlencoded

task=reset password for john@company.com

Response:
{
  "job_id": "a1b2c3d4",
  "status": "submitted",
  "task": "reset password for john@company.com"
}
```

### **Stream Logs (SSE)**

```http
GET /api/automation/{job_id}/logs

Response headers:
Content-Type: text/event-stream
Cache-Control: no-cache

Response body (streaming):
data: {"timestamp": "00:12:30", "level": "info", "message": "🚀 Starting..."}
data: {"timestamp": "00:12:31", "level": "success", "message": "✅ Logged in"}
data: {"type": "complete", "status": "completed", "result": {...}}
```

### **Get Job Status**

```http
GET /api/automation/{job_id}/status

Response:
{
  "job_id": "a1b2c3d4",
  "task": "reset password for john@company.com",
  "status": "completed",
  "log_count": 24,
  "start_time": "2026-04-14T12:30:00",
  "end_time": "2026-04-14T12:30:50",
  "duration": 50.23,
  "result": {
    "success": true,
    "steps_taken": 8,
    "actions": [...]
  }
}
```

### **Get Recent Jobs**

```http
GET /api/automation/jobs/recent

Response:
{
  "jobs": [
    {
      "job_id": "a1b2c3d4",
      "task": "reset password for john@company.com",
      "status": "completed",
      "start_time": "2026-04-14T12:30:00"
    },
    ...
  ]
}
```

---

## 🔐 Security

### **Current Implementation**

- ✅ Session authentication required (`/api/automation/*` checks cookies)
- ✅ Only authenticated users can submit tasks
- ✅ CSRF protection via form submission
- ✅ XSS protection via Jinja2 template escaping

### **Recommendations for Production**

- [ ] Add rate limiting (prevent task spam)
- [ ] Add audit logging (who ran what, when)
- [ ] Add approval workflow (admin reviews before execution)
- [ ] Add timeout limits (kill jobs running > 5 minutes)
- [ ] Add resource limits (CPU, memory per job)
- [ ] Encrypt job logs at rest

---

## 📞 Support

**Local Issue?** Check logs:
```bash
# Check browser console (F12)
# Check backend terminal output
# Check logs/\*.json files
```

**Railway Issue?** Check:
```
Railway Dashboard → Deployments → {your-deploy} → Logs
```

---

## 🎉 Next Steps

1. ✅ Test locally first: `http://localhost:8000/automation`
2. ✅ Try all 4 templates and watch logs live
3. ✅ Push to GitHub: `git push origin master`
4. ✅ Redeploy Railway (auto-redeploy on push)
5. ✅ Test in production: `https://your-app.railway.app/automation`
6. ✅ Share with team!

---

**Built with ❤️ for IT automation. Watch those steps execute! 🚀**
