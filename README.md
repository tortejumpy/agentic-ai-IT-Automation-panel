# 🤖 Agentic AI IT Support Automation System

A production-quality agentic AI system that automates IT admin tasks using **browser automation + LLM reasoning**. The agent operates like a human user navigating a real web interface — no API shortcuts.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  CLI: python run_agent.py "reset password for john@company.com" │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │  ITSupportAgent │  ← ReAct Loop Orchestrator
                    │   agent/agent.py│
                    └────────┬────────┘
         ┌───────────────────┼───────────────────┐
   ┌─────▼──────┐     ┌──────▼──────┐     ┌──────▼──────┐
   │ Planner    │     │ Executor    │     │ BrowserTools│
   │ (Groq LLM) │     │ (Dispatch + │     │ (Playwright)│
   │ planner.py │     │  Retry)     │     │ tools.py    │
   └────────────┘     └─────────────┘     └──────┬──────┘
                                                  │
                                         ┌────────▼────────┐
                                         │ Mock IT Admin   │
                                         │ FastAPI + HTML  │
                                         │ localhost:8000  │
                                         └─────────────────┘
```

### ReAct Loop (Reason → Act → Observe → Refine)

```
1. PLAN    → LLM converts NL request to step-by-step action plan
2. ACT     → Playwright executes browser actions (click, type, navigate)
3. OBSERVE → Read page content to verify result
4. REFINE  → LLM decides next action OR confirms task completion
             (with retry + replan on failures)
```

---

## 📁 Project Structure

```
agentic-ai/
│
├── backend/                    # Mock IT Admin Panel (FastAPI)
│   ├── main.py                 # App entry point, route registration
│   ├── routes/
│   │   ├── auth.py             # /login, /logout
│   │   ├── users.py            # /users, /create-user
│   │   └── admin.py            # /dashboard, /reset-password, /assign-license
│   ├── models/
│   │   └── database.py         # In-memory user store + CRUD helpers
│   └── templates/              # Jinja2 HTML templates
│       ├── base.html           # Dark-theme design system + nav
│       ├── login.html
│       ├── dashboard.html
│       ├── users.html
│       ├── create_user.html
│       ├── reset_password.html
│       └── assign_license.html
│
├── agent/                      # AI Agent Core
│   ├── agent.py                # Main orchestrator (ReAct loop)
│   ├── planner.py              # Groq LLM planner + system prompt
│   ├── executor.py             # Action dispatcher + retry logic
│   └── tools.py                # Playwright browser tools
│
├── run_agent.py                # CLI entry point
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variables template
├── run.sh                      # One-command startup script
└── README.md
```

---

## ⚙️ Setup Instructions

### 1. Prerequisites

- Python 3.10+
- A [Groq API key](https://console.groq.com/keys) (free tier available)

### 2. Clone & Install

```bash
# Navigate to the project
cd agentic-ai

# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate

# Activate (Linux/macOS)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browser (Chromium)
playwright install chromium
```

### 3. Configure Environment

```bash
# Copy the example file
copy .env.example .env       # Windows
cp .env.example .env         # Linux/macOS

# Edit .env and add your Groq API key
GROQ_API_KEY=your_groq_api_key_here
```

---

## 🚀 Running the System

### Step 1: Start the Mock IT Admin Panel

```bash
# From the project root (with venv activated)
uvicorn backend.main:app --reload
```

The admin panel will be available at: **http://localhost:8000**

**Login credentials:** `admin` / `admin123`

---

### Step 2: Run the AI Agent (in a new terminal)

```bash
# Reset a user's password
python run_agent.py "reset password for john@company.com"

# Create a new user
python run_agent.py "create user alice@company.com with name Alice Johnson"

# Create user AND assign pro license (multi-step)
python run_agent.py "create user bob@company.com and assign pro license"

# Assign enterprise license to existing user
python run_agent.py "assign enterprise license to jane@company.com"

# Run headlessly (no browser window)
python run_agent.py --headless "reset password for john@company.com"

# Use a faster/smaller model
python run_agent.py --model llama-3.1-8b-instant "reset password for john@company.com"

# Output result as JSON
python run_agent.py --json "reset password for john@company.com"
```

---

## 🧠 Agent Behavior Design

### How the Agent Thinks

```
User: "Create user alice@company.com and assign pro license"

PLAN (LLM output):
  Step 1: open_url → http://localhost:8000/login
  Step 2: type_text → username field → "admin"
  Step 3: type_text → password field → "admin123"
  Step 4: click → login-submit-btn
  Step 5: open_url → http://localhost:8000/users  ← check if user exists first
  Step 6: get_page_text_contains → "alice@company.com"
  Step 7: (IF not found) open_url → http://localhost:8000/create-user
  Step 8: type_text → name → "Alice"
  Step 9: type_text → email → "alice@company.com"
  Step 10: type_text → password → "TempPass123"
  Step 11: click → create-user-submit-btn
  Step 12: get_page_text_contains → "created successfully"  ← verify
  Step 13: open_url → http://localhost:8000/assign-license
  Step 14: type_text → email → "alice@company.com"
  Step 15: select_option → license_type → "pro"
  Step 16: click → assign-license-submit-btn
  Step 17: get_page_text_contains → "assigned"  ← verify
  Step 18: done → "Created alice@company.com with pro license"
```

### Conditional Logic

The agent checks if a user **already exists** before creating:
```
IF "alice@company.com" found on /users page → skip create-user
ELSE → proceed with user creation
```

### Error Recovery

```
Step fails → Retry (up to 3 times)
           → Ask LLM for alternative approach (replan)
           → Continue with next step if unrecoverable
```

---

## 📋 Admin Panel Pages

| Route | Description | Key Form Fields |
|-------|-------------|-----------------|
| `/login` | Admin authentication | `username`, `password` |
| `/dashboard` | Stats overview + quick actions | N/A |
| `/users` | List all users | N/A |
| `/create-user` | Add new user | `name`, `email`, `password`, `license_type` |
| `/reset-password` | Reset user password | `email`, `new_password`, `confirm_password` |
| `/assign-license` | Assign license tier | `email`, `license_type` |

**License tiers:** `basic` | `pro` | `enterprise`

---

## 📊 Agent Tools Reference

| Tool | Description |
|------|-------------|
| `open_url(url)` | Navigate to URL, wait for page load |
| `click(selector)` | Click element (multi-strategy: ID, text, CSS) |
| `type_text(selector, text)` | Clear + fill a form field |
| `select_option(selector, value)` | Pick from a `<select>` dropdown |
| `extract_text(selector)` | Read page content for observation |
| `check_element_exists(selector)` | Check if element is present |
| `get_page_text_contains(text)` | Search page content for a string |
| `wait(seconds)` | Pause execution |
| `take_screenshot(path)` | Capture page for debugging |
| `submit_form(selector)` | Submit a form |

---

## 📁 Logs & Artifacts

Each agent run creates files in the `logs/` directory:

```
logs/
├── 20241214_143022_actions.json   ← Complete action log (JSON)
└── 20241214_143022_final.png      ← Screenshot at task completion
```

The action log contains every step with: action taken, target, value, and the observation result.

---

## 🔧 Configuration Options

```bash
python run_agent.py [OPTIONS] "your request"

Options:
  --headless          Run browser in headless mode (no window)
  --model MODEL       Groq model ID (default: llama-3.3-70b-versatile)
  --log-dir DIR       Directory for logs/screenshots (default: logs/)
  --json              Output result as JSON

Groq Model Options:
  llama-3.3-70b-versatile   Best quality (default)
  llama-3.1-8b-instant      Fastest, lower cost
  mixtral-8x7b-32768        High context window
```

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| `GROQ_API_KEY not set` | Create `.env` file with your Groq API key |
| `Connection refused` | Start the backend: `uvicorn backend.main:app --reload` |
| `Playwright not found` | Run: `playwright install chromium` |
| `Browser not visible` | Remove `--headless` flag |
| `LLM returns bad JSON` | Check Groq API key; try a different model |
| `Step fails repeatedly` | Take a screenshot (`--json` mode) and inspect the log |

---

## 🔒 Security Notes

- The admin panel uses cookie-based sessions (demo-grade, not production)
- Credentials are hardcoded (`admin/admin123`) — for demo purposes only
- User data is stored in-memory and resets on server restart
- The Groq API key must never be committed to version control

---

## 📜 License

MIT — Built for educational and demonstration purposes.
