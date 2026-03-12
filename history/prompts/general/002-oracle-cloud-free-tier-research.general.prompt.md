---
id: 002
title: Oracle Cloud Free Tier Deployment Research
stage: general
date: 2026-03-09
surface: agent
model: claude-opus-4-6
feature: none
branch: 002-silver-fte-foundation
user: user
command: research
labels: ["oracle-cloud", "deployment", "infrastructure", "free-tier", "odoo", "claude-code"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - history/prompts/general/002-oracle-cloud-free-tier-research.general.prompt.md
tests:
  - n/a
---

## Prompt

Research Oracle Cloud Free Tier for deploying a Python-based AI Employee system. I need VERIFIED facts only:

1. Search for Oracle Cloud Free Tier current offerings (VMs, specs, limits)
2. Can we run Python scripts 24/7 on Oracle Free Tier?
3. Can we run Odoo Community on Oracle Free Tier?
4. Can we install Claude Code on Oracle Free Tier VM?
5. What OS options are available?
6. Any restrictions or gotchas?
7. How to set up HTTPS on Oracle Free VM?

Use web search to verify current information. Do NOT hallucinate - only report what you can verify.

## Response snapshot

Comprehensive web-verified research covering all 7 questions. Key findings: Oracle Always Free tier provides ARM A1 instances (4 OCPUs, 24 GB RAM, 200 GB storage) indefinitely. Python 24/7 confirmed via systemd/cron. Odoo Community runs on ARM64 Docker. Claude Code native installer works on ARM Linux. Ubuntu 22.04 Minimal recommended. Major gotchas: ARM capacity shortages in popular regions, idle instance reclamation (<20% CPU over 7 days), dual firewall (OCI Security List + OS). HTTPS via Nginx + Let's Encrypt/Certbot is well-documented and free.

## Outcome

- Impact: Research complete - verified Oracle Cloud Free Tier is viable for full FTE system deployment at $0/month
- Tests: n/a (research task)
- Files: 1 PHR created
- Next prompts: Create Oracle Cloud deployment plan/spec, set up OCI account, provision ARM instance
- Reflection: All 7 questions answered with web-verified sources. ARM capacity availability is the main risk factor.

## Evaluation notes (flywheel)

- Failure modes observed: None - all searches returned relevant results
- Graders run and results (PASS/FAIL): n/a
- Prompt variant (if applicable): n/a
- Next experiment: Verify ARM instance availability in target region before committing to architecture
