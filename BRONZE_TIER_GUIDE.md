# Bronze Tier — Complete Guide (Roman Urdu)

> **Classmates ke liye:** Yeh guide Bronze Tier AI Employee ko check karne aur chalane ke liye hai.
> Har step clearly explain kiya gaya hai — video ke liye perfect guide.

---

## Bronze Tier Kya Hai? (Architecture Overview)

Bronze Tier ek **Local AI Employee System** hai jo automatically aapke files ko process karta hai.

```
Aap file daalo          Watcher detect kare         Orchestrator uthaye
  Inbox/         →      Needs_Action/ FILE     →      Claude ko call kare
                                                             ↓
Dashboard update ←    Done/ mein move kare    ←    SUMMARY file likhay
```

### Do Main Components

| Component | Kya karta hai |
|-----------|--------------|
| **Watcher** | `Inbox/` folder ko monitor karta hai. Naya file aata hai to `Needs_Action/` mein action file banata hai |
| **Orchestrator** | Har 60 second mein `Needs_Action/` check karta hai. File mile to Claude ko call karta hai |

> **Important:** Watcher aur Orchestrator dono **alag alag** chalte hain, parallel mein.
> Watcher orchestrator ko run **nahi karta** — dono saath start hotay hain.

---

## Step 0 — Prerequisites (Pehle Yeh Check Karo)

### 0.1 Python aur uv check karo
```bash
python3 --version    # 3.12+ hona chahiye
uv --version         # installed hona chahiye
```

### 0.2 Claude Code CLI check karo
```bash
CLAUDECODE="" claude --version
```
Agar "command not found" aaye:
```bash
npm install -g @anthropic-ai/claude-code
```

### 0.3 Project folder mein jao
```bash
cd /mnt/e/hackathon-0/full-time-equivalent-project
```

---

## Step 1 — .env File Check Karo

```bash
cat .env
```

Yeh values honi chahiye:
```env
VAULT_PATH=/mnt/e/hackathon-0/full-time-equivalent-project/AI_Employee_Vault
POLL_INTERVAL=60
CLAUDE_TIMEOUT=300
DRY_RUN=false        # <-- IMPORTANT: false hona chahiye real Claude ke liye
LOG_LEVEL=INFO
```

> **DRY_RUN=true** hoga to Claude call nahi hoga — sirf files move hongi.
> **DRY_RUN=false** hoga to real Claude processing hogi aur SUMMARY files banegi.

---

## Step 2 — Tests Chalao (Sab Kuch Theek Hai?)

```bash
uv run pytest -v
```

**Expected output:**
```
55 passed in ~8s
```

Agar sab tests pass hoon to system ready hai. Koi fail hua to code mein kuch masla hai.

---

## Step 3 — Vault Setup Check Karo

```bash
ls AI_Employee_Vault/
```

**Yeh 9 folders hone chahiye:**
```
Approved/
Company_Handbook.md
Dashboard.md
Done/
Inbox/
Logs/
Needs_Action/
Pending_Approval/
Rejected/
```

Agar vault exist nahi karta:
```bash
./run.sh setup
```

---

## Step 4 — Manual End-to-End Test (Important!)

Yeh steps video mein clearly dikhao:

### 4.1 — Test file Inbox mein daalo
```bash
echo "Yeh meri test file hai. AI Employee process karo." > AI_Employee_Vault/Inbox/my_test.txt
```

### 4.2 — Watcher scan chalao (action file banaye ga)
```bash
uv run python3 -c "
from pathlib import Path
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
from src.watchers.filesystem_watcher import FilesystemWatcher
watcher = FilesystemWatcher(vault_path=Path('AI_Employee_Vault'))
watcher._startup_scan()
print('Needs_Action mein:', list((Path('AI_Employee_Vault/Needs_Action')).glob('FILE_*.md')))
"
```

**Expected:** `Needs_Action/FILE_my_test.txt.md` ban jaye

### 4.3 — Orchestrator ek poll chalao (Claude trigger hoga)
```bash
CLAUDE_TIMEOUT=300 uv run python3 -c "
import os, logging
from pathlib import Path
os.environ['DRY_RUN'] = 'false'
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s]: %(message)s')
from src.orchestrator.orchestrator import Orchestrator
orch = Orchestrator(vault_path=Path('AI_Employee_Vault'), dry_run=False)
print('Orchestrator poll shuru...')
orch._poll_once()
print('Poll complete!')
"
```

**Yeh 60-120 second le ga** — Claude real mein kaam kar raha hoga.

### 4.4 — Results check karo

**Done/ folder check karo:**
```bash
ls AI_Employee_Vault/Done/
```
Tumhe dikhna chahiye:
- `FILE_my_test.txt.md` (action file — moved here)
- `SUMMARY_FILE_my_test.txt.md` (Claude ne likha) ← **Yeh proof hai ke kaam hua**

**Dashboard check karo:**
```bash
head -20 AI_Employee_Vault/Dashboard.md
```
`Last Updated` timestamp abhi ka hona chahiye.

**Logs check karo:**
```bash
cat AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json | python3 -m json.tool | tail -30
```
`processing_completed` entry dikhni chahiye.

---

## Step 5 — Full System Chalao (Production Mode)

Jab sab manually check ho jaye, poora system ek saath chalao:

```bash
./run.sh run
```

Ya directly:
```bash
uv run python3 -m src.main run
```

**Output dikhega:**
```
Starting AI Employee system...
  Vault: /mnt/e/.../AI_Employee_Vault
  Poll interval: 60s
  Dry run: False

[INFO] FilesystemWatcher running
[INFO] Orchestrator started. Poll interval: 60s, dry_run=False
```

Ab har baar `Inbox/` mein file daalo — automatically process hogi.

---

## Step 6 — DRY_RUN Mode vs Real Mode

| Mode | Kya hota hai |
|------|-------------|
| `DRY_RUN=true` | Claude call nahi hota. Sirf file `Done/` mein move hoti hai. SUMMARY nahi banta. |
| `DRY_RUN=false` | Real Claude subprocess chalti hai. SUMMARY file banti hai. Dashboard update hoti hai. |

**Development mein** `DRY_RUN=true` use karo — fast aur free.
**Demo mein** `DRY_RUN=false` use karo — real Claude kaam karta hai.

---

## Step 7 — Kuch Bhi Kaam Na Kare To (Troubleshooting)

### Problem: "Claude Code not found"
```bash
npm install -g @anthropic-ai/claude-code
claude auth login
```

### Problem: SUMMARY file nahi bani
```bash
# Claude ka permission issue hai — yeh flag zaroor hona chahiye
# orchestrator.py mein check karo yeh line:
grep "dangerously-skip-permissions" src/orchestrator/orchestrator.py
```
Output mein `--dangerously-skip-permissions` dikhna chahiye.

### Problem: Needs_Action mein file nahi bani
```bash
# File type check karo — .exe aur unknown types reject hotay hain
# Sirf: .txt .md .pdf .docx .csv .png .jpg .mp3 .mp4 allowed hain
```

### Problem: Dashboard update nahi hua
```bash
# DRY_RUN check karo
cat .env | grep DRY_RUN
# false hona chahiye
```

---

## Complete Flow — Ek Nazar Mein

```
1. ./run.sh run
        |
        |-----> Watcher start (Inbox/ monitor kare)
        |-----> Orchestrator start (Needs_Action/ har 60s check kare)

2. Aap: AI_Employee_Vault/Inbox/ mein file daalo
        |
        v
3. Watcher: File detect kiya!
            Needs_Action/FILE_yourfile.md bana diya
            Audit log mein entry likhi

4. Orchestrator (next poll mein):
            FILE_yourfile.md mila!
            Claude ko call kiya:
              claude --print --dangerously-skip-permissions "skill padhho, file process karo..."

5. Claude (real AI):
            .claude/skills/process_document.md padha
            Inbox/yourfile.txt padha
            Done/SUMMARY_FILE_yourfile.md likha
            Logs/ mein entry likhi

6. Orchestrator:
            Action file Done/ mein move kiya
            Dashboard.md update kiya
            Audit log mein processing_completed likha

7. DONE! Check karo:
            Done/SUMMARY_FILE_yourfile.md  ← Claude ki summary
            Dashboard.md                   ← Updated stats
            Logs/YYYY-MM-DD.json           ← Complete audit trail
```

---

## Quick Reference Commands

```bash
# Tests chalao
uv run pytest -v

# Vault setup
./run.sh setup

# Poora system chalao
./run.sh run

# Done/ check karo
ls AI_Employee_Vault/Done/

# Dashboard dekho
cat AI_Employee_Vault/Dashboard.md

# Aaj ke logs dekho
cat AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json
```

---

*Bronze Tier — Personal AI Employee Hackathon-0*
*Guide version: 2026-02-18*
