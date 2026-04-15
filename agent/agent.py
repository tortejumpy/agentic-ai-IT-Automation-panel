"""
Agentic IT Support Agent — Main Orchestrator
=============================================
Implements the ReAct (Reason → Act → Observe → Reflect) loop.

Flow:
  1. Receive natural language request
  2. Planner generates initial step plan (LLM call)
  3. For each step:
     a. Executor runs the browser action
     b. Observe the result (page content / success message)
     c. Planner decides next step based on observation
     d. If step fails: retry → replan → abort
  4. Log all actions with results
  5. Return final summary

This is the heart of the agentic system.
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from agent.planner import Planner
from agent.executor import Executor
from agent.tools import BrowserTools

# ---------------------------------------------------------------------------
# Logging setup — rich format with timestamps
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("agent.core")

# Maximum steps before forcing a stop (prevents infinite loops)
MAX_STEPS = 30

# Base URL for the IT admin panel.
# On Railway, $PORT is assigned dynamically at runtime — never hardcode 8000.
# BACKEND_URL env var overrides everything (useful for staging/custom domains).
def _get_base_url() -> str:
    explicit = os.getenv("BACKEND_URL", "").strip()
    if explicit:
        return explicit.rstrip("/")
    port = os.getenv("PORT", "8000")
    return f"http://localhost:{port}"

BASE_URL = _get_base_url()


class ITSupportAgent:
    """
    The main agentic AI system.
    Orchestrates the Plan → Execute → Observe → Refine loop.
    """

    def __init__(
        self,
        headless: bool = False,
        log_dir: str = "logs",
        groq_model: str = "llama-3.3-70b-versatile",
        base_url: str = None,
    ):
        """
        Args:
            headless: If False, opens visible browser. Set True for CI/background.
            log_dir: Directory to save action logs and screenshots.
            groq_model: Groq model ID for the planner.
        """
        self.headless = headless
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Resolve backend URL — must match the port this process is bound to.
        # On Railway $PORT is dynamic; on local dev it defaults to 8000.
        self.base_url = base_url or _get_base_url()
        logger.info(f"🌐 Backend URL: {self.base_url}")

        # Initialize components
        self.tools = BrowserTools(headless=headless)
        self.planner = Planner(model=groq_model, base_url=self.base_url)
        self.executor: Optional[Executor] = None  # Created after browser starts

        # Session state
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.is_running = False

    async def run(self, request: str) -> dict:
        """
        Main entry point: execute an IT support request end-to-end.

        Args:
            request: Natural language IT task, e.g.,
                     "reset password for john@company.com"
                     "create user alice@company.com and assign pro license"

        Returns:
            Summary dict with: success, steps_taken, actions, duration
        """
        start_time = time.time()
        logger.info("=" * 65)
        logger.info(f"🤖 IT SUPPORT AGENT — Session {self.session_id}")
        logger.info(f"📋 Request: {request}")
        logger.info("=" * 65)

        self.is_running = True

        try:
            # ── Phase 1: Start browser ─────────────────────────────────────
            await self.tools.start()
            self.executor = Executor(self.tools)

            # ── Phase 2: Generate initial plan ────────────────────────────
            logger.info("\n📝 PHASE 1: PLANNING")
            logger.info("-" * 40)
            initial_plan = self.planner.generate_initial_plan(request)

            if not initial_plan:
                logger.error("❌ Planner returned empty plan. Aborting.")
                return self._build_result(request, False, "Planner returned empty plan", start_time)

            logger.info(f"✅ Plan generated with {len(initial_plan)} steps")

            # ── Phase 3: Execute steps (ReAct loop) ───────────────────────
            logger.info("\n⚡ PHASE 2: EXECUTION (ReAct Loop)")
            logger.info("-" * 40)

            history = []         # Tracks all (action, result) pairs
            current_step = 0
            task_done = False
            task_success = False
            final_summary = ""

            # Execute the initial plan steps
            for step in initial_plan:
                if current_step >= MAX_STEPS:
                    logger.warning(f"⚠️ Reached max steps limit ({MAX_STEPS}). Stopping.")
                    break

                current_step += 1
                step_num = step.get("step", current_step)
                logger.info(f"\n{'─'*50}")
                logger.info(f"STEP {step_num}/{len(initial_plan)}: {step.get('reasoning', 'executing...')}")

                # ── ACT: Execute the action ────────────────────────────────
                result = await self.executor.execute(step)

                # Record in history
                history.append({"action": step, "result": result})

                # ── OBSERVE: Read current page state ──────────────────────
                observation = result.get("observation", "")

                # Terminal: done action
                if step.get("action") == "done" or result.get("done"):
                    task_done = True
                    task_success = True
                    final_summary = step.get("target", "Task completed")
                    logger.info(f"🏁 Task completed: {final_summary}")
                    break

                # Check for failure with no recovery
                if not result.get("success"):
                    logger.warning(f"⚠️ Step failed: {result.get('error', 'unknown')}")

                    # ── REPLAN: Ask LLM for recovery action ───────────────
                    recovery = self.planner.replan_on_failure(
                        request=request,
                        failed_step=step,
                        error=result.get("error", "step failed"),
                        history=history,
                    )

                    if recovery and recovery.get("action") != "done":
                        logger.info(f"🔄 Attempting recovery: {recovery.get('action')}")
                        recovery_result = await self.executor.execute(recovery)
                        history.append({"action": recovery, "result": recovery_result})

                        if not recovery_result.get("success"):
                            logger.error("❌ Recovery also failed. Continuing to next step.")
                    else:
                        logger.error("❌ Cannot recover. Continuing to next step.")

                # ── REFINE: After plan completes, use ReAct to decide more ─
                # (Only if we're on the last planned step and task isn't done)

            # ── Phase 4: ReAct continuation (if plan finished but task not done) ──
            if not task_done and current_step < MAX_STEPS:
                logger.info("\n🔄 PHASE 3: REACT CONTINUATION")
                logger.info("-" * 40)
                logger.info("Plan finished — using ReAct loop to verify completion...")

                # Get current page state for observation
                obs_result = await self.executor.execute({
                    "action": "extract_text",
                    "target": "body",
                    "value": "",
                    "reasoning": "Observing current page state",
                })
                current_observation = obs_result.get("text", obs_result.get("observation", ""))[:1000]

                # Ask LLM if we're done or need more steps
                for _ in range(5):  # Max 5 additional ReAct cycles
                    if current_step >= MAX_STEPS:
                        break

                    next_action = self.planner.decide_next_action(
                        request=request,
                        history=[{"action": h["action"].get("action", ""), "result": h["result"]} for h in history],
                        current_observation=current_observation,
                    )

                    if next_action.get("action") == "done":
                        task_done = True
                        task_success = True
                        final_summary = next_action.get("target", "Task completed")
                        logger.info(f"🏁 Agent confirmed done: {final_summary}")
                        break

                    current_step += 1
                    result = await self.executor.execute(next_action)
                    history.append({"action": next_action, "result": result})

                    # Update observation
                    current_observation = result.get("observation", "")

                    if result.get("done"):
                        task_done = True
                        task_success = True
                        final_summary = "Task completed via ReAct loop"
                        break

            # ── Phase 5: Final screenshot and summary ──────────────────────
            screenshot_path = str(self.log_dir / f"{self.session_id}_final.png")
            await self.tools.take_screenshot(screenshot_path)

            # If we finished all steps but no "done" signal, check page for success
            if not task_done:
                obs = await self.executor.execute({
                    "action": "extract_text",
                    "target": "body",
                    "value": "",
                    "reasoning": "Final page check",
                })
                page_text = obs.get("text", "").lower()
                if "successfully" in page_text or "✅" in page_text:
                    task_success = True
                    final_summary = "Task completed (success message detected on page)"
                else:
                    task_success = False
                    final_summary = "Task may not have completed — no success message detected"

            return self._build_result(
                request, task_success, final_summary, start_time,
                steps_taken=current_step,
            )

        except KeyboardInterrupt:
            logger.info("\n⚠️ Interrupted by user.")
            return self._build_result(request, False, "Interrupted by user", start_time)

        except Exception as e:
            logger.error(f"\n💥 Unhandled exception: {e}", exc_info=True)
            return self._build_result(request, False, f"Fatal error: {e}", start_time)

        finally:
            # Always save the action log
            self._save_log()
            await self.tools.close()
            self.is_running = False

    # ----------------------------------------------------------------
    # Internal helpers
    # ----------------------------------------------------------------

    def _build_result(
        self,
        request: str,
        success: bool,
        summary: str,
        start_time: float,
        steps_taken: int = 0,
    ) -> dict:
        """Build the final result dict returned to the caller."""
        duration = round(time.time() - start_time, 2)

        result = {
            "session_id": self.session_id,
            "request": request,
            "success": success,
            "summary": summary,
            "steps_taken": steps_taken,
            "duration_seconds": duration,
            "actions": self.executor.get_action_log() if self.executor else [],
            "log_dir": str(self.log_dir),
        }

        logger.info("\n" + "=" * 65)
        logger.info(f"{'✅ SUCCESS' if success else '❌ FAILED'}: {summary}")
        logger.info(f"📊 Steps: {steps_taken} | Duration: {duration}s")
        logger.info("=" * 65 + "\n")

        return result

    def _save_log(self):
        """Save the complete action log to a JSON file."""
        if not self.executor:
            return

        log_path = self.log_dir / f"{self.session_id}_actions.json"
        try:
            with open(log_path, "w") as f:
                json.dump(self.executor.get_action_log(), f, indent=2, default=str)
            logger.info(f"💾 Action log saved: {log_path}")
        except Exception as e:
            logger.error(f"⚠️ Could not save log: {e}")


# ---------------------------------------------------------------------------
# Convenience: run synchronously from non-async contexts
# ---------------------------------------------------------------------------
def run_agent(request: str, headless: bool = False) -> dict:
    """
    Synchronous wrapper for use in CLI scripts.

    Args:
        request: Natural language IT task
        headless: Whether to run browser headlessly

    Returns:
        Result dict from agent.run()
    """
    agent = ITSupportAgent(headless=headless)
    return asyncio.run(agent.run(request))
