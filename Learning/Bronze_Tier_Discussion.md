# Hackathon-0: Bronze Tier Understanding — Full Discussion
**Format:** Question (English) → Answer (Roman Urdu)
**Purpose:** Video reference aur learning documentation
**Project:** Personal AI Employee Hackathon-0 — Building Autonomous FTEs in 2026

---

## SECTION 1: Hackathon-0 Overview

---

**Q1: What is Hackathon-0 about? Give me a simple summary.**

**A:**
Yeh hackathon aap ko sikhata hai ke ek AI Employee (Digital FTE) kaise banao jo 24/7 kaam kare — aap ki emails handle kare, WhatsApp messages ka jawab de, bank transactions check kare, social media post kare, aur har Monday ko aap ko ek "CEO Briefing" de ke bataye ke business mein kya hua.

Sab kuch local machine pe chalta hai (privacy ke liye), Claude Code brain hai, aur Obsidian dashboard/memory hai.

**Main components:**
- **Brain:** Claude Code (reasoning engine)
- **Memory/GUI:** Obsidian (local markdown files)
- **Senses:** Python Watcher scripts (Gmail, WhatsApp, File System)
- **Hands:** MCP Servers (external actions lene ke liye)

---

**Q2: What does this line mean — "A Digital FTE is an AI agent that is built, hired, and priced as if it were a human employee. This shifts the conversation from software licenses to headcount budgets."**

**A:**
Yeh line ek soch badalne ki baat kar rahi hai — AI ko software nahi, balke employee samjho.

**FTE = Full-Time Equivalent** — ek business term — matlab ek full-time employee jo 40 ghante hafta kaam kare.

**Purani soch vs Nayi soch:**

| Purani Soch | Nayi Soch |
|-------------|-----------|
| "Ek software ka license khareedein — $50/month" | "Ek Digital Employee hire karein — $500/month" |
| CEO sochta hai: yeh ek tool hai | CEO sochta hai: yeh ek banda hai jo kaam karega |

**Asli point:** Jab tum AI ko employee kehte ho, log turant value samajhte hain — 85-90% cost saving dikhti hai, CEO approve kar deta hai.

---

## SECTION 2: Obsidian — What It Is

---

**Q3: What is Obsidian? Why are we using it in this hackathon?**

**A:**
Obsidian ek note-taking app hai — bilkul free — jismein tum Markdown files (.md) mein notes likhte ho. Yeh sab notes tumhare apne computer pe locally save hoti hain, kisi cloud pe nahi.

**Is hackathon mein Obsidian ka role:**

| File | Kaam |
|------|------|
| Dashboard.md | Real-time summary — bank balance, pending tasks |
| Company_Handbook.md | Rules — Claude kaise behave kare |
| /Needs_Action/ folder | Naye tasks jo AI ko karne hain |
| /Done/ folder | Complete ho chuke tasks |
| /Logs/ folder | AI ne kya kiya — sab record |

**Kyun Obsidian?**
1. Local hai — data tumhare computer pe (privacy)
2. Markdown files hain — Claude easily padh aur likh sakta hai
3. Free hai
4. Linking feature hai (Wikipedia jaisa navigation)

---

**Q4: I can also see files and logs using VS Code. So what is the main purpose of Obsidian?**

**A:**
Obsidian Claude ke liye nahi hai — Obsidian TUMHARE liye hai. Claude ko koi fark nahi padta, woh terminal se files padhta hai.

**VS Code vs Obsidian:**

|                           |     VS Code     |       Obsidian     |
|--|---------|---------|
| Files dekhna              |       ✅        |         ✅        |
| Links clickable           |       ❌        |         ✅        |
| Navigation                | Manually folder  |      Ek click     |
                                mein jaao 
| Feel                      |    Code editor   |  Dashboard/Wikipedia |

**Simple:** Claude Code = Backend (kaam karne wala). Obsidian = Frontend/GUI (tumhein dikhane wala).

---

**Q5: What is a "Vault" in Obsidian?**

**A:**
**Vault = Sirf ek normal folder hai tumhare computer mein. Bas!**

```
C:\Users\TumharaName\AI_Employee_Vault\   ← Yeh hai vault
```

Jab tum yeh folder Obsidian mein open karte ho — woh isko "vault" kehta hai. Koi special cheez nahi — bas ek folder! Obsidian us folder ki saari .md files ko dikhata hai.

---

**Q6: When we write [[filename]] in a markdown file, does it work in both VS Code and Obsidian?**

**A:**
Nahi — yeh standard Markdown nahi hai!

| Syntax | Standard Markdown? | VS Code mein? | Obsidian mein? |
|--------|-------------------|--------------|----------------|
| `[text](file.md)` | ✅ Haan | ✅ Haan (Ctrl+Click) | ✅ Haan |
| `[[filename]]` | ❌ Nahi | ❌ Nahi | ✅ Haan |

`[[filename]]` Obsidian ka special "WikiLinks" syntax hai. Yeh standard Markdown nahi hai — isliye VS Code mein kaam nahi karega.

**Obsidian mein `[[]]` se:**
- Blue clickable link banta hai
- Click karo — file khul jaye
- Auto-complete milti hai typing karte waqt
- Backlinks dikhte hain

---

**Q7: How do I open a folder as a vault in Obsidian?**

**A:**
1. Obsidian kholo
2. Left bottom corner mein vault name ya gear icon pe click karo
3. "Open another vault" select karo
4. "Open folder as vault" pe click karo
5. Apna folder select karo — Done!

**Note:** "Create new vault" mat dabao — woh naya folder banata hai. Tumhein "Open folder as vault" chahiye.

---

## SECTION 3: Requirements & Setup

---

**Q8: Can we fulfill all the requirements for Hackathon-0? Check our system.**

**A:**
System check karne ke baad yeh results the:

| Component | Required | System Pe | Status |
|-----------|----------|-----------|--------|
| Claude Code | Active subscription | v2.1.42 | ✅ Pass |
| Obsidian | v1.10.6+ | Installed | ✅ Pass |
| Python | 3.13+ | 3.12.3 | ⚠️ Update needed |
| Node.js | v24+ LTS | v20.19.6 | ❌ Update zaroori |
| Git | Latest | 2.43.0 | ✅ Pass |

---

**Q9: If I update Node.js from v20 to v24, will my existing files and projects be affected?**

**A:**
Nahi — bilkul safe rahenge!

**Kya hota hai update pe:**
- Node.js v20 → v24 se replace ho jaata hai (ek hi version)
- Tumhara code alag cheez hai — safe
- 99% cases mein purana code v24 pe bhi chalega

**Agar rare case mein issue aaye:**
```bash
npm install  # Project folder mein chalao — problem solve
```

**Node.js = Screwdriver (tool). Tumhara code = Furniture. Screwdriver badlo, furniture safe.**

---

**Q10: What is the difference between amd64 and amd32 in Python installer (e.g., python-3.14.3-amd64)?**

**A:**
| Version | Matlab | Kis Computer Ke Liye |
|---------|--------|---------------------|
| **amd64** | 64-bit | Modern computers (2010 ke baad) |
| **amd32 (x86)** | 32-bit | Purane computers |

**Tumhare liye:** `python-3.14.3-amd64.exe` download karo — modern computer hai.

**Check karne ka tarika:** Windows → Settings → System → About → "System type" dekho.

---

## SECTION 4: Bronze Tier — Detailed Understanding

---

**Q11: What is Bronze Tier? What are its 5 main things?**

**A:**
Bronze = Sabse pehla aur basic level. Isko complete karna minimum requirement hai.

**5 Cheezein banani hain:**

1. **Obsidian Vault** with Dashboard.md aur Company_Handbook.md
2. **One Watcher Script** (Gmail OR File System)
3. **Claude Code** vault se files padhe aur likhe
4. **Basic Folder Structure:** /Inbox, /Needs_Action, /Done
5. **Agent Skills** — har AI functionality ek skill ke tor pe

---

**Q12: What is a Vault again and what does the folder structure look like?**

**A:**
```
AI_Employee_Vault/          ← Vault (sirf ek folder)
├── Dashboard.md            ← Main screen
├── Company_Handbook.md     ← Rules
├── Inbox/                  ← Manual file drop
├── Needs_Action/           ← Watchers yahan files banate hain
└── Done/                   ← Complete tasks
```

**Teen folders ka matlab:**
- **Inbox/** = Tumhara manual "drop box" — tum khud files dalte ho
- **Needs_Action/** = Watchers automatic files banate hain — Claude yahan se padhta hai
- **Done/** = Kaam complete — Claude yahan move karta hai

---

**Q13: What is the flow when Gmail Watcher detects an email? Does Claude Code run automatically?**

**A:**
**Nahi — Claude 24/7 nahi chalta. Teen alag scripts hain:**

| Script | Kaam | 24/7? |
|--------|------|-------|
| Gmail Watcher (Python) | Gmail check karo, file banao | ✅ Haan |
| Orchestrator.py (Python) | Folder dekho, Claude trigger karo | ✅ Haan |
| Claude Code | File padho, kaam karo, exit karo | ❌ Nahi |

**Complete flow:**
```
Gmail pe email aaya
        ↓
Gmail Watcher (Python) detect kiya → Needs_Action/EMAIL_ali.md bani
        ↓
Orchestrator.py ne file dekhi → Claude Code trigger kiya
        ↓
Claude Code ne file padhi → kaam kiya → Done/ mein move kiya → Exit
        ↓
Orchestrator dobara wait karta hai
```

**Real life example:**
- Security Guard (Watcher) = 24/7 gate pe
- Manager (Orchestrator) = 24/7 office mein
- Employee (Claude Code) = Aaya, kaam kiya, ghar chala gaya

---

**Q14: Does Gmail Watcher use Claude Code to create files?**

**A:**
Nahi! Gmail Watcher pure Python script hai — Claude se koi talluq nahi.

**Gmail Watcher khud karta hai:**
1. Gmail API se connect hota hai
2. New email check karta hai
3. Email milti hai → khud .md file banata hai
4. Needs_Action/ mein save karta hai
5. Khatam — Claude ka koi kaam nahi tha!

**Responsibilities:**

| Kaam | Kaun | Claude? |
|------|------|---------|
| Gmail check karna | Python Watcher | ❌ Nahi |
| .md file banana | Python Watcher | ❌ Nahi |
| File padhna & samajhna | Claude Code | ✅ Haan |
| Action lena | Claude Code | ✅ Haan |

---

**Q15: What is the purpose of the Inbox folder when we have a Gmail Watcher that automatically creates files in Needs_Action?**

**A:**
**Inbox folder Gmail ke liye nahi hai!**

| Folder | Kaun Use Karta Hai | Kaise |
|--------|-------------------|-------|
| Needs_Action/ | Gmail Watcher | Automatic |
| **Inbox/** | **Tum khud** | **Manual drag & drop** |
| Done/ | Claude Code | Automatic |

**Inbox ka real use:**
- Bank statement PDF jo tum ne website se download ki
- WhatsApp se mila contract jo tumhare computer pe hai
- Scanned receipt
- Koi bhi file jo automatically nahi aayi

**Rule:**
```
Automatically aayi (email)  →  Gmail Watcher → Needs_Action/ (direct)
Manually tumhare paas hai   →  Inbox/ mein daalo → File Watcher detect kare
```

---

**Q16: What does Claude actually do when I add a bank statement PDF to the Inbox folder? Give a real world example.**

**A:**
**Scenario:** Tum ne HBL bank website se statement download ki aur Inbox/ mein daali.

**Step 1 — Tum:**
```
HBL_January_2026.pdf → Inbox/ folder mein drag kiya
```

**Step 2 — File System Watcher (Python):**
```
File detect ki → Needs_Action/FILE_HBL_January_2026.md banayi
```

**Step 3 — Orchestrator:**
```
File dekhi → Claude Code trigger kiya
```

**Step 4 — Claude PDF padhta hai:**
```
Transactions:
- Jan 3:  Netflix           -$15
- Jan 5:  Client Ali        +$1,500
- Jan 12: Unknown - Dubai   -$850  ← Suspicious!
- Jan 15: Electricity Bill  -$45
```

**Step 5 — Claude yeh karta hai:**
- Accounting/January_2026.md update karta hai (transactions list)
- Dashboard.md update karta hai (balance: $1,160)
- Pending_Approval/ mein alert file banata hai (suspicious $850 charge)
- PDF ko Done/ mein move karta hai

**Tum sirf:** Approval dete ho — bas!

---

**Q17: Is the processing (summarize, calculate, alert) already specified, or do I mention it myself?**

**A:**
**Tum khud specify karte ho — Claude automatically nahi janta.**

**2 jagah likho:**

**1. Company_Handbook.md mein:**
```markdown
## Bank Statement Rules:
- Total income/expense calculate karo
- $500 se upar charge ho → flag karo
- Monthly summary banao
```

**2. Agent Skills mein:**
```markdown
# Skill: process_bank_statement
1. PDF padho
2. Transactions nikalo
3. Total calculate karo
4. Suspicious charges flag karo
5. Dashboard update karo
```

**Summary:**

| Cheez | Kaun Decide Karta Hai |
|-------|----------------------|
| Kya process karna hai | ✅ Tum |
| Kaise process karna hai | ✅ Tum (Handbook + Skills) |
| Actually process karna | ✅ Claude |

---

**Q18: What does "Flag any payment over $500 for my approval" mean? What is flagging?**

**A:**
**Flag = Ruko! Pehle mujhse poochho!**

```
Payment $500 se upar detect hui
        ↓
Claude khud action NAHI leta
        ↓
Pending_Approval/ mein file banata hai:

"⚠️ Payment $850 detect hui — Dubai Account
 Kya approve karoon?
 → /Approved mein daalo = Haan
 → /Rejected mein daalo = Nahi"
        ↓
Tum decision lete ho
```

**Flag = Alert + Roko + Approval Maango**

---

**Q19: Is there any restriction in the documentation on what we can write in Company_Handbook.md or Agent Skills?**

**A:**
Sirf 2 cheezein restrict hain:

| Restriction | Kyun |
|-------------|------|
| Payments automatically mat karo | Security — hamesha approval lo |
| Credentials vault mein mat rakho | Privacy — .env file use karo |

**Baaki sab tumhara apna — koi restriction nahi!**

---

**Q20: What are the common types of processing people generally want when they add different files?**

**A:**
**(Note: Yeh documentation se nahi — general best practices hain)**

| File Type | Common Processing |
|-----------|------------------|
| Bank Statement | Transactions, totals, $500+ flag, subscriptions list |
| Invoice/Receipt | Amount, vendor, due date, accounting mein add |
| Contract | Start/end date, payment terms, renewal reminder, risky clauses |
| Report/Document | 5 bullet summary, action items, deadlines, key numbers |
| Resume (HR) | Skills, experience, job match score (1-10) |

---

**Q21: What is the difference between Company_Handbook.md and Agent Skills? Do I need both?**

**A:**
**Dono alag cheezein hain — dono zaroori hain:**

|            Company_Handbook.md  |     Agent Skill     |
|--          |--------------------|        ----         |
| Kya hai?   | General rules      | Specific kaam ka procedure |
| Kitne?     | Sirf **ek**        | Har kaam ke liye **alag** |
| Example    | "Flag $500+ payments" | "Bank statement process ke exact steps" |
| Jaise      | Employee handbook  | SOP (Standard Operating Procedure) |

**Relation:**
```
Handbook kehta hai: "$500+ flag karo"
Agent Skill batata hai: "Bank statement process karne ke
                         exact steps kya hain — step 1, 2, 3..."
```

---

**Q22: For Bronze tier, thinking about Silver/Gold future, what structure should I build?**

**A:**
**Future-ready structure:**

```
AI_Employee_Vault/
├── Company_Handbook.md          ← Sirf EK (general rules)
├── .claude/
│   └── skills/
│       ├── process_bank_statement.md
│       ├── process_invoice.md
│       ├── process_contract.md
│       └── process_document.md  ← Bronze mein yeh ek general skill banao
├── Needs_Action/
├── Inbox/
├── Done/
└── Logs/
```

**Bronze mein kya banao:**

| Step |     Kya Banao             | Note |
|------|     -----------           |------|
| 1    | Company_Handbook.md       | General rules — hamesha ek rahega |
| 2    | File System Watcher       | Bronze requirement |
| 3    | process_document.md skill | Ek general skill — sab handle kare |
| 4    | Folder structure          | Silver/Gold mein same rahegi |

**Bronze mein general skill banao, Silver/Gold mein specific skills add karte jao!**

---

## SECTION 5: Quick Reference Summary

---

### Key Concepts at a Glance:

|       Concept       |        Simple Matlab         |
|      ---------      |        --------------        |
| Vault               | Sirf ek computer folder |
| Obsidian            | Tumhara visual dashboard |
| Claude Code         | AI brain — sochta aur kaam karta hai |
| Gmail Watcher       | Python script — email detect karta hai |
| File System Watcher | Python script — Inbox folder dekhta hai |
| Orchestrator.py     | Manager — Claude ko trigger karta hai |
| Needs_Action/       | Pending kaam — Claude yahan se padhta hai |
| Inbox/              | Tumhara manual drop box |
| Done/               | Complete kaam |
| Company_Handbook.md | Claude ke liye rules |
| Agent Skills        | Claude ke liye step-by-step procedures |
| Flag                | Roko + Alert + Approval maango |
| HITL                | Human-in-the-Loop — sensitive actions pe tumse poochho |

---

### Bronze Tier Complete Flow:

```
[Email aaya Gmail pe]
        ↓
[Gmail Watcher — Python — 24/7]
Email detect → Needs_Action/EMAIL_xyz.md banayi
        ↓
[File System Watcher — Python — 24/7]
Inbox mein file aayi → Needs_Action/FILE_xyz.md banayi
        ↓
[Orchestrator.py — Python — 24/7]
Needs_Action mein file dekhi → Claude Code trigger kiya
        ↓
[Claude Code — sirf jab kaam ho]
Company_Handbook.md padha → Rules samjhe
Agent Skill padha → Procedure samjha
File process ki → Action liya
Approval chahiye → Pending_Approval/ mein file banayi
Kaam hua → Done/ mein move kiya
Dashboard.md update kiya → Exit
        ↓
[Tum — Human]
Dashboard dekho → Approvals do → Monitor karo
```

---

*File created for Hackathon-0 learning documentation.*
*Discussion date: February 2026*
*Purpose: Bronze Tier video reference*
