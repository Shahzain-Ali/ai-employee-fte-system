# Platinum Tier — Requirements Checklist

**Feature**: 004-platinum-cloud-local
**Created**: 2026-03-09
**Status**: Pre-Implementation

---

## Cloud 24/7 Deployment

- [ ] **FR-001**: Oracle Cloud Free Tier ARM A1 VM provisioned with Ubuntu 22.04+, Python 3.12+, uv, Claude Code CLI
- [ ] **FR-002**: All services (watchers, orchestrator, health monitor) managed via PM2/systemd with auto-restart
- [ ] **FR-003**: All services auto-start on VM reboot
- [ ] **FR-004**: Claude Code headless mode (`claude -p` or `claude-agent-sdk`) working on cloud VM

## Work-Zone Specialization

- [ ] **FR-005**: Cloud Agent restricted to draft-only operations (no send/publish/confirm)
- [ ] **FR-006**: Local Agent handles all final actions (send, publish, WhatsApp, banking, dashboard)
- [ ] **FR-007**: Single-writer rule: only Local Agent writes Dashboard.md; Cloud writes to `/Updates/`
- [ ] **FR-008**: Sensitive credentials exist ONLY on Local machine, never on Cloud VM

## Git-Synced Vault

- [ ] **FR-009**: Git repo (GitHub private) syncs vault between Cloud and Local
- [ ] **FR-010**: Vault folder structure created: `/Needs_Action/`, `/In_Progress/`, `/Plans/`, `/Pending_Approval/`, `/Updates/`, `/Done/`, `/Logs/`
- [ ] **FR-011**: Claim-by-move rule implemented (first mover owns task)
- [ ] **FR-012**: Hybrid sync: event-based push (inotifywait/gitwatch) + timer-based pull (2-3 min)
- [ ] **FR-013**: Merge conflict auto-resolution strategy implemented

## Security (Vault Sync)

- [ ] **FR-014**: `.gitignore` configured BEFORE first sync (excludes `.env`, tokens, sessions, credentials, keys)
- [ ] **FR-015**: Only `.md`, `.json`, `.txt` files in Git history
- [ ] **FR-016**: Cloud and Local maintain independent `.env` files
- [ ] **FR-017**: Cloud VM SSH uses key-only authentication (no password)

## Odoo on Cloud

- [ ] **FR-018**: Odoo deployed on Cloud VM via Docker (docker-compose) with PostgreSQL
- [ ] **FR-019**: HTTPS enabled via Let's Encrypt + Nginx reverse proxy
- [ ] **FR-020**: Odoo MCP server URL updated to cloud HTTPS URL
- [ ] **FR-021**: Automatic daily database backups configured
- [ ] **FR-022**: Certbot auto-renewal configured via cron

## Health Monitoring

- [ ] **FR-023**: Health script checks Odoo, watchers, orchestrator, disk, RAM every 3-5 min
- [ ] **FR-024**: Auto-restart on failure (3 retries), then alert on repeated failure
- [ ] **FR-025**: All health checks logged with timestamp

## Local Agent Auto-Start

- [ ] **FR-026**: Windows Task Scheduler starts WSL + orchestrator on login
- [ ] **FR-027**: Orchestrator runs in background (no visible terminal)
- [ ] **FR-028**: Immediate `git pull` and pending approval check on startup

## Platinum Demo (Minimum Passing Gate)

- [ ] **FR-029**: End-to-end flow works: email → cloud draft → sync → local approve → send → log → done
- [ ] **FR-030**: Every step verifiable through audit logs with timestamps

---

## Success Criteria Validation

- [ ] **SC-001**: Platinum Demo works 3/3 times with laptop OFF during email receipt
- [ ] **SC-002**: Cloud VM runs 48+ hours without manual intervention
- [ ] **SC-003**: Vault sync delivers changes within 5 minutes
- [ ] **SC-004**: Cloud Agent zero send/publish actions in 24-hour audit
- [ ] **SC-005**: Local auto-start within 60 seconds on 3 cold boots
- [ ] **SC-006**: Health monitor recovers crashed component within 5 minutes
- [ ] **SC-007**: Odoo HTTPS with valid SSL certificate
- [ ] **SC-008**: Zero sensitive files in Git history
- [ ] **SC-009**: Claim-by-move prevents duplicate processing
- [ ] **SC-010**: 24-hour laptop-off accumulation syncs correctly

---

## Pre-Implementation Setup

- [ ] Oracle Cloud Free Tier account created
- [ ] ARM A1 VM provisioned (4 OCPUs, 24GB RAM, Ubuntu 22.04+)
- [ ] SSH key pair generated and configured
- [ ] GitHub private repo for vault sync created
- [ ] GitHub SSH key added to Cloud VM
- [ ] Domain pointed to VM IP (optional, for Let's Encrypt)
- [ ] Anthropic API key available for Cloud VM
- [ ] Windows Task Scheduler can trigger WSL commands
