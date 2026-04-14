"""
CLI Entry Point for the IT Support Agent
=========================================
Usage:
    python run_agent.py "reset password for john@company.com"
    python run_agent.py "create user alice@company.com and assign pro license"
    python run_agent.py --headless "assign enterprise license to jane@company.com"

The script:
1. Validates the Groq API key is set
2. Starts the agent with a visible or headless browser
3. Prints a detailed summary of actions taken
4. Exits with code 0 on success, 1 on failure
"""

import argparse
import json
import os
import sys

# Force UTF-8 output on Windows to support emoji characters
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")

from dotenv import load_dotenv

# Load .env file first (before any imports that need GROQ_API_KEY)
load_dotenv(override=True)


def validate_environment():
    """Ensure all required environment variables are present."""
    missing = []
    if not os.getenv("GROQ_API_KEY"):
        missing.append("GROQ_API_KEY")

    if missing:
        print("❌ Missing required environment variables:")
        for var in missing:
            print(f"   - {var}")
        print("\nCreate a .env file with these values. See .env.example for reference.")
        sys.exit(1)


def print_result(result: dict):
    """Pretty-print the agent execution result."""
    print("\n" + "=" * 65)
    status = "✅ SUCCESS" if result["success"] else "❌ FAILED"
    print(f"  {status}")
    print("=" * 65)
    print(f"  Request    : {result['request']}")
    print(f"  Summary    : {result['summary']}")
    print(f"  Steps taken: {result['steps_taken']}")
    print(f"  Duration   : {result['duration_seconds']}s")
    print(f"  Session ID : {result['session_id']}")
    print(f"  Log dir    : {result['log_dir']}")

    print("\n📋 Action Log:")
    for i, action in enumerate(result.get("actions", []), 1):
        act_name = action.get("action", "?")
        target = action.get("target", "")
        obs = action.get("result", {}).get("observation", "")
        ok = "✅" if action.get("result", {}).get("success") else "❌"
        print(f"  {i:2d}. {ok} [{act_name}] {target[:50]} → {obs[:60]}")

    print("=" * 65 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Agentic AI IT Support Automation System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_agent.py "reset password for john@company.com"
  python run_agent.py "create user alice@company.com with name Alice Johnson and assign pro license"
  python run_agent.py --headless "assign enterprise license to jane@company.com"
  python run_agent.py --model llama-3.1-8b-instant "reset password for john@company.com"
        """,
    )

    parser.add_argument(
        "request",
        type=str,
        help='Natural language IT task (e.g., "reset password for john@company.com")',
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        default=False,
        help="Run browser in headless mode (no visible window)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="llama-3.3-70b-versatile",
        help="Groq model to use (default: llama-3.3-70b-versatile)",
    )
    parser.add_argument(
        "--log-dir",
        type=str,
        default="logs",
        help="Directory to save action logs and screenshots (default: logs/)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Output result as JSON instead of formatted text",
    )

    args = parser.parse_args()

    # Validate environment before anything else
    validate_environment()

    print(f"\n🤖 Agentic AI IT Support System")
    print(f"   Request  : {args.request}")
    print(f"   Model    : {args.model}")
    print(f"   Headless : {args.headless}")
    print(f"   Log dir  : {args.log_dir}")
    print(f"\nMake sure the backend is running: uvicorn backend.main:app --reload")
    print("-" * 65)

    # Import here to avoid circular imports and ensure env is loaded
    from agent.agent import ITSupportAgent
    import asyncio

    agent = ITSupportAgent(
        headless=args.headless,
        log_dir=args.log_dir,
        groq_model=args.model,
    )

    result = asyncio.run(agent.run(args.request))

    if args.json:
        # JSON output mode — useful for piping to other tools
        print(json.dumps(result, indent=2, default=str))
    else:
        print_result(result)

    # Exit code reflects success/failure
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
