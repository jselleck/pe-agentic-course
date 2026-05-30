"""
shared/verify_setup.py
----------------------
Pre-flight check for the course environment.
Run before any module exercise: python shared/verify_setup.py
"""

import sys
import os
import subprocess
import importlib.util


REQUIRED_PYTHON = (3, 10)
REQUIRED_PACKAGES = ["anthropic", "openai"]


def check_python():
    v = sys.version_info
    ok = v >= REQUIRED_PYTHON
    status = "✅" if ok else "❌"
    print(f"{status} Python {v.major}.{v.minor}.{v.micro}  (need ≥ {REQUIRED_PYTHON[0]}.{REQUIRED_PYTHON[1]})")
    return ok


def check_api_keys():
    provider = os.environ.get("AI_PROVIDER", "auto").lower()
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
    openai_key = os.environ.get("OPENAI_API_KEY", "")

    anthropic_ok = bool(anthropic_key and anthropic_key.startswith("sk-"))
    openai_ok = bool(openai_key and openai_key.startswith("sk-"))

    def print_key(name, ok, hint):
        status = "✅" if ok else "❌"
        suffix = "" if ok else f"  → Set with: {hint}"
        print(f"{status} {name}{suffix}")

    print_key("ANTHROPIC_API_KEY", anthropic_ok, "export ANTHROPIC_API_KEY=your_key_here")
    print_key("OPENAI_API_KEY", openai_ok, "export OPENAI_API_KEY=your_key_here")
    print(f"ℹ️  AI_PROVIDER={provider}  (use anthropic, openai, or both)")

    if provider in ("both", "compare", "comparison"):
        return anthropic_ok and openai_ok
    if provider in ("openai", "codex"):
        return openai_ok
    if provider in ("anthropic", "claude"):
        return anthropic_ok
    return anthropic_ok or openai_ok


def check_packages():
    all_ok = True
    for pkg in REQUIRED_PACKAGES:
        found = importlib.util.find_spec(pkg) is not None
        status = "✅" if found else "❌"
        hint = "" if found else f"  → Install with: pip install {pkg}"
        print(f"{status} {pkg}{hint}")
        all_ok = all_ok and found
    return all_ok


def check_gh_cli():
    try:
        result = subprocess.run(
            ["gh", "--version"],
            capture_output=True, text=True, timeout=5
        )
        ok = result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        ok = False
    status = "✅" if ok else "⚠️ "
    hint = "" if ok else " (optional — needed for GitHub Issue exercises)"
    print(f"{status} GitHub CLI (gh){hint}")
    return True  # Non-blocking — gh is optional for early modules


def main():
    print("=" * 50)
    print("  Agentic AI in Platform Engineering — Setup Check")
    print("=" * 50)
    results = [
        check_python(),
        check_api_keys(),
        check_packages(),
        check_gh_cli(),
    ]
    print("=" * 50)
    if all(results):
        print("✅  All checks passed. You're ready to run the exercises.")
    else:
        print("❌  One or more checks failed. Fix the issues above and re-run.")
        sys.exit(1)


if __name__ == "__main__":
    main()
