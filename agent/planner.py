"""
LLM Planner — Groq Integration
--------------------------------
Converts natural language IT requests into structured JSON action plans.
Also serves as the "Reason" step in the ReAct loop, deciding the next
action based on previous observations.

The planner uses a carefully designed system prompt to ensure the LLM
outputs consistent, machine-parseable JSON plans.
"""

import json
import logging
import os
import re
from typing import Optional

from groq import Groq
from dotenv import load_dotenv

load_dotenv(override=True)

logger = logging.getLogger("agent.planner")

# ---------------------------------------------------------------------------
# System prompt — defines the agent's role and output format
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are an expert IT automation agent controlling a web browser.
You interact with a Mock IT Admin Panel running at http://localhost:8000.

## Your Role
- Automate IT support tasks by navigating the web UI like a human
- Never use shortcuts or API calls — always use the browser
- Always think step-by-step before acting

## Available Pages
- /login — Admin login (username: admin, password: admin123)
- /dashboard — Overview and quick actions
- /users — List all users
- /create-user — Create a new user (form with: name, email, password, license_type)
- /reset-password — Reset any user's password (form with: email, new_password, confirm_password)
- /assign-license — Assign license (form with: email, license_type). License options: basic, pro, enterprise

## Form Field IDs (use these as selectors)
### Login: username, password, login-submit-btn
### Create User: name, email, password, license_type, create-user-submit-btn
### Reset Password: email, new_password, confirm_password, reset-password-submit-btn
### Assign License: email, license_type, assign-license-submit-btn

## Rules
1. ALWAYS start by navigating to /login if not already authenticated
2. ALWAYS observe the result before deciding the next step
3. NEVER assume success — verify by checking the page for confirmation messages
4. If a step fails, retry once then try an alternative approach
5. For conditional logic (e.g., "if user exists, skip creation"), check /users first

## Output Format
ALWAYS output a valid JSON object with this exact structure:
{
    "action": "tool_name",
    "target": "selector_or_url",
    "value": "value_to_type_or_select_or_empty_string",
    "reasoning": "brief explanation of why this action",
    "expected_outcome": "what you expect to see after this action"
}

## Available Actions (tool_name values)
- open_url: navigate to a URL (target = URL)
- click: click an element (target = CSS selector or ID)
- type_text: type into a field (target = field ID, value = text to type)
- select_option: select dropdown option (target = select ID, value = option value)
- extract_text: read page content (target = "body" or CSS selector)
- check_element_exists: check if element is on page (target = CSS selector)
- get_page_text_contains: check if text appears on page (target = text to search)
- wait: pause execution (target = seconds as string, e.g., "1")
- take_screenshot: capture page (target = filename)
- done: signal task completion (target = summary of what was accomplished)

## CRITICAL
- Output ONLY the JSON object, no other text
- Use the exact field IDs listed above for form fields
- After submitting a form, always extract_text to verify the result
"""


# ---------------------------------------------------------------------------
# Initial planners — create actionable step sequences from NL requests
# ---------------------------------------------------------------------------
INITIAL_PLAN_PROMPT = """
Given the user's IT request, create a complete plan of browser actions.

User Request: "{request}"

Think through what steps are needed:
1. Login to admin panel
2. Navigate to the correct page
3. Fill in the required form fields
4. Submit and verify

Output ONLY a JSON array of action steps. Each step must follow this format:
{{
    "step": <number>,
    "action": "<tool_name>",
    "target": "<selector_or_url>",
    "value": "<value_or_empty>",
    "reasoning": "<why this step>",
    "expected_outcome": "<what to expect>"
}}
"""


class Planner:
    """
    Uses Groq LLM to:
    1. Generate an initial action plan from a natural language request
    2. Decide the next action based on current observations (ReAct step)
    3. Handle plan adjustments when steps fail
    """

    def __init__(self, model: str = "llama-3.3-70b-versatile"):
        """
        Args:
            model: Groq model to use. llama-3.3-70b-versatile is fast and capable.
        """
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable not set. Check your .env file.")

        self.client = Groq(api_key=api_key)
        self.model = model
        logger.info(f"🧠 Planner initialized with model: {model}")

    def generate_initial_plan(self, request: str) -> list[dict]:
        """
        Convert a natural language request into a sequential action plan.

        Args:
            request: e.g., "reset password for john@company.com"

        Returns:
            List of step dicts, each with action/target/value/reasoning
        """
        logger.info(f"📝 Generating initial plan for: '{request}'")

        prompt = INITIAL_PLAN_PROMPT.format(request=request)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,  # Low temperature for consistent, structured output
            max_tokens=2000,
        )

        content = response.choices[0].message.content.strip()
        logger.debug(f"🧠 Raw plan response:\n{content}")

        # Parse JSON from response (handle markdown code blocks)
        plan = self._parse_json(content)

        if isinstance(plan, list):
            logger.info(f"✅ Generated {len(plan)}-step plan")
            for i, step in enumerate(plan):
                logger.info(f"   Step {i+1}: {step.get('action')} → {step.get('target')} | {step.get('reasoning', '')}")
            return plan
        else:
            logger.warning("⚠️ Plan response wasn't a list, wrapping...")
            return [plan] if isinstance(plan, dict) else []

    def decide_next_action(
        self,
        request: str,
        history: list[dict],
        current_observation: str,
    ) -> dict:
        """
        ReAct 'Reason' step: given the current state, decide what to do next.
        Called after each action completes.

        Args:
            request: Original user request
            history: List of {action, result} dicts from previous steps
            current_observation: What we currently see on the page

        Returns:
            Next action dict, or {"action": "done", ...} when complete
        """
        logger.info("🤔 Deciding next action...")

        # Build a history summary for the LLM
        history_text = "\n".join([
            f"Step {i+1}: {h['action']} → {h.get('result', {}).get('observation', 'no observation')}"
            for i, h in enumerate(history)
        ])

        prompt = f"""
Original Task: "{request}"

Actions taken so far:
{history_text if history_text else "None — this is the first action."}

Current page observation:
{current_observation}

Based on the above, what is the SINGLE NEXT action to take?

If the task is fully complete (success message observed), output:
{{"action": "done", "target": "task_summary", "value": "", "reasoning": "Task completed", "expected_outcome": "Done"}}

Otherwise output the next action in JSON format.
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=500,
        )

        content = response.choices[0].message.content.strip()
        logger.debug(f"🧠 Next action response:\n{content}")

        action = self._parse_json(content)
        if isinstance(action, dict):
            logger.info(f"   ➡️  Next: {action.get('action')} → {action.get('target')} | {action.get('reasoning', '')}")
            return action
        else:
            logger.error("❌ Could not parse next action from LLM response")
            return {"action": "done", "target": "error", "value": "", "reasoning": "Failed to parse LLM response"}

    def replan_on_failure(
        self,
        request: str,
        failed_step: dict,
        error: str,
        history: list[dict],
    ) -> Optional[dict]:
        """
        Recovery: when a step fails, ask the LLM for an alternative approach.

        Args:
            request: Original user request
            failed_step: The step that failed
            error: Error message
            history: Previous successful steps

        Returns:
            Alternative action dict, or None if no recovery possible
        """
        logger.info(f"🔄 Replanning after failure: {error}")

        prompt = f"""
The following action FAILED during the IT automation task:

Task: "{request}"
Failed Action: {json.dumps(failed_step)}
Error: {error}

History of previous steps:
{json.dumps(history, indent=2)}

What is an alternative approach to recover from this failure and continue the task?
Output a SINGLE alternative action in JSON format.
If you cannot recover, output: {{"action": "done", "target": "failed", "value": "", "reasoning": "Cannot recover", "expected_outcome": "Task failed"}}
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=400,
        )

        content = response.choices[0].message.content.strip()
        action = self._parse_json(content)
        if isinstance(action, dict):
            logger.info(f"   🔄 Recovery action: {action.get('action')} → {action.get('target')}")
            return action
        return None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _parse_json(self, text: str) -> any:
        """
        Robustly parse JSON from LLM output.
        Handles markdown code blocks and stray text.
        """
        # Remove markdown fences if present
        text = re.sub(r"```(?:json)?\s*", "", text)
        text = re.sub(r"```", "", text)
        text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try extracting a JSON object/array from the text
            json_match = re.search(r"(\[[\s\S]*\]|\{[\s\S]*\})", text)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass

            logger.error(f"❌ JSON parse failed. Raw text:\n{text[:300]}")
            return {}
