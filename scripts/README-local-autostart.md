# Local Auto-Start Setup Guide

## Windows Task Scheduler Configuration

### Steps:
1. Open **Task Scheduler** (search "Task Scheduler" in Start menu)
2. Click **Create Task** (not "Create Basic Task")
3. **General tab:**
   - Name: `FTE Local Orchestrator`
   - Description: `Auto-start AI Employee Local Agent on login`
   - Run whether user is logged on or not: **Yes**
4. **Triggers tab:**
   - New → Begin the task: **At log on**
   - Specific user: your Windows account
5. **Actions tab:**
   - New → Action: **Start a program**
   - Program: `wscript.exe`
   - Arguments: `"C:\path\to\full-time-equivalent-project\scripts\start-local-hidden.vbs"`
6. **Settings tab:**
   - Allow task to be run on demand: **Yes**
   - If the task fails, restart every: **5 minutes**
   - Stop the task if it runs longer than: **Disabled**

### Manual Start
```bash
# In WSL terminal:
bash /mnt/e/hackathon-0/full-time-equivalent-project/scripts/start-local.sh
```

### Verify Running
```bash
# Check if Local Orchestrator is running:
pgrep -f local_orchestrator

# Check logs:
tail -f ~/fte-local-orchestrator.log
```
