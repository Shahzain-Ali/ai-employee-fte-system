module.exports = {
  apps: [
    {
      name: "fte-system",
      script: "uv",
      args: "run python -m src.main run",
      cwd: "/home/ubuntu/fte-project",
      restart_delay: 10000,
      max_restarts: 10,
      env: {
        DRY_RUN: "false",
        POLL_INTERVAL: "60",
        CLAUDE_TIMEOUT: "300"
      }
    }
  ]
};
