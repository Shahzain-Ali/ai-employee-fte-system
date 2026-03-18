#!/bin/bash
# Setup Cloud VM — Platinum Tier
# Run on Oracle Cloud ARM A1 VM (Ubuntu 22.04 aarch64)
# Usage: ssh ubuntu@<VM_IP> 'bash -s' < scripts/setup-cloud-vm.sh

set -euo pipefail

LOG="/var/log/fte-cloud-setup.log"
sudo mkdir -p /var/log/fte
exec > >(tee -a "$LOG") 2>&1

echo "=== FTE Cloud VM Setup — $(date -u) ==="

# 1. System update
echo "[1/10] Updating system..."
sudo apt update && sudo apt upgrade -y

# 2. Install essentials
echo "[2/10] Installing essentials..."
sudo apt install -y git curl wget build-essential inotify-tools fail2ban nginx certbot python3-certbot-nginx

# 3. SSH hardening
echo "[3/10] Hardening SSH..."
sudo sed -i 's/#\?PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl restart sshd
echo "SSH: Password auth disabled"

# 4. Install Docker
echo "[4/10] Installing Docker..."
sudo apt install -y docker.io docker-compose-v2
sudo usermod -aG docker ubuntu
echo "Docker installed. NOTE: logout/login needed for group to take effect"

# 5. Install Node.js 22 LTS
echo "[5/10] Installing Node.js 22 LTS..."
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo bash -
sudo apt install -y nodejs
echo "Node.js $(node --version) installed"

# 6. Install PM2
echo "[6/10] Installing PM2..."
sudo npm install -g pm2
echo "PM2 $(pm2 --version) installed"

# 7. Install uv (Python package manager)
echo "[7/10] Installing uv..."
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
echo "uv installed"

# 8. Install Claude Code CLI
echo "[8/10] Installing Claude Code CLI..."
sudo npm install -g @anthropic-ai/claude-code
echo "Claude Code CLI installed"

# 9. Install gitwatch
echo "[9/10] Installing gitwatch..."
git clone https://github.com/gitwatch/gitwatch.git /tmp/gitwatch 2>/dev/null || true
sudo install -b /tmp/gitwatch/gitwatch.sh /usr/local/bin/gitwatch
echo "gitwatch installed"

# 10. Configure firewall
echo "[10/10] Configuring firewall..."
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw --force enable
echo "Firewall: ports 22, 80, 443 open"

# Create log directories
sudo mkdir -p /var/log/fte /var/log/fte-health
sudo chown -R ubuntu:ubuntu /var/log/fte /var/log/fte-health

# PM2 startup (auto-start on reboot)
echo ""
echo "=== Post-setup manual steps ==="
echo "1. Run: claude login (authenticate CLI)"
echo "2. Clone vault repo: git clone git@github.com:<user>/fte-vault.git ~/vault"
echo "3. Clone project: git clone <project-repo> ~/fte-project && cd ~/fte-project && uv sync"
echo "4. Copy .env: cp config/cloud.env.example .env && nano .env"
echo "5. Start PM2: pm2 start config/ecosystem.config.js && pm2 save"
echo "6. Enable PM2 startup: pm2 startup (follow instructions)"
echo "7. For Odoo: cd ~/fte-project && docker compose -f config/docker-compose-odoo.yml up -d"
echo "8. For HTTPS: sudo certbot --nginx -d odoo.yourdomain.com"
echo ""
echo "=== Setup complete — $(date -u) ==="
