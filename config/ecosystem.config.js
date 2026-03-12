// PM2 Ecosystem Configuration — Platinum Tier Cloud VM
// All processes managed by PM2 for auto-restart and monitoring

module.exports = {
  apps: [
    {
      name: "cloud-orchestrator",
      script: "uv",
      args: "run python -m src.orchestrator.cloud_orchestrator",
      cwd: "/home/ubuntu/fte-project",
      env: {
        AGENT_CONFIG: "/home/ubuntu/fte-project/config/cloud-agent.yaml",
        VAULT_PATH: "/home/ubuntu/vault",
      },
      restart_delay: 5000,
      max_restarts: 10,
      autorestart: true,
      watch: false,
      log_file: "/var/log/fte/cloud-orchestrator.log",
      error_file: "/var/log/fte/cloud-orchestrator-error.log",
      out_file: "/var/log/fte/cloud-orchestrator-out.log",
    },
    {
      name: "email-watcher",
      script: "uv",
      args: "run python -m src.watchers.gmail_watcher",
      cwd: "/home/ubuntu/fte-project",
      env: {
        VAULT_PATH: "/home/ubuntu/vault",
      },
      restart_delay: 10000,
      max_restarts: 10,
      autorestart: true,
      watch: false,
      log_file: "/var/log/fte/email-watcher.log",
      error_file: "/var/log/fte/email-watcher-error.log",
      out_file: "/var/log/fte/email-watcher-out.log",
    },
    {
      name: "gitwatch",
      script: "/usr/local/bin/gitwatch",
      args: "-r origin -b main /home/ubuntu/vault",
      autorestart: true,
      restart_delay: 5000,
      max_restarts: 5,
      log_file: "/var/log/fte/gitwatch.log",
      error_file: "/var/log/fte/gitwatch-error.log",
      out_file: "/var/log/fte/gitwatch-out.log",
    },
    {
      name: "health-monitor",
      script: "/home/ubuntu/fte-project/scripts/health-monitor.sh",
      cron_restart: "*/5 * * * *",
      autorestart: false,
      watch: false,
      log_file: "/var/log/fte/health-monitor.log",
      error_file: "/var/log/fte/health-monitor-error.log",
      out_file: "/var/log/fte/health-monitor-out.log",
    },
  ],
};
