"""
shared/output.py
----------------
Format agent output as JSON, CI summary markdown, and issue body text.
Used by all module agent scripts.
"""

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path


def save_json(result: dict, module: int, label: str = "output") -> Path:
    """
    Write result to output/<label>_moduleN.json.
    Returns the file path.
    """
    out_dir = Path(__file__).parent.parent / "output"
    out_dir.mkdir(exist_ok=True)
    filename = out_dir / f"{label}_module{module}.json"
    with open(filename, "w") as f:
        json.dump(result, f, indent=2)
    print(f"[output] Saved → {filename}")
    return filename


def to_step_summary(result: dict, title: str = "Agent Result") -> str:
    """
    Format result as CI summary markdown.
    Writes to $GITHUB_STEP_SUMMARY on GitHub Actions, and to output/*.md on
    GitLab CI so it can be uploaded as an artifact.
    Returns the markdown string in all cases.
    """
    _MAX_CELL = 120   # characters — keeps table rows readable in the GitHub UI

    def _comparison_summary() -> str | None:
        providers = ("anthropic", "openai")
        if not all(provider in result for provider in providers):
            return None
        if not all(isinstance(result.get(provider), dict) for provider in providers):
            return None

        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        lines = [
            f"## {title}",
            f"_Generated: {ts}_",
            "",
            "| Provider | Status | Model | Summary | Confidence | Error |",
            "|----------|--------|-------|---------|------------|-------|",
        ]
        for provider in providers:
            entry = result[provider]
            payload = entry.get("result") if isinstance(entry.get("result"), dict) else {}
            summary = payload.get("summary", payload.get("diagnosis", payload.get("recommended_action", "")))
            confidence = payload.get("confidence", "")
            error = entry.get("error", "")
            lines.append(
                "| {provider} | {status} | {model} | {summary} | {confidence} | {error} |".format(
                    provider=provider,
                    status=entry.get("status", ""),
                    model=entry.get("model", ""),
                    summary=_format_val(summary),
                    confidence=_format_val(confidence),
                    error=_format_val(error),
                )
            )
        return "\n".join(lines)

    def _format_val(v) -> str:
        if isinstance(v, bool):
            return str(v)
        if isinstance(v, (dict, list)):
            s = json.dumps(v)
            return s[:_MAX_CELL] + "…" if len(s) > _MAX_CELL else s
        s = str(v)
        return s[:_MAX_CELL] + "…" if len(s) > _MAX_CELL else s

    def _write_ci_summary(md: str) -> None:
        summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary_path:
            with open(summary_path, "a") as f:
                f.write(md + "\n\n")

        if os.environ.get("GITLAB_CI"):
            out_dir = Path(__file__).parent.parent / "output"
            out_dir.mkdir(exist_ok=True)
            slug = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
            summary_file = out_dir / f"summary_{slug or 'agent_result'}.md"
            summary_file.write_text(md + "\n")
            print(f"[output] Summary saved → {summary_file}")

    comparison_md = _comparison_summary()
    if comparison_md:
        _write_ci_summary(comparison_md)
        return comparison_md

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"## {title}",
        f"_Generated: {ts}_",
        "",
        "| Field | Value |",
        "|-------|-------|",
    ]
    for k, v in result.items():
        # Skip large raw-data blobs from the summary table
        if k == "raw_platform_data":
            lines.append(f"| `{k}` | _(omitted — see output JSON)_ |")
            continue
        val = _format_val(v)
        lines.append(f"| `{k}` | {val} |")

    md = "\n".join(lines)

    _write_ci_summary(md)

    return md


def to_github_issue(result: dict, module: int) -> str:
    """
    Format result as a GitHub Issue body.
    Returns the markdown string.
    """
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    confidence = result.get("confidence", "UNKNOWN")
    action = result.get("recommended_action", result.get("action", "N/A"))
    reasoning = result.get("reasoning", result.get("diagnosis", ""))
    escalate = result.get("escalate", False)

    emoji = "🔴" if escalate else "🟢"

    body = f"""## {emoji} Agent Diagnosis — Module {module}

**Timestamp:** {ts}
**Confidence:** `{confidence}`
**Escalate:** `{escalate}`

### Recommended Action
{action}

### Reasoning
{reasoning}

### Full Output
```json
{json.dumps(result, indent=2)}
```

---
_Written by Ajay · ajay@platformetrics.com · ajay@platformengineering.org_
"""
    return body
