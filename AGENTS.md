# Aegis — Project Context & Session Memory

## Project Overview
Aegis Engine v3.1.0 — Private AI Assistant (Email + Files + Data, self-learning, encrypted)
Python/Flask monolith with Jinja2 templates, SQLite storage, Ollama AI integration.

---

### [2026-07-10 19:20] — codeflow-analysis.json Issue Resolution Sprint
- **State**: Success
- **MCP Data Used**: code_tree for AST analysis, grep for usage verification, explore subagent for dead code confirmation
- **Agents Deployed**: explore (dead function verification)
- **Architectural Decisions**:
  1. **OS Command Injection**: Replaced `os.system()` with `subprocess.run()` in `notifications/notifier.py`
  2. **Hardcoded Secret**: Added security warning + placeholder guidance in `docs/DEPLOYMENT.md`
  3. **XSS Vulnerabilities**: Fixed 3 real XSS vectors in `assistant.html` (textContent instead of innerHTML), `email.html` (textContent for draft), `security.html` (DOM API for compliance checks)
  4. **Bare Except Clauses**: Replaced 3 bare `except:` with `except Exception:` in `simple_assistant.py`
  5. **Dead Code Removed**: 17 unused functions across 7 files (logging_config, metrics, notifications, auth, migrations, chat, rate_limit, session, demo_data)
  6. **Large File Split**: Extracted security/2FA/backup routes (8 fns) into `dashboard/security_routes.py` and settings/model routes (8 fns) into `dashboard/settings_routes.py`, reducing `app.py` from 43→27 functions and 977→660 lines
- **Tests**: 139/143 pass; 4 pre-existing environment-specific failures (RAM/disk/Ollama availability)
- **Remaining Known Issues**:
  - `learning/memory.py` (32 fns, 795 lines) — domain complexity, not worth splitting
  - Circular dependency detections were mostly false positives from static analysis
  - Architecture violation flags were false positives (Flask templates are meant to be rendered by views)
- **Next Turn Directive**: Run the dashboard (`python3 run_dashboard.sh`) to smoke-test the blueprint route registration, or begin work on new features
