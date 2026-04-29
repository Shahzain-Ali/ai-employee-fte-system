// PM2 Ecosystem Configuration — Platinum Tier Cloud VM
// Uses main.py with AGENT_MODE=cloud → CloudOrchestrator (draft-only)

module.exports = {
  apps: [
    {
      name: "fte-system",
      script: "/home/ubuntu/.local/bin/uv",
      args: "run python -m src.main run",
      cwd: "/home/ubuntu/fte-project",
      env: {
        AGENT_MODE: "cloud",
        VAULT_PATH: "/home/ubuntu/fte-project/AI_Employee_Vault",
        CLOUD_CONFIG_PATH: "/home/ubuntu/fte-project/config/cloud-agent.yaml",
        DRY_RUN: "false",
        POLL_INTERVAL: "60",
        CLAUDE_TIMEOUT: "300",
      },
      restart_delay: 10000,
      max_restarts: 10,
      autorestart: true,
      watch: false,
      out_file: "/var/log/fte/fte-system-out.log",
      error_file: "/var/log/fte/fte-system-error.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss",
      merge_logs: true,
    },
  ],
};
