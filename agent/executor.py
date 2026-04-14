"""
Step Executor — Translates agent actions into browser tool calls
---------------------------------------------------------------
The executor receives a single action dict from the planner and
dispatches it to the correct BrowserTools method.

It also handles:
- Retry logic (up to 3 attempts per step)
- Error observation and reporting back to the agent loop
- Action result normalization
"""

import asyncio
import logging
from typing import Optional

from agent.tools import BrowserTools

logger = logging.getLogger("agent.executor")

# Maximum number of retry attempts before escalating to replanner
MAX_RETRIES = 3

# Delay between retries (seconds)
RETRY_DELAY = 1.5


class Executor:
    """
    Dispatches individual agent actions to Playwright browser tools.
    Handles retries and translates tool results to agent observations.
    """

    def __init__(self, tools: BrowserTools):
        """
        Args:
            tools: Initialized BrowserTools instance (browser already launched)
        """
        self.tools = tools
        self._action_log: list[dict] = []  # Full history of actions + results

    def get_action_log(self) -> list[dict]:
        """Return the complete log of all executed actions."""
        return self._action_log

    async def execute(self, action: dict) -> dict:
        """
        Execute a single agent action with retry logic.

        Args:
            action: Dict with keys: action, target, value, reasoning, expected_outcome

        Returns:
            Result dict with: success, observation, action_name
        """
        action_name = action.get("action", "unknown")
        target = action.get("target", "")
        value = action.get("value", "")
        reasoning = action.get("reasoning", "")
        expected = action.get("expected_outcome", "")

        logger.info(f"⚡ EXECUTE: [{action_name}] target='{target}' value='{value}'")
        logger.info(f"   💭 Reasoning: {reasoning}")
        logger.info(f"   🎯 Expected: {expected}")

        result = None
        last_error = None

        # Retry loop
        for attempt in range(1, MAX_RETRIES + 1):
            if attempt > 1:
                logger.info(f"   🔁 Retry attempt {attempt}/{MAX_RETRIES}...")
                await asyncio.sleep(RETRY_DELAY)

            try:
                result = await self._dispatch(action_name, target, value)

                if result.get("success"):
                    break  # Success — exit retry loop
                else:
                    last_error = result.get("error", "Unknown error")
                    logger.warning(f"   ⚠️ Attempt {attempt} failed: {last_error}")

            except Exception as e:
                last_error = str(e)
                logger.error(f"   ❌ Exception on attempt {attempt}: {e}")
                result = {"success": False, "error": str(e), "observation": f"Exception: {e}"}

        # If all retries failed, mark as failed
        if result is None or not result.get("success"):
            result = result or {}
            result["success"] = False
            result["observation"] = result.get("observation", f"All {MAX_RETRIES} attempts failed. Last error: {last_error}")

        # Log this action
        log_entry = {
            "action": action_name,
            "target": target,
            "value": value,
            "reasoning": reasoning,
            "result": result,
        }
        self._action_log.append(log_entry)

        # Log outcome
        status = "✅" if result.get("success") else "❌"
        logger.info(f"   {status} Result: {result.get('observation', 'no observation')}")

        return result

    # ----------------------------------------------------------------
    # Action dispatcher — maps action names to tool calls
    # ----------------------------------------------------------------

    async def _dispatch(self, action_name: str, target: str, value: str) -> dict:
        """
        Route action name to the corresponding BrowserTools method.

        Args:
            action_name: Action key from LLM output
            target: CSS selector, URL, or text depending on action
            value: Value to type/select (may be empty)

        Returns:
            Tool result dict
        """
        # Normalize action name (handle underscores/aliases)
        action_name = action_name.lower().replace("-", "_")

        dispatch_table = {
            # Navigation
            "open_url": lambda: self.tools.open_url(target),
            "navigate": lambda: self.tools.open_url(target),
            "goto": lambda: self.tools.open_url(target),

            # Interaction
            "click": lambda: self.tools.click(target, description=value or target),
            "type_text": lambda: self.tools.type_text(target, value),
            "fill": lambda: self.tools.type_text(target, value),
            "type": lambda: self.tools.type_text(target, value),
            "select_option": lambda: self.tools.select_option(target, value),
            "select": lambda: self.tools.select_option(target, value),

            # Observation
            "extract_text": lambda: self.tools.extract_text(target or "body"),
            "read_page": lambda: self.tools.extract_text("body"),
            "check_element_exists": lambda: self.tools.check_element_exists(target),
            "get_page_text_contains": lambda: self.tools.get_page_text_contains(target),
            "page_contains": lambda: self.tools.get_page_text_contains(target),
            "verify": lambda: self.tools.get_page_text_contains(target),

            # Utility
            "wait": lambda: self.tools.wait(float(target) if target.replace(".", "").isdigit() else 1.0),
            "take_screenshot": lambda: self.tools.take_screenshot(target or "screenshot.png"),
            "screenshot": lambda: self.tools.take_screenshot(target or "screenshot.png"),

            # Form submission
            "submit_form": lambda: self.tools.submit_form(target or "form"),

            # Terminal action — handled by agent loop, not tools
            "done": lambda: {"success": True, "observation": f"Task completed: {target}", "done": True},
        }

        handler = dispatch_table.get(action_name)
        if handler is None:
            logger.warning(f"⚠️ Unknown action: '{action_name}'. Treating as no-op.")
            return {"success": False, "error": f"Unknown action: {action_name}", "observation": f"Unknown action '{action_name}'"}

        return await handler()
