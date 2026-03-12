# Quickstart: Platinum Tier Setup

**Feature**: 004-platinum-cloud-local
**Date**: 2026-03-09

---

## Prerequisites

- [ ] Gold Tier fully implemented and working
- [ ] Oracle Cloud Free Tier account (https://cloud.oracle.com)
- [ ] GitHub private repository for vault sync
- [ ] SSH key pair (for Cloud VM access)
- [ ] Domain name (optional, for Odoo HTTPS with Let's Encrypt)
- [ ] Anthropic API key for Cloud VM

---

## Phase 1: Cloud VM Setup

### 1.1 Provision Oracle Cloud ARM A1

```bash
# Via Oracle Cloud Console:
# Compute → Instances → Create Instance
# Image: Canonical Ubuntu 22.04 (aarch64)
# Shape: VM.Standard.A1.Flex (4 OCPUs, 24GB RAM)
# Network: Create new VCN with public subnet
# SSH: Upload your public key
```

### 1.2 Initial VM Configuration

```bash
# SSH into VM
ssh -i ~/.ssh/id_ed25519 ubuntu@<VM_PUBLIC_IP>

# Update system
sudo apt update && sudo apt upgrade -y

# Install essentials
sudo apt install -y git curl wget build-essential inotify-tools fail2ban nginx

# Disable password login
sudo sed -i 's/PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl restart sshd

# Install Docker
sudo apt install -y docker.io docker-compose-v2
sudo usermod -aG docker ubuntu
newgrp docker

# Install Node.js 22 LTS
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo bash -
sudo apt install -y nodejs

# Install PM2
sudo npm install -g pm2

# Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Claude Agent SDK
pip install claude-agent-sdk
```

### 1.3 Configure Firewall

```bash
# Oracle Cloud Security List (via Console):
# Allow: 22 (SSH), 80 (HTTP), 443 (HTTPS)

# Ubuntu firewall
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

---

## Phase 2: Vault Sync Setup

### 2.1 Configure Git on Cloud VM

```bash
# Generate SSH key for GitHub
ssh-keygen -t ed25519 -C "cloud-agent@oracle"
cat ~/.ssh/id_ed25519.pub
# → Add this key to GitHub repository as deploy key (with write access)

# Configure git
git config --global user.name "Cloud Agent"
git config --global user.email "cloud-agent@fte"

# Clone vault repo
git clone git@github.com:<user>/fte-vault.git ~/vault
```

### 2.2 Create Vault Structure

```bash
cd ~/vault
mkdir -p Needs_Action/{email,social,invoice,general}
mkdir -p In_Progress/{cloud,local}
mkdir -p Plans/{email,social,invoice}
mkdir -p Pending_Approval/{email,social,invoice}
mkdir -p Updates
mkdir -p Done/{email,social,invoice}
mkdir -p Logs
mkdir -p Briefings
touch Dashboard.md
```

### 2.3 Configure .gitignore (BEFORE first sync!)

```bash
cat > ~/vault/.gitignore << 'EOF'
# Secrets — NEVER sync
.env
*.token
*.session
*credentials*
*.key
*.pem
whatsapp-session/
banking/
*secret*
*.pickle
*.p12

# OS/Editor
.DS_Store
*.swp
*~
.vscode/
EOF

git add -A && git commit -m "init: vault structure with security gitignore"
git push origin main
```

### 2.4 Install gitwatch (push on change)

```bash
git clone https://github.com/gitwatch/gitwatch.git /tmp/gitwatch
sudo install -b /tmp/gitwatch/gitwatch.sh /usr/local/bin/gitwatch

# Test it
gitwatch -r origin -b main ~/vault &
```

### 2.5 Configure cron pull (every 3 minutes)

```bash
crontab -e
# Add:
# */3 * * * * cd /home/ubuntu/vault && git pull --rebase origin main >> /var/log/git-pull.log 2>&1
```

---

## Phase 3: Odoo on Cloud

### 3.1 Docker Compose

```bash
mkdir -p ~/odoo && cd ~/odoo
# Create docker-compose.yml with arm64v8/odoo image
# Configure PostgreSQL, volumes, and port 8069
docker compose up -d
```

### 3.2 HTTPS with Let's Encrypt

```bash
# Point domain to VM IP (A record)
# Configure Nginx reverse proxy for Odoo
sudo certbot --nginx -d odoo.yourdomain.com
# Auto-renewal is configured automatically
```

### 3.3 Odoo Backup Cron

```bash
# Daily backup at 2 AM
crontab -e
# 0 2 * * * docker exec odoo-db pg_dump -U odoo odoo > ~/backups/odoo_$(date +\%Y\%m\%d).sql
```

---

## Phase 4: Deploy AI Employee on Cloud

### 4.1 Clone Project

```bash
git clone <project-repo> ~/fte-project
cd ~/fte-project
uv sync
```

### 4.2 Configure Cloud .env

```bash
cat > ~/fte-project/.env << 'EOF'
ANTHROPIC_API_KEY=sk-ant-...
GMAIL_CREDENTIALS_PATH=/home/ubuntu/.credentials/gmail.json
META_PAGE_ACCESS_TOKEN=...
ODOO_URL=http://localhost:8069
# ... other API keys
EOF
```

### 4.3 PM2 Ecosystem

```bash
# Create ecosystem.config.js with all processes
pm2 start ecosystem.config.js
pm2 save
pm2 startup  # Follow instructions for systemd integration
```

---

## Phase 5: Local Agent Setup

### 5.1 Clone Vault on Local

```bash
# In WSL
git clone git@github.com:<user>/fte-vault.git ~/vault

# Install gitwatch
sudo apt install inotify-tools
# ... same gitwatch setup as cloud
```

### 5.2 Configure Windows Task Scheduler

```
1. Open Task Scheduler
2. Create Task: "FTE Local Orchestrator"
3. Trigger: At log on
4. Action: wsl -d Ubuntu -- bash -c "/home/user/fte-project/scripts/start-local.sh"
5. Settings: Run whether user is logged on or not
```

### 5.3 Local Start Script

```bash
#!/bin/bash
# scripts/start-local.sh
cd ~/vault && git pull --rebase origin main
cd ~/fte-project && python -m src.orchestrator.local_orchestrator &
gitwatch -r origin -b main ~/vault &
```

---

## Phase 6: Verify Platinum Demo

```bash
# 1. Ensure laptop is OFF (or close WSL)
# 2. Send test email to your Gmail
# 3. Check Cloud VM: tail -f ~/vault/Logs/$(date +%Y-%m-%d).json
# 4. Verify draft created in ~/vault/Pending_Approval/email/
# 5. Turn on laptop / start WSL
# 6. Verify Local pulls and shows notification
# 7. Approve the draft
# 8. Verify email sent
# 9. Verify task moved to /Done/
```
