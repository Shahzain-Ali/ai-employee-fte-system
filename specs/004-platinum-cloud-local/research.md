# Research: Platinum Tier — Always-On Cloud + Local Executive

**Feature**: 004-platinum-cloud-local
**Date**: 2026-03-09
**Status**: Complete

---

## R-001: Claude Code on Cloud VM (ARM64)

### Decision: Claude Code CLI + Agent SDK (Python)

### Findings

**Claude Code CLI Headless Mode:**
- Command: `claude -p "prompt"` — the `-p` (or `--print`) flag runs non-interactively
- Output formats: `--output-format text` (default), `json`, `stream-json`
- Tool control: `--allowedTools "Read,Edit,Bash"` for auto-approval
- Continue conversations: `--continue` or `--resume <session_id>`
- System prompt: `--append-system-prompt "instructions"`
- Source: https://code.claude.com/docs/en/headless

**Claude Agent SDK (Python):**
- Install: `pip install claude-agent-sdk`
- CLI is automatically bundled — no separate Claude Code install needed
- Two usage modes:
  - `query()` — one-off tasks, no conversation history
  - `ClaudeSDKClient` — stateful conversations, custom tools, hooks
- Custom tools can be Python functions (in-process MCP servers)
- Source: https://pypi.org/project/claude-agent-sdk/
- GitHub: https://github.com/anthropics/claude-agent-sdk-python

**ARM64 Compatibility:**
- Known issues with ARM64 native installer (GitHub issue #27405)
- Workaround: Authenticate on x86_64, copy credentials to ARM64
- Alternative: Use `claude-agent-sdk` Python package (bundles CLI)
- Node.js 18+ required (recommended: Node.js 22 LTS)
- Source: https://github.com/anthropics/claude-code/issues/27405

### Rationale
Use `claude-agent-sdk` Python package as primary method — it bundles Claude Code CLI,
avoids ARM64 installer issues, and provides programmatic Python control matching our
existing Python codebase. Fall back to `claude -p` for simple one-off tasks.

### Alternatives Considered
| Alternative | Why Rejected |
|------------|-------------|
| Claude Code native installer on ARM64 | Known auth issues on ARM64 |
| Direct Anthropic API calls | Loses Claude Code's tool use, agent loop, context management |
| OpenAI/other LLM | Hackathon requires Claude Code as reasoning engine |

---

## R-002: Git Sync Between Cloud and Local

### Decision: gitwatch (push) + cron git pull (pull)

### Findings

**gitwatch (github.com/gitwatch/gitwatch):**
- Bash script that watches files/directories and auto-commits on change
- Uses `inotifywait` (from `inotify-tools` package) on Linux
- Command: `gitwatch -r origin -b main /path/to/vault`
- 2-second delay after change before commit (prevents race conditions)
- Recursive directory watching (all subdirectories included)
- `.git/` directory auto-excluded from monitoring
- Can run as systemd user service for persistence
- Installation: `git clone + install -b gitwatch.sh /usr/local/bin/gitwatch`
- Source: https://github.com/gitwatch/gitwatch

**Timer-Based Pull (cron):**
- Simple cron job: `*/3 * * * * cd /path/to/vault && git pull --rebase origin main`
- Every 3 minutes, pull remote changes
- `--rebase` avoids unnecessary merge commits
- Conflict resolution: `git pull --rebase --strategy-option=theirs` for auto-accept remote

**Hybrid Approach (chosen):**
- **Push side**: gitwatch with inotifywait — pushes within seconds of file change
- **Pull side**: cron job every 2-3 minutes — checks for remote updates
- Both Cloud and Local run both push and pull
- Result: ~1-3 minute sync latency in worst case

**Dependencies:**
- `inotify-tools` package (provides `inotifywait`)
- `git` (already needed)
- `cron` (standard on Ubuntu)

### Rationale
gitwatch is battle-tested, simple, and uses inotifywait for efficient file watching.
Combined with cron pull, it provides near-real-time sync without wasteful constant
polling. Both are standard Linux tools with zero maintenance overhead.

### Alternatives Considered
| Alternative | Why Rejected |
|------------|-------------|
| simonthum/git-sync | Less maintained, fewer features than gitwatch |
| Syncthing | Cannot safely sync .git/ directories |
| rsync + cron | No version control, no conflict detection |
| Custom Python watchdog script | Reinventing the wheel; gitwatch already does this |
| Webhook-based (GitHub Actions → SSH) | Adds complexity, requires webhook endpoint |

---

## R-003: Oracle Cloud Free Tier ARM A1

### Decision: Oracle Cloud Free Tier ARM A1 (4 OCPUs, 24GB RAM)

### Findings

**Always Free Specs (verified 2026):**
- Shape: VM.Standard.A1.Flex (Ampere ARM)
- OCPUs: Up to 4 (total across all A1 instances)
- RAM: Up to 24 GB (total across all A1 instances)
- Can be 1 instance (4 OCPU, 24GB) or split across up to 4 instances
- Boot volume: 50 GB default (200 GB total combined)
- Network: 50 Mbps internet, 480 Mbps private
- Outbound: 10 TB/month
- OS: Ubuntu 22.04+ (Canonical image available)
- Source: https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm

**Provisioning Gotchas:**
- ARM A1 instances may show "Out of capacity" in popular regions
- Workaround: Try different regions or retry at off-peak hours
- Some users report needing multiple attempts over days
- Source: https://lowendspirit.com/discussion/6130/oracle-cloud-free-arm-instances

**Security Setup:**
- SSH key-only: Edit `/etc/ssh/sshd_config` → `PasswordAuthentication no`
- fail2ban: `apt install fail2ban` (default SSH jail active)
- Firewall: Oracle Cloud Security Lists (VCN-level) + `ufw`
- Open ports: 22 (SSH), 80 (HTTP), 443 (HTTPS), 8069 (Odoo, optional)

**Software Stack on ARM64 Ubuntu:**
- Docker: `apt install docker.io docker-compose-v2` (ARM64 native)
- Node.js 22 LTS: `curl -fsSL https://deb.nodesource.com/setup_22.x | bash -`
- Python 3.12+: Available via `apt` or `deadsnakes` PPA
- uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- PM2: `npm install -g pm2` then `pm2 startup` for auto-start
- Nginx: `apt install nginx`
- certbot: `apt install certbot python3-certbot-nginx`

### Rationale
4 OCPUs + 24GB RAM is MORE than sufficient for Odoo + watchers + Claude Code.
Forever free means zero ongoing cost. ARM64 is well-supported by Docker, Node.js,
Python, and all our dependencies.

### Alternatives Considered
| Alternative | Why Rejected |
|------------|-------------|
| AWS EC2 Free Tier | Only 1 year free, t2.micro too small (1GB RAM) |
| Google Cloud Free | f1-micro too small (0.6GB RAM) |
| Azure Free | B1S too small (1GB RAM) |
| Self-hosted (home server) | Requires port forwarding, static IP, power costs |
| Raspberry Pi | Similar ARM but requires hardware purchase, home internet |

---

## R-004: Odoo on ARM64 Docker

### Decision: Official arm64v8/odoo Docker image

### Findings

- Official ARM64 image: `arm64v8/odoo` on Docker Hub
- Nightly builds for each Odoo version
- Compatible with standard docker-compose setup
- Port 8069 (default)
- Config mount: `/etc/odoo`
- Addons mount: `/mnt/extra-addons`
- Works with PostgreSQL ARM64 image
- Source: https://hub.docker.com/r/arm64v8/odoo/

**HTTPS Setup (Nginx + Let's Encrypt):**
- Nginx reverse proxy: proxy_pass to localhost:8069
- certbot: `certbot --nginx -d odoo.yourdomain.com`
- Auto-renewal: certbot adds cron job automatically
- If no domain: self-signed cert with `openssl req -x509`

**Backup Strategy:**
- `pg_dump` for PostgreSQL database (daily cron)
- Filestore backup: `/var/lib/odoo/filestore/` (daily rsync/tar)
- Retention: Keep 7 daily + 4 weekly backups

### Rationale
Official ARM64 image ensures compatibility and regular updates. Same docker-compose
approach as Gold tier, just different image tag and cloud deployment.

---

## R-005: Process Management (PM2 vs systemd)

### Decision: PM2 for application processes

### Findings

**PM2:**
- Install: `npm install -g pm2`
- Start: `pm2 start ecosystem.config.js`
- Auto-restart on crash: built-in
- Startup: `pm2 startup` + `pm2 save` — survives reboots
- Logs: `pm2 logs` — centralized logging
- Monitor: `pm2 monit` — real-time dashboard
- Ecosystem file: single config for all processes

**systemd:**
- Native to Ubuntu, no installation needed
- More complex unit file creation
- Better for system-level services
- Less convenient for multi-process app management

### Rationale
PM2 is simpler for managing multiple application processes (watchers, orchestrator,
health monitor) from a single config file. systemd used only for Docker and Nginx
(system services). Constitution mentions PM2 as an option.

---

## R-006: Local Auto-Start (Windows Task Scheduler + WSL)

### Decision: Windows Task Scheduler → WSL bash → orchestrator

### Findings

**Setup:**
1. Create a `.bat` or `.vbs` script that runs: `wsl -d Ubuntu -- bash -c "/path/to/start-local.sh"`
2. Add to Task Scheduler: Trigger = "At log on", Action = run the script
3. The start script: `cd /vault && git pull && python -m orchestrator.local_orchestrator &`

**Background Execution:**
- Use `.vbs` script with `WScript.Shell.Run` (hidden window) to avoid terminal popup
- WSL process runs invisibly in background
- Alternative: `wsl --exec` for direct command execution

### Rationale
Windows Task Scheduler is the native way to run tasks on login. Combined with WSL,
it provides seamless auto-start without requiring the user to open any terminal.
