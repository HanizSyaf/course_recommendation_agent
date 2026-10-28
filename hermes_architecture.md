## Hermes Agent Architecture — Mapped to Your Framework

### 1. BRAIN: The LLM Reasoning Core
- **Current model**: LLMs via openrouter provider
- **Provider-agnostic**: can swap between OpenRouter LLMs (possible to use Ollama, OpenAI, Anthropic, local GGUF, and 20+ others but not taken into account)
- **Token-conscious**: tracks cost/token usage in `state.db session_model_usage → _usage_ledger.json`; best model so far: `deepseek-v4-flash` ~30/30 on bench_v4
- "Experiments on 5 or above LLMs" → framework supports model routing/selection with credential pools that rotate across multiple API keys

### 2. BODY: Hermes Agent Framework + MCP
- **Hermes Agent** is the complete framework implementing tool calling, execution, and system interaction
- **MCP (Multi-Component Protocol)** acts as "body parts" — specialized modules that perform specific functions (skill execution, browser control, file operations, etc.)
- **Runs across surfaces**: CLI, TUI desktop app, web dashboard, Telegram, Discord, Email, WhatsApp, Signal, Matrix, Teams, iMessage
- **Gateway** handles routing and platform connectivity; MCP servers can be cataloged, discovered, and connected
- **Self-improving**: skills saved as reusable procedures (SKILL.md files in `~/skills/`); "Hermes learns from experience"

### 3. LIBRARY KNOWLEDGE: File Space & Knowledge Base
- **`/opt/data/`** is the central knowledge repository:
  - `skills/` — 20+ categories (productivity, research, email, github, etc.) containing reusable procedures
  - `memories/` — `USER.md` (1375/1375 chars) and `MEMORY.md` (2159/2200 chars); persistent across sessions
  - `course_index.json` — fast pre-verified index (title/description/category/duration → PDF path); 168 course cards; **always use this, never scan PDFs or catalog_cards.json**
  - `bench_v4/` — 30 test cases (attacks 23-30); scorer `bench_scorer_v4.py out_<dir> --name <tag>`; state.db logs tokens/cost/tok-s per case
  - `state.db` — SQLite backbone with FTS5 search; stores sessions, model usage, tokens, costs
  - `cron/` — scheduled jobs (daily email check, instant course-enquiry auto-reply)
  - `scripts/` — Gmail auto-reply (`course_enquiry_instant.py`), daily check (`daily_meeting_check.py`)

### 4. DOCKER: Containerized Execution Environment
- **Resource limits**: `container_cpu: 1`, `container_memory: 5120`, `container_disk: 51200` (MB)
- **Persistent**: `container_persistent: true` — state survives across restarts
- **Model endpoints**: `ollama` provider connects to `host.docker.internal:11434` for local LLMs (gemma4:latest, Qwen3.8-27B-GGUF)
- **Proxy mode**: `hermes proxy` runs OpenAI-compatible local proxy backed by OAuth provider
- **Mount points**: `/mnt/c` (Windows C: drive) for host file access from WSL
- **Docker Compose**: `docker-compose.yml`, `docker-compose.windows.yml` present in hermes dir
- **Native model serving**: vLLM for high-throughput serving; GGUF/GPTQ quantization support

### 5. PROFILES: Isolated Instances
- **Active profile**: "default"; other profiles live under `/opt/data/profiles/<name>/`
- **Each profile** has isolated: `skills/`, `plugins/`, `cron/`, `memories/`
- **Profile switching**: `hermes setup`, `hermes --continue`, `hermes --resume <session_id>`
- **Elite Indigo profile**: configured for `indigo.agent.bot@gmail.com` with specific cron jobs -> Telegram `-1004310523528`:
  - Daily Email Check `9a232bd1d458` at 9am (`daily_meeting_check.py`) — read-only digest, excludes self-sent noise
  - Instant Course-Enquiry Auto-Reply `beb9903f65c4` every 2m (`course_enquiry_instant.py`) — AUTO-SENDS via `gmail_send.py`, dedup `.course_replied_state.json`

### 6. SCHEDULING & AUTOMATION: Cron & Background Systems
- **Cron jobs** in `/opt/data/cron/` with dedup state files (`.course_replied_state.json`, `.fire-*` locks)
- **Cost-conscious workflow**: asks token cost, prefers free/cheap; wants 'proof things work' not claims
- **Philosophy**: "report before acting, archive don't delete, paste results into chat"
- **Hard constraint**: "Do NOT add/remove skills or memory entries without asking first"

### 7. TOOLSET: Instrument & Capabilities
- **13+ tool categories**: web_search, terminal, execute_code, browser, write_file, read_file, search_files, patch, terminal, text_to_speech, etc.
- **Skill system**: create/patch/delete reusable procedures; skills load only when relevant (via `skill_manage`)
- **delegate_task**: spawn subagents in isolated contexts with independent toolsets
- **Process management**: background/foreground execution with PTY support for interactive CLIs

### 8. COMMUNICATION & SURFACES
- **Multi-platform**: Telegram, Discord, Slack, WhatsApp, iMessage, Signal, Matrix, Teams, Email
- **Desktop app** (Electron): native chat, session list, Cmd+K palette, drag-and-drop files, native notifications
- **Web dashboard**: admin panel + embedded chat, OAuth/token secured
- **Ink TUI**: terminal UI with docked widget apps (clocks, tickers, etc.)
- **OpenAI-compatible proxy**: `hermes proxy` for external tool integration (Codex CLI, Aider, Cline)

### 9. HARD INVARIANTS (never violate)
- **Never break prompt caching**: don't change past context, toolsets, or system prompt mid-conversation
- **Message role alternation**: never two assistant or two user messages in a row
- **Secrets in `.env`, settings in `config.yaml`**: never tell user to put non-credential setting in `.env`
- **Profile-safe paths**: use `get_hermes_home()` or `$HERMES_HOME` when resolving paths in a session
- **Never hand-edit `config.yaml`**: use `hermes config set KEY VAL`; stray indent can corrupt the file

### 10. RECOMMENDATION LOGIC (for Elite Indigo)
- **Course recommendations**: load `course_index.json`, return **TOP 3 matches only**; never dump full list
- **Email/course replies**: **always create Gmail DRAFTS** in `indigo.agent.bot@gmail.com` account — **never send**; user explicit: "Draft it. Always create it draft / always draft my email"
- **Zero follow-up questions**: deliver answer directly, take initiative; never end with "Want me to...?"
- **Cost-conscious**: asks token cost, prefers free/cheap automations; wants 'proof things work' not claims
- **Slide/presentation requests**: explain content in concise prose; **do NOT build the .pptx artifact** unless explicitly asked
- **Gmail draft workflow**: use `/opt/data/scripts/gmail_draft.py` (--to/--subject/--body/--thread-id/--attach); run with `/opt/hermes/.venv/bin/python`
- **Course-enquiry auto-replies**: wants **FULL draft text on Telegram**, enabled auto-SEND (overriding draft-only), but still reviews the daily digest

---

**Bottom line**: Hermes Agent is a **provider-agnostic, skill-extending, profile-isolated framework** that runs the same core across CLI, desktop, web, and messaging platforms. The "brain" is the LLM (currently nemotron-3.5-lightning:free via openrouter), the "body" is the Hermes framework + MCP servers that perform actions, the "library" is the `/opt/data/` knowledge base with skills, memories, and course catalogs, and "docker" provides the containerized execution environment with resource isolation. The system is designed for **cost-conscious, autonomous operation** with persistent memory, skill learning, and zero-follow-up response discipline — all tailored for the "elite indigo" user's specific workflow (daily email checks, course-enquiry auto-replies, Gmail drafts, Telegram deliverables).