' Start FTE Local Agent — Hidden Window (no terminal popup)
' Used by Windows Task Scheduler to auto-start on login
'
' Setup:
' 1. Open Task Scheduler
' 2. Create Task: "FTE Local Orchestrator"
' 3. Trigger: At log on
' 4. Action: wscript.exe "C:\path\to\start-local-hidden.vbs"
' 5. Settings: Run whether user is logged on or not

Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "wsl -d Ubuntu -- bash -c ""/mnt/e/hackathon-0/full-time-equivalent-project/scripts/start-local.sh""", 0, False
