module.exports = {
  apps: [
    {
      name: "fte-system",
      script: "src/main.py",
      interpreter: "/mnt/e/hackathon-0/full-time-equivalent-project/.venv/bin/python",
      args: "run",
      cwd: "/mnt/e/hackathon-0/full-time-equivalent-project",
      env: {
        DRY_RUN: "false",
        POLL_INTERVAL: "60",
        CLAUDE_TIMEOUT: "300",
        LOG_LEVEL: "INFO",
      },
      // Auto-restart on crash
      autorestart: true,
      max_restarts: 10,
      restart_delay: 5000,
      watch: false,
      // Log files
      out_file: "./logs/pm2-out.log",
      error_file: "./logs/pm2-error.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss",
      merge_logs: true,
    },
  ],
};
