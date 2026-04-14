"""
Automation task routes: /automation/console, /api/automation/submit, /api/automation/logs
Allows users to submit IT automation tasks through a web UI and see real-time execution logs.
"""

import asyncio
import json
import logging
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

from agent.agent import ITSupportAgent

# Load environment
load_dotenv()
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

router = APIRouter()
templates = Jinja2Templates(directory="backend/templates")

# In-memory job storage (for demo; use database for production)
jobs_store: dict = {}

logger = logging.getLogger("automation")


def require_auth(request: Request):
    """Simple auth guard."""
    return request.cookies.get("session") == "authenticated"


class JobExecutor:
    """Manages job execution with real-time log streaming."""
    
    def __init__(self, job_id: str, task: str):
        self.job_id = job_id
        self.task = task
        self.logs: list = []
        self.status = "pending"  # pending, running, completed, failed
        self.result: Optional[dict] = None
        self.start_time = None
        self.end_time = None
        self.agent: Optional[ITSupportAgent] = None
        
    def log(self, message: str, level: str = "info"):
        """Add a log message with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = {
            "timestamp": timestamp,
            "level": level,
            "message": message
        }
        self.logs.append(log_entry)
        logger.info(f"[{self.job_id}] {message}")
        
    def execute(self):
        """Execute the automation task in a new event loop (runs in thread)."""
        self.status = "running"
        self.start_time = datetime.now()
        
        try:
            self.log(f"🚀 Starting automation task: {self.task}", "info")
            self.log(f"📋 Task ID: {self.job_id}", "info")
            self.log("=" * 60, "info")
            
            # Initialize agent
            self.log("🔧 Initializing agent...", "info")
            self.agent = ITSupportAgent(
                headless=True,  # No GUI in railway
                log_dir="logs",
                groq_model=GROQ_MODEL
            )
            
            # Hook into agent logging
            self._setup_log_capture()
            
            # Create a new event loop for this thread
            # This is necessary for Playwright on Windows to work properly
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Run the agent in the new event loop
                self.log("⏳ Planning phase starting...", "info")
                result = loop.run_until_complete(self.agent.run(self.task))
                
                self.log("=" * 60, "info")
                self.log(f"✅ Task completed successfully!", "success")
                self.log(f"📊 Execution summary:", "info")
                self.log(f"   - Success: {result.get('success', False)}", "info")
                self.log(f"   - Steps: {result.get('steps_taken', 0)}", "info")
                self.log(f"   - Duration: {result.get('duration', 0):.2f}s", "info")
                
                self.result = result
                self.status = "completed"
            finally:
                loop.close()
            
        except Exception as e:
            error_msg = str(e)
            self.log(f"❌ Error: {error_msg}", "error")
            self.log("Task failed. Check logs above for details.", "error")
            self.status = "failed"
            self.result = {"success": False, "error": error_msg}
            import traceback
            self.log(traceback.format_exc(), "error")
            
        finally:
            self.end_time = datetime.now()
            # Clean up browser
            if self.agent:
                try:
                    # Run close in the same loop if it exists
                    if asyncio.get_event_loop().is_running():
                        asyncio.create_task(self.agent.tools.close())
                    else:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            loop.run_until_complete(self.agent.tools.close())
                        finally:
                            loop.close()
                except:
                    pass
    
    def _setup_log_capture(self):
        """Capture agent logs to our log system."""
        # Get the agent logger and add our handler
        agent_logger = logging.getLogger("agent.core")
        
        class LogCapture(logging.Handler):
            def __init__(self, job_executor):
                super().__init__()
                self.executor = job_executor
                
            def emit(self, record):
                try:
                    message = self.format(record)
                    # Extract level
                    level = record.levelname.lower()
                    # Add to logs
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    self.executor.logs.append({
                        "timestamp": timestamp,
                        "level": level,
                        "message": message
                    })
                except Exception:
                    pass
        
        # Add our capture handler
        capture_handler = LogCapture(self)
        agent_logger.addHandler(capture_handler)


# Thread pool for running blocking operations
executor_pool = ThreadPoolExecutor(max_workers=3, thread_name_prefix="automation_")

# ---------------------------------------------------------------------------
# GET /automation — automation control panel (web UI)
# ---------------------------------------------------------------------------
@router.get("/automation", response_class=HTMLResponse)
async def automation_console(request: Request):
    """Show the automation task control panel."""
    if not require_auth(request):
        return RedirectResponse(url="/login", status_code=302)
    
    return templates.TemplateResponse(
        "automation-console.html",
        {"request": request}
    )


# ---------------------------------------------------------------------------
# POST /api/automation/submit — submit a new automation task
# ---------------------------------------------------------------------------
@router.post("/api/automation/submit")
async def submit_task(request: Request, task: str = Form(...)):
    """Submit a new automation task."""
    if not require_auth(request):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    if not task or len(task.strip()) < 5:
        return JSONResponse(
            {"error": "Task must be at least 5 characters"},
            status_code=400
        )
    
    # Create job
    job_id = str(uuid4())[:8]
    executor = JobExecutor(job_id, task)
    jobs_store[job_id] = executor
    
    # Start execution in a thread pool (not in FastAPI's event loop)
    # This avoids the Playwright subprocess issue on Windows
    loop = asyncio.get_event_loop()
    loop.run_in_executor(executor_pool, executor.execute)
    
    return JSONResponse({
        "job_id": job_id,
        "status": "submitted",
        "task": task
    })


# ---------------------------------------------------------------------------
# GET /api/automation/{job_id}/logs — stream execution logs (SSE)
# ---------------------------------------------------------------------------
@router.get("/api/automation/{job_id}/logs")
async def stream_logs(job_id: str, request: Request):
    """Stream execution logs as Server-Sent Events."""
    if not require_auth(request):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    job = jobs_store.get(job_id)
    if not job:
        return JSONResponse({"error": "Job not found"}, status_code=404)
    
    async def log_generator():
        """Generate log events for streaming."""
        sent_count = 0
        
        while True:
            # Get new logs since last check
            new_logs = job.logs[sent_count:]
            
            # Send all new logs
            for log_entry in new_logs:
                data = json.dumps(log_entry)
                yield f"data: {data}\n\n"
                sent_count += 1
            
            # If job is done and all logs sent, signal completion
            if job.status != "running" and sent_count >= len(job.logs):
                yield f"data: {json.dumps({'type': 'complete', 'status': job.status, 'result': job.result})}\n\n"
                break
            
            # Wait before checking again (prevents busy looping)
            await asyncio.sleep(0.5)
    
    return StreamingResponse(
        log_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# ---------------------------------------------------------------------------
# GET /api/automation/{job_id}/status — get job status
# ---------------------------------------------------------------------------
@router.get("/api/automation/{job_id}/status")
async def get_job_status(job_id: str, request: Request):
    """Get current job status."""
    if not require_auth(request):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    job = jobs_store.get(job_id)
    if not job:
        return JSONResponse({"error": "Job not found"}, status_code=404)
    
    return JSONResponse({
        "job_id": job_id,
        "task": job.task,
        "status": job.status,
        "log_count": len(job.logs),
        "start_time": job.start_time.isoformat() if job.start_time else None,
        "end_time": job.end_time.isoformat() if job.end_time else None,
        "duration": (job.end_time - job.start_time).total_seconds() if job.end_time and job.start_time else None,
        "result": job.result
    })


# ---------------------------------------------------------------------------
# GET /api/automation/jobs/recent — list recent jobs
# ---------------------------------------------------------------------------
@router.get("/api/automation/jobs/recent")
async def get_recent_jobs(request: Request):
    """List recent automation jobs."""
    if not require_auth(request):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    jobs = []
    for job_id, executor in sorted(jobs_store.items(), key=lambda x: x[1].start_time or datetime.now(), reverse=True)[:10]:
        jobs.append({
            "job_id": job_id,
            "task": executor.task,
            "status": executor.status,
            "start_time": executor.start_time.isoformat() if executor.start_time else None,
        })
    
    return JSONResponse({"jobs": jobs})
