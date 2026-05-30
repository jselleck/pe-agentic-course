# Agentic AI in Platform Engineering
### A PlatformEngineering.org course

This repository contains the hands-on exercise code for every module of the course. Each `moduleN/` directory is self-contained: one agent script, one sample data file, one config, and a README with the exercise brief.

---

## Quick Start

```bash
# 1. Fork the repo first (required for GitHub Actions secrets)
#    Go to https://github.com/InternalDeveloperPlatform/pe-agentic-course and click Fork

# 2. Clone YOUR fork
git clone https://github.com/YOUR_USERNAME/pe-agentic-course.git
cd pe-agentic-course

# 2. Set one or both API keys
export ANTHROPIC_API_KEY=sk-ant-...
# export OPENAI_API_KEY=sk-...

# 3. Pick the live provider when you run without --mock
#    Options: anthropic, openai, both
export AI_PROVIDER=anthropic

# 4. Verify your environment
python shared/verify_setup.py

# 5. Run a module exercise (example: Module 2)
python module2/agent.py
```

---

## Repository Structure

```
.
├── shared/                     # Common utilities — do not modify
│   ├── claude_client.py        # ask() compatibility shim
│   ├── llm_client.py           # ask() function — Anthropic/OpenAI/compare
│   ├── output.py               # JSON, Step Summary, and GitHub Issue formatters
│   └── verify_setup.py         # Pre-flight environment check
│
├── module1/                    # Module 1: Platform Pain Points & The AI Opportunity
├── module2/                    # Module 2: Build Your First AI Agent
├── module3/                    # Module 3: Agents That Think — ReAct & Planning
├── module4/                    # Module 4: AI-Powered Diagnosis and Remediation
├── module5/                    # Module 5: Intelligent CI/CD and Adaptive Delivery
├── module6/                    # Module 6: Operational Intelligence & Conversational Observability
├── module7/                    # Module 7: Multi-Agent Coordination & Implementation Strategy
├── module8/                    # Module 8: Capstone — Build Your Platform Engineering Agent
│
├── .github/workflows/          # One CI workflow per module
│   ├── module1-hello-agent.yml
│   ├── module2-first-agent.yml
│   └── ...
├── .gitlab-ci.yml              # GitLab CI jobs for the same module runs
│
├── output/                     # Agent output JSON from previous runs (for comparison)
└── docs/                       # Architecture diagrams and reference guides
```

## Files in Every Module Directory

| File | Purpose |
|------|---------|
| `agent.py` or `triage_agent.py` | Main agent script — the exercise entry point |
| `sample_log.txt` or `sample_data.json` | Realistic test data for the exercise |
| `agent-config.yml` | Scenario config: model, max_iterations, context fields |
| `README.md` | Exercise brief, setup instructions, success criteria |

---

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | ≥ 3.10 | |
| anthropic SDK | latest | Installed by `pip install -r requirements.txt` |
| openai SDK | latest | Installed by `pip install -r requirements.txt` |
| GitHub CLI (`gh`) | any | Optional — needed for Modules 7–8 |
| ANTHROPIC_API_KEY | — | Required for `AI_PROVIDER=anthropic` or `both` |
| OPENAI_API_KEY | — | Required for `AI_PROVIDER=openai` or `both` |
| AI_PROVIDER | `auto` | `anthropic`, `openai`, or `both` |

## Provider Modes

The exercises still call one helper: `ask(system, user, model, max_tokens)`.
Choose the live backend with `AI_PROVIDER`:

```bash
AI_PROVIDER=anthropic python module2/triage_agent.py
AI_PROVIDER=openai python module2/triage_agent.py
AI_PROVIDER=both python module2/triage_agent.py
```

`AI_PROVIDER=both` runs the same prompt against both providers and saves a
side-by-side JSON result. If `AI_PROVIDER` is unset, the client uses OpenAI only
when `OPENAI_API_KEY` is set and `ANTHROPIC_API_KEY` is not; otherwise it keeps
the original Anthropic default.

---

## GitHub Actions

Each module has a corresponding workflow in `.github/workflows/`. Workflows trigger on push to the relevant `moduleN/**` path and run the agent against the sample data. Output JSON is uploaded as an artifact for comparison.

To enable CI for your fork: add `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, or both as repository secrets in **Settings → Secrets and variables → Actions**. To compare both in CI, add a repository variable named `AI_PROVIDER` with the value `both`.

## GitLab CI

The root `.gitlab-ci.yml` runs the same module agents in GitLab without sharing
or generating config from GitHub Actions. Jobs run automatically when their
module path or `shared/**` changes, and they can also be started manually from
GitLab's **Run pipeline** page.

Add `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, and optional `AI_PROVIDER` as GitLab
CI/CD variables. If no provider key is set, jobs fall back to `MOCK_MODE=1`.
Outputs are uploaded as GitLab job artifacts from `output/*.json` and
`output/*.md`.

---

## Module Progression

Each module's exercise builds on the previous. By Module 8 you have a fully assembled production agent — every component built in Modules 1–7 is integrated into the capstone.

| Module | Topic | Key Output |
|--------|-------|-----------|
| 1 | Hello Agent | First Claude API call, parse JSON |
| 2 | First AI Agent | Five-step agentic loop |
| 3 | ReAct & Planning | Multi-step iterative reasoning |
| 4 | Diagnosis & Remediation | Event-driven triage agent |
| 5 | Intelligent CI/CD | Quality gate with release decision |
| 6 | Conversational Observability | Natural-language ops queries |
| 7 | Multi-Agent Coordination | Orchestrator + specialist routing |
| 8 | Capstone | Full production agent pipeline |
