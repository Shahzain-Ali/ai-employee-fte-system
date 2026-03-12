# Bronze Tier — Video Demo Script

**Purpose**: Presenter-only guide for live demo during video recording.
**Language**: Roman Urdu (steps) + English (folder/file names)
**Audience**: Video presenter — viewers do NOT see this file.

---

## Pre-Demo Checklist (Before Recording)

Yeh sab pehle check kar lein:

- [ ] System chal raha hai — `pm2 list` mein `filesystem_watcher` aur `orchestrator` ka status **online** ho
- [ ] Vault khuli ho Obsidian mein — `AI_Employee_Vault/` folder
- [ ] Dashboard.md open ho Obsidian mein
- [ ] Ek test file ready ho — `invoice.txt` ya `test_document.pdf`
- [ ] Ek `.exe` file ready ho reject demo ke liye — `malware.exe` (empty file)
- [ ] Terminal open ho vault folder pe

---

## DEMO 1 — Normal File Processing (Inbox → Done)

**On screen**: Obsidian vault dikhao — Inbox/ folder empty ho

### Step 1: File Drop karo
```
Drag & drop karo:  invoice.txt  →  AI_Employee_Vault/Inbox/
```
Viewers ko explain karo:
> "Yeh hamara AI employee ka mailbox hai. Jaise hum koi document daftar mein dete hain, hum isko Inbox mein rakh dete hain."

### Step 2: Watcher ka reaction dikhao (~5 seconds)
Obsidian mein `Needs_Action/` folder refresh karo.
Ek naya file dikhega:
```
FILE_invoice.txt.md
```
> "Watcher ne file detect ki — OS ne event bheja — Python ne pakda. Abhi tak koi Claude nahi chala."

### Step 3: Action File kholo
`Needs_Action/FILE_invoice.txt.md` kholo.
Show karo YAML frontmatter:
```yaml
file_path: .../Inbox/invoice.txt
file_name: invoice.txt
file_type: .txt
status: pending
created_at: 2026-02-20T...
```
> "Yeh action file hai. Claude ke liye kaam ka ticket. Status: pending."

### Step 4: Orchestrator wait karo (~60 seconds)
Terminal mein live logs dikhao:
```
pm2 logs orchestrator
```
> "Orchestrator har 60 second mein check karta hai — koi pending file hai? Abhi queue mein hai hamari file."

### Step 5: Claude ka kaam dikhao
Jab Claude trigger ho:
- Terminal mein `claude` process dikhega
- `Done/` folder mein file move hogi
- Dashboard.md update hogi

> "Claude ne file padhi, process ki, aur Done/ mein shift kar di. Kaam complete."

### Step 6: Dashboard dikhao
Obsidian mein `Dashboard.md` refresh karo:
- **Status**: Working → Idle
- **Completed Today**: +1
- **Recent Activity**: invoice.txt processed

---

## DEMO 2 — Approval Workflow (Sensitive Action)

**On screen**: Reset karo — naya document jo payment ki request karta ho

### Step 1: Sensitive file drop karo
```
Drag & drop:  payment_request.txt  →  AI_Employee_Vault/Inbox/
```
> "Is baar file ek sensitive kaam ki request hai — payment ya external communication."

### Step 2: Watcher detection dikhao
`Needs_Action/FILE_payment_request.txt.md` bana — wahi as before.

### Step 3: Claude processes, pauses for approval
Orchestrator Claude ko trigger karta hai.
Claude file padhta hai, action identify karta hai — **sensitive action**.

Ab `Pending_Approval/` folder mein naya file banta hai:
```
APPROVAL_payment_request_20260220T....md
```
> "Claude ne ruk ke kaha — yeh kaam meri permission ke baghair nahi hoga. Yahan hamara HITL hai — Human in the Loop."

### Step 4: Dashboard dikhao
`Dashboard.md`:
- **Status**: ⚠️ Waiting for Approval
- **Pending Approvals**: 1

### Step 5: Approval file kholo
`Pending_Approval/APPROVAL_payment_request_....md` kholo aur dikhao:
- Kya kaam karna hai
- Kis permission ki zaroorat hai
- Instructions: Move to `Approved/` or `Rejected/`

### Step 6: Approve karo
File ko:
```
Pending_Approval/  →  Approved/
```
> "Hum ne file Approved folder mein move ki — yeh hamari taraf se green light hai."

### Step 7: Claude resumes
Orchestrator `Approved/` folder dekh raha hai. Claude dobara trigger hota hai aur kaam complete karta hai. File `Done/` mein move hoti hai.

---

## DEMO 3 — Rejection Workflow

**On screen**: Same APPROVAL file jo abhi tak Pending mein ho

> "Ab maan lo hum yeh kaam approve nahi karna chahte."

### Step 1: Reject karo
File ko:
```
Pending_Approval/  →  Rejected/
```

### Step 2: System ka response
- Original file `Done/` mein move hoti hai (completed as rejected)
- Log entry banti hai: `status: rejected`
- Dashboard update hota hai

> "AI ne accept kiya hamara decision. Log mein note ho gaya. Koi action nahi liya."

---

## DEMO 4 — Security: File Rejected (.exe)

**On screen**: Terminal khola ho

### Step 1: .exe file drop karo
```
Drag & drop:  malware.exe  →  AI_Employee_Vault/Inbox/
```
> "Koi galti se ya testing ke liye executable file Inbox mein daal de."

### Step 2: Rejection dikhao
`Needs_Action/` mein naya file:
```
REJECTED_malware.exe.md
```
> "Watcher ne file type check ki — .exe blocked hai. Claude ko kabhi nahi bheja. Security layer ne rok liya."

### Step 3: REJECTED file kholo
Dikhao:
```yaml
reason: Unsupported file type — .exe files are not allowed
```

---

## DEMO 5 — Dashboard Live View

**On screen**: Dashboard.md full screen Obsidian mein

Yeh fields dikhao:
| Field | Value |
|-------|-------|
| Status | Idle / Working / ⚠️ Approval Needed |
| Pending | Count from Needs_Action/ |
| Completed Today | Count from Done/ |
| Pending Approvals | Count from Pending_Approval/ |
| Recent Activity | Last 5 actions |

> "Yeh hamara control room hai. Ek nazar mein pata chal jata hai AI employee kya kar raha hai."

---

## Demo End — Quick Recap (On Camera)

> "Aaj humne dekha:
> 1. File Inbox mein gai — Watcher ne pakda
> 2. Orchestrator ne Claude ko trigger kiya
> 3. Normal file — Done mein gayi
> 4. Sensitive file — Approval maanga, hum ne approve kiya, kaam hua
> 5. Rejection — AI ne accept kiya, koi action nahi
> 6. .exe file — Security layer ne block ki, Claude tak pohnchi hi nahi
>
> Yahi hai Bronze Tier — Personal AI Employee Foundation."

---

## Folder Reference (Quick Reminder)

```
AI_Employee_Vault/
├── Inbox/              ← Aap files yahan dalte ho
├── Needs_Action/       ← Watcher yahan action files banata hai
├── Pending_Approval/   ← Claude yahan approval file banata hai
├── Approved/           ← Aap yahan move karte ho approve karne ke liye
├── Rejected/           ← Aap yahan move karte ho reject karne ke liye
├── Done/               ← Completed kaam yahan aata hai
├── Logs/               ← JSON audit trail
├── Dashboard.md        ← Live status view
└── Company_Handbook.md ← AI ke rules
```

---

*Presenter only — viewers ke sath share mat karna.*
