# Silver Tier — Q&A Discussion Guide (Roman Urdu)

> **Yeh guide Silver Tier ke baare mein sab common sawaal aur jawab cover karta hai.**
> Classmates ke liye tayyar kiya gaya — video aur review ke liye perfect reference.

---

## Section 1 — Silver Tier Kya Hai? Bronze Se Farq?

**Q: Bronze Tier aur Silver Tier mein basic farq kya hai?**

A: Bronze Tier ek **local** system tha — sirf tumhare laptop ke files dekhta tha. Silver Tier **internet se connect** hota hai. Ab AI Employee Gmail aur WhatsApp jaise real services ko monitor karta hai.

```
BRONZE TIER:
  Inbox/ folder → Watcher → Orchestrator → Claude → Done/

SILVER TIER:
  Gmail / WhatsApp → Watcher → Orchestrator → Claude → LinkedIn post / Email reply
```

**Q: Kya Bronze ka code waste ho gaya?**

A: Bilkul nahi. Silver Tier Bronze ke upar build hota hai. Orchestrator, Vault, Dashboard — yeh sab wahi hain. Sirf **watchers** badlay hain — ab filesystem ki jagah Gmail aur WhatsApp ko watch karte hain.

**Q: Silver Tier mein kya kya naya aata hai?**

A: Teeen main cheezein:

| Nayi Cheez | Kya karta hai |
|------------|--------------|
| **External Watchers** | Gmail aur WhatsApp se messages uthata hai |
| **Playwright** | Browser ko automatically chalata hai — LinkedIn pe post karta hai |
| **Human Approval** | Koi bhi action karne se pehle insaan se confirm leta hai |

**Q: Silver Tier ka maqsad kya hai?**

A: AI Employee ab sirf file processor nahi — ab woh:
- Aapke emails padhta hai
- WhatsApp messages dekhta hai
- Automatically LinkedIn pe posts karta hai
- Lekin koi bhi bada kaam karne se **pehle aapse poochta hai**

---

## Section 2 — Watchers: Gmail aur WhatsApp

**Q: Gmail Watcher kaise kaam karta hai?**

A: Gmail Watcher **Gmail API** use karta hai. Yeh OAuth2 se authenticate hota hai, aur phir inbox check karta hai. Jab koi email aata hai, woh usse `Needs_Action/` mein daal deta hai — bilkul waise jaise Bronze mein file aane pe hota tha.

```
Gmail Inbox
    ↓
Gmail API (OAuth2)
    ↓
GmailWatcher.check_new_messages()
    ↓
Needs_Action/EMAIL_subject.md (action file)
    ↓
Orchestrator → Claude
```

**Q: Gmail ke liye credentials kahan se aate hain?**

A: Google Cloud Console se. Process yeh hai:

1. Google Cloud Console mein project banao
2. Gmail API enable karo
3. OAuth2 credentials download karo (`credentials.json`)
4. Pehli baar run karo — browser khulega, permission do
5. `token.json` save ho jaye ga — agla baar automatic login

**Q: WhatsApp Watcher kaise kaam karta hai?**

A: WhatsApp ke liye **Twilio WhatsApp API** ya **WhatsApp Business API** use hoti hai. Yeh ek **webhook** system hai:

```
WhatsApp message aaya
    ↓
Twilio webhook → tumhara server
    ↓
WhatsAppWatcher.process_incoming()
    ↓
Needs_Action/WA_sender_timestamp.md
    ↓
Orchestrator → Claude
```

**Q: Kya personal WhatsApp se direct connect ho sakta hai?**

A: Seedha nahi. Personal WhatsApp ka official API nahi hai. Options:

| Option | Pros | Cons |
|--------|------|------|
| **Twilio WhatsApp** | Official, reliable | Paid, number verify karna parta hai |
| **WhatsApp Business API** | Official Meta API | Business verification chahiye |
| **Baileys (unofficial)** | Free, personal number | Terms of Service violation ka risk |

**Recommended:** Twilio WhatsApp — safe aur kaam karta hai.

**Q: Dono watchers saath kaise chalte hain?**

A: Har watcher ek alag **thread** mein chalta hai, aur dono simultaneously monitor karte hain:

```python
# main.py mein concept
threads = [
    Thread(target=gmail_watcher.run),
    Thread(target=whatsapp_watcher.run),
    Thread(target=orchestrator.run),
]
```

---

## Section 3 — Playwright: Kya Hai, Kisne Banaya, Security

**Q: Playwright kya hai?**

A: Playwright ek **browser automation library** hai. Iska matlab: aap code likh ke browser ko control kar sakte ho — bilkul insaan ki tarah.

```python
# Playwright example: website pe jaao, button dabaao
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto("https://linkedin.com")
    page.fill("#username", "email@example.com")
    page.click("button[type=submit]")
```

**Q: Kisne banaya Playwright?**

A: **Microsoft** ne banaya — 2020 mein release kiya. Pehle Selenium ka alternative tha. Ab yeh industry standard ban gaya hai. Python, JavaScript, TypeScript, Java, C# — sab mein kaam karta hai.

**Q: Playwright aur Selenium mein farq kya hai?**

A:

| Feature | Playwright | Selenium |
|---------|-----------|---------|
| **Speed** | Fast (modern architecture) | Slower |
| **Auto-wait** | Haan — element ready hone ka khud intezaar karta hai | Nahi — manually wait likhna parta hai |
| **Multi-browser** | Chrome, Firefox, Safari | Chrome, Firefox, Safari |
| **Banaya kisne** | Microsoft | Open source community |
| **JS execution** | Built-in | Alag se likhna parta hai |

**Q: Playwright secure hai? LinkedIn block nahi karta?**

A: Yeh important sawaal hai. Kuch key points:

1. **Bot detection exist karta hai** — LinkedIn, Google sab detect kar sakte hain agar behavior robotic lage
2. **Mitigations:**
   - `playwright-stealth` plugin use karo
   - Random delays daalo clicks ke darmiyan
   - Headful mode (visible browser) use karo headless ki jagah
   - Human-like mouse movements simulate karo
3. **Rate limiting** — zyada baar login mat karo, natural behavior raho
4. **Terms of Service** — LinkedIn ka ToS bot use ko restrict karta hai, isliye human approval important hai

**Q: Playwright install kaise hota hai?**

A:
```bash
uv add playwright
uv run playwright install chromium
```

---

## Section 4 — LinkedIn Auto Post: Flow aur Playwright Ka Use

**Q: LinkedIn post ka complete flow kya hai?**

A: Step by step:

```
1. Gmail/WhatsApp se trigger aaya
         ↓
2. Orchestrator ne Claude ko call kiya
         ↓
3. Claude ne content generate kiya (post text)
         ↓
4. Human Approval: "Kya yeh post karna chahte ho?" → Haan/Nahi
         ↓
5. Approved? → Playwright chalao
         ↓
6. Playwright ne LinkedIn kholaa
   - Login kiya (agar zarurat ho)
   - "Start a post" click kiya
   - Content paste kiya
   - "Post" button dabaya
         ↓
7. Done! Dashboard update hua
```

**Q: Claude content kaise generate karta hai?**

A: Claude ko ek skill file di jati hai. Maslan `linkedin_post.md` skill mein instructions hoti hain:

```
Skill: LinkedIn Post Generator
Input: Email/WhatsApp message
Task: Iss message se professional LinkedIn post banao
Format: 3-5 lines, engaging hook, relevant hashtags
```

Claude yeh skill padhta hai, input content dekhta hai, aur post draft karta hai.

**Q: Agar LinkedIn ka layout change ho jaye to kya hoga?**

A: Playwright ka code break ho sakta hai. Isliye:
- CSS selectors ki jagah **ARIA labels** use karo (zyada stable hote hain)
- Screenshots le ke debug karo
- `page.get_by_role("button", name="Post")` — yeh zyada reliable hai `page.click(".post-btn")` se

**Q: Kya multiple posts ek saath ho sakti hain?**

A: Haan, lekin better hai ek ek post karo — aur har post ke liye alag human approval lo. Zyada spam-like behavior LinkedIn detect kar sakta hai.

---

## Section 5 — Claude Reasoning Loop + Plan.md

**Q: Claude Reasoning Loop kya hota hai?**

A: Yeh Silver Tier ka ek key concept hai. Bronze mein Claude sirf ek kaam karta tha — file process karo. Silver mein Claude **sochta hai pehle**, phir kaam karta hai.

```
Input aaya
    ↓
Claude: "Mujhe pehle plan banana chahiye"
    ↓
Plan.md mein likhta hai:
  - Step 1: Email padhna
  - Step 2: Relevant content dhundhna
  - Step 3: LinkedIn post draft karna
  - Step 4: Human se approval lena
    ↓
Har step execute karta hai
    ↓
Agar kuch fail ho to plan revisit karta hai
```

**Q: Plan.md kya hota hai?**

A: Plan.md ek temporary working file hai jahan Claude apna action plan likhta hai. Yeh **not** project ki permanent plan file — yeh ek scratchpad hai jo Claude ek task ke liye use karta hai.

**Q: Kyun Plan.md zaruri hai? Seedha kaam kyon nahi karta?**

A: 3 reasons:

1. **Transparency** — Tum dekh sako Claude kya karne wala hai, approve/reject kar sako
2. **Recovery** — Agar beech mein fail ho, plan se resume kar sako
3. **Human Approval** — Plan dikhao, insaan review kare, phir execute karo

**Q: Kya Claude khud plan change kar sakta hai?**

A: Haan — agar execution mein kuch unexpected aaye, Claude plan update karta hai. Maslan: "Email ka attachment nahi khul raha — alternative approach try karta hoon."

---

## Section 6 — MCP Server: Email Bhejna

**Q: MCP Server kya hai?**

A: **Model Context Protocol** — Anthropic ne banaya. Yeh ek standard hai jisse Claude external tools aur services se baat kar sakta hai directly.

```
Claude ←→ MCP Server ←→ External Service
                          (Gmail, Slack, etc.)
```

**Q: MCP Server se email kaise bheja jata hai?**

A: Process:

```
1. Claude decide karta hai: "Yeh email bhejna chahiye"
         ↓
2. MCP tool call karta hai:
   send_email(to="user@example.com", subject="...", body="...")
         ↓
3. MCP Server yeh request receive karta hai
         ↓
4. Gmail API / SMTP use karke email bhejta hai
         ↓
5. Confirmation Claude ko milti hai
```

**Q: MCP Server Bronze mein tha? Silver mein kya naya hai?**

A:
- **Bronze:** MCP nahi tha — Claude sirf files likhta tha
- **Silver:** MCP servers add kiye — Claude ab directly APIs call kar sakta hai

**Q: Kaunse MCP servers Silver mein use honge?**

A: Main ones:

| MCP Server | Kaam |
|------------|------|
| `gmail-mcp` | Email padhna aur bhejna |
| `filesystem-mcp` | Files read/write (Bronze wala) |
| `slack-mcp` (optional) | Slack messages |

**Q: MCP Server secure hai?**

A: Security ke liye:
- API keys `.env` mein rakhni chahiye — kabhi hardcode mat karo
- MCP server ko sirf localhost pe chalao — public expose mat karo
- Rate limits set karo taake accidentally zyada emails na jayein

---

## Section 7 — Human Approval: Kaise Dete Hain

**Q: Human Approval kyon zaruri hai Silver Tier mein?**

A: Bronze mein Claude sirf local files process karta tha — galti hogi to file delete karo, redo karo. Silver mein Claude **real actions** karta hai:
- Email bhejta hai (wapas nahi hoti)
- LinkedIn post karta hai (public)
- WhatsApp message bhejta hai

Isliye **har important action se pehle** human se confirm lena zaruri hai.

**Q: Approval flow technically kaise kaam karta hai?**

A: Do approaches hain:

**Approach 1: File-based approval**
```
1. Claude writes: Pending_Approval/ACTION_linkedin_post.md
   Content:
   ---
   Action: LinkedIn Post
   Content: "Excited to share our new project..."
   Approve? YES/NO
   ---

2. Tum file kholo, "YES" likho, save karo

3. Orchestrator detect karta hai → action execute karta hai
```

**Approach 2: CLI/Terminal approval**
```
1. Orchestrator terminal mein print karta hai:
   "Kya LinkedIn pe yeh post karna chahte ho? (y/n)"

2. Tum keyboard pe "y" ya "n" dabaate ho

3. Action execute ya cancel hota hai
```

**Q: Agar main approval nahi deta aur system wait karta rahe?**

A: System `Pending_Approval/` folder mein file rakhta hai aur **continue karta hai doosre kaam**. Yeh blocking operation nahi hai. Jab tum approve karo tab execute hoga.

**Q: Ek saath kai approvals hon to kya hoga?**

A: Queue system hoga. `Pending_Approval/` mein multiple files hongi. Tum ek ek review karo. Orchestrator sequence mein process karega.

**Q: Kya auto-approve bhi ho sakta hai?**

A: Technically haan — but **strongly recommended nahi** for Silver Tier. Auto-approve ka matlab Silver ka point khatam — human oversight silver tier ka core value hai.

---

## Section 8 — Cron / Task Scheduler: Real Examples

**Q: Cron kya hota hai?**

A: Cron ek **time-based job scheduler** hai Linux mein. Iska kaam hai: "Yeh command is time pe chalao."

```bash
# Cron syntax:
# minute  hour  day  month  weekday  command
  *       *     *    *      *        /command/to/run

# Examples:
  0       9     *    *      1-5      python check_email.py
  # Monday-Friday, 9 AM pe email check karo

  */30    *     *    *      *        python check_whatsapp.py
  # Har 30 minute pe WhatsApp check karo

  0       8     *    *      1        python weekly_report.py
  # Har Monday 8 AM pe weekly report banao
```

**Q: Silver Tier mein cron kaise use hoga?**

A: Kuch real examples:

```bash
# Crontab mein add karo (crontab -e se edit karo)

# Har 5 minute pe Gmail check karo
*/5 * * * * /path/to/project/run.sh check-gmail

# Subah 9 baje daily briefing banao
0 9 * * * /path/to/project/run.sh daily-briefing

# Har Monday LinkedIn weekly summary post karo
0 10 * * 1 /path/to/project/run.sh linkedin-weekly

# Raat ko 11 baje sab pending approvals clear karo (optional)
0 23 * * * /path/to/project/run.sh process-pending
```

**Q: Cron ki jagah koi aur option bhi hai?**

A: Haan:

| Tool | Platform | Best For |
|------|----------|----------|
| **Cron** | Linux/Mac | Simple, always available |
| **Task Scheduler** | Windows | Windows users ke liye |
| **APScheduler** | Python library | Python ke andar hi schedule |
| **Celery Beat** | Python | Complex workflows, distributed |

Silver Tier mein `APScheduler` acha option hai kyunki yeh Python code ke andar hi chal sakta hai — alag cron job banana nahi parta.

```python
# APScheduler example
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(check_gmail, 'interval', minutes=5)
scheduler.add_job(daily_briefing, 'cron', hour=9, minute=0)
scheduler.start()
```

**Q: Agar scheduled task fail ho jaye to kya hoga?**

A: Error handling zaruri hai:

```python
def check_gmail():
    try:
        gmail_watcher.check_new_messages()
    except Exception as e:
        # Log error, send alert, continue
        logger.error(f"Gmail check failed: {e}")
        # Next scheduled run pe phir try karega
```

---

## Section 9 — Agent Skills: Konsi Skills Banegi

**Q: Silver Tier mein kaunsi agent skills hongi?**

A: Bronze mein ek skill thi — `process_document.md`. Silver mein multiple specialized skills banegi:

| Skill File | Kaam |
|-----------|------|
| `email_responder.md` | Email padhna, appropriate reply draft karna |
| `whatsapp_handler.md` | WhatsApp message handle karna |
| `linkedin_poster.md` | LinkedIn ke liye content generate karna |
| `daily_briefing.md` | Saare pending items ka summary banana |
| `content_creator.md` | Different platforms ke liye content adapt karna |

**Q: Skill file kaise likhte hain?**

A: Skill file plain markdown mein hoti hai. Claude isko padhta hai aur samajhta hai kya karna hai:

```markdown
# Skill: Email Responder

## Purpose
Incoming emails ko padhna aur professional replies draft karna.

## Input
- Email subject
- Email body
- Sender information

## Rules
- Always professional tone use karo
- Agar urgent hai, mark karo "URGENT" flag ke saath
- Agar attachment hai, summary include karo
- Reply 3-5 sentences se zyada mat karo jab tak zarurat na ho

## Output Format
Reply ko yeh format mein likho:
Subject: Re: [original subject]
Body: [reply text]
Action Required: [YES/NO - human approval chahiye?]
```

**Q: Skills kitni specific honi chahiye?**

A: Balance rakho:
- **Too generic:** "Handle all communications" — Claude confuse hoga
- **Too specific:** "Agar email 47 characters se chhota ho aur subject mein 'urgent' ho..." — over-engineered
- **Just right:** Clear purpose, clear input/output, kuch rules

**Q: Kya skills ek doosre ko call kar sakti hain?**

A: Directly nahi — skills Claude ke instructions hain, code nahi. Lekin Claude ek task pe multiple skills consult kar sakta hai. Maslan: email aaya → `email_responder.md` padha → content banana hai to `content_creator.md` bhi padha.

---

## Section 10 — Dashboard: Silver Mein Update

**Q: Bronze ka Dashboard kaisa tha?**

A: Bronze ka `Dashboard.md` simple tha:

```markdown
# AI Employee Dashboard
Last Updated: 2026-02-18 10:30:00
Total Processed: 5
Today: 2
Pending: 0
```

**Q: Silver mein Dashboard kaise badlega?**

A: Silver Dashboard zyada information dikhayega:

```markdown
# AI Employee Dashboard — Silver Tier
Last Updated: 2026-02-18 15:45:00

## Today's Activity
- Emails Processed: 12
- WhatsApp Messages: 3
- LinkedIn Posts: 1

## Pending Approvals
- [ ] LinkedIn Post: "Excited to share..." (2026-02-18 14:30)
- [ ] Email Reply to john@example.com (2026-02-18 15:00)

## Recent Actions
- ✅ Email replied to sarah@company.com — "Project update sent"
- ✅ LinkedIn post published — 45 impressions so far
- ⏳ WhatsApp message pending approval

## Watchers Status
- Gmail Watcher: ✅ Running (last check: 2 min ago)
- WhatsApp Watcher: ✅ Running (last check: 5 min ago)

## Stats
- Total Emails Processed: 47
- Total Posts Created: 8
- Human Approvals Given: 23
- Actions Rejected: 2
```

**Q: Dashboard automatically update hota hai?**

A: Haan — Silver Tier mein Dashboard ko Orchestrator har kaam ke baad update karta hai, Bronze ki tarah. Silver mein zyada fields update honge — watchers status, pending approvals, platform-specific stats.

**Q: Kya Dashboard ko web UI bana sakte hain?**

A: Yeh Gold Tier ka concept hai. Silver mein Dashboard ek markdown file hi rahega — lekin yeh Obsidian ya VS Code mein preview kar sakte ho nicely formatted.

---

## Silver Tier — Complete Flow Ek Nazar Mein

```
EXTERNAL WORLD                    SILVER TIER SYSTEM
─────────────────                 ──────────────────────────────────

Gmail Inbox      ──→ GmailWatcher ──→ Needs_Action/EMAIL_*.md ──┐
WhatsApp         ──→ WAWatcher    ──→ Needs_Action/WA_*.md    ──┤
                                                                  ↓
                                              Orchestrator (har 5 min poll)
                                                        ↓
                                          Claude ko call karo (with skill)
                                                        ↓
                                        Claude: Plan.md likhta hai
                                        Claude: Content/reply generate karta hai
                                        Claude: Human Approval request karta hai
                                                        ↓
                                          Pending_Approval/ mein file
                                                        ↓
                                       HUMAN REVIEWS ←─── TUM
                                       Approve / Reject
                                                        ↓
                              ┌── Approved ──────────────────────────┐
                              ↓                                       ↓
                    LinkedIn (Playwright)                    Email Reply (MCP)
                    Post publish hogi                        Email bheja jaye ga
                              ↓                                       ↓
                         Dashboard.md update ←────────────────────────┘
                         Done/ mein move
                         Logs/ mein entry
```

---

## Quick Reference — Silver Tier Commands

```bash
# Gmail Watcher test karo
uv run python3 -c "from src.watchers.gmail_watcher import GmailWatcher; ..."

# Playwright install karo
uv add playwright && uv run playwright install chromium

# Pending approvals dekho
ls AI_Employee_Vault/Pending_Approval/

# Dashboard dekho
cat AI_Employee_Vault/Dashboard.md

# Crontab edit karo
crontab -e

# Logs dekho
cat AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json
```

---

---

## Section 11 — LinkedIn Ban Risk aur Stealth Mode

**Q: Kya Playwright se LinkedIn account permanently ban ho sakta hai?**

A: Haan, ban ho sakta hai. LinkedIn ka Terms of Service automation tools ko restrict karta hai.

| Risk Level | Kya Ho Sakta Hai |
|------------|-----------------|
| First time | Temporary restriction (24-72 hours) |
| Second time | Account warning |
| Repeated | Permanent ban |

Koi 100% guarantee nahi. Isliye **official account use mat karo Playwright ke liye**.

**Q: Toh phir kya approach use karein?**

A: Test account approach:

```
1. Naya Gmail banao (e.g., yourname.fte.test@gmail.com)
2. Us Gmail se naya LinkedIn test account banao
3. Playwright us test account pe chalao
4. Official LinkedIn account bilkul safe rahe
```

Hackathon demo ke liye yeh perfectly valid hai. Judges ko system ka flow dikhana hai — test account se woh bhi ho jata hai.

**Q: Stealth mode kya hota hai? Kyun use karte hain?**

A: Normal Playwright browser mein ek sign hota hai jo batata hai yeh automated bot hai:

```
navigator.webdriver = TRUE  ← LinkedIn ko pata chal jaata hai
```

`playwright-stealth` library yeh sign hide karti hai:

```python
from playwright_stealth import stealth_sync
page = browser.new_page()
stealth_sync(page)  # Browser ab "real human" jaisa lagtaa hai
```

| Normal Playwright | Stealth Mode |
|-------------------|--------------|
| webdriver = TRUE | webdriver = FALSE |
| Robot timing | Random human-like delays |
| Fake fingerprint | Real Chrome fingerprint |

Simple shabdon mein: **Stealth mode = bot ko insaan ki tarah dikhana.**

---

## Section 12 — Claude Token Limit aur Kiro Fallback

**Q: Agar Claude ka token limit exceed ho jaye to FTE flow pe kya impact hoga?**

A: Watchers chalta rahenge (emails/WhatsApp detect hote rahenge) — sirf Claude processing rukegi.

```
Normal:
Action file → Claude → Done

Limit hit hone pe:
Action file → Claude ❌ → File Needs_Action/ mein stuck
```

**Q: Isko kaise handle karte hain?**

A: Teen layer approach:

1. **Retry Logic** — 3 attempts, har baar 5 minute wait
2. **Queue** — File Needs_Action/ mein pending rahe, miss nahi hogi
3. **Dashboard Alert** — "Claude unavailable" dikhaye

**Q: Kiro kya hai aur yeh kaise help karta hai?**

A: Kiro ek IDE hai jisme Claude ke 500 free credits milte hain. Jab Anthropic ke credits khatam hoon, Kiro gateway ke zariye Claude use kar sakte hain.

```
Normal:
WSL → claude → Anthropic API

Kiro Fallback:
WSL → ccr code → Kiro Gateway (localhost:8000) → Kiro Credits
```

**Q: Kiro setup kaise karte hain? (Already cloned: C:\Users\TechLink\Desktop\Kiro-setup\kiro-openai-gateway)**

A: 3 terminal approach:

**Terminal 1 — Windows PowerShell (Gateway start karo):**
```bash
cd C:\Users\TechLink\Desktop\Kiro-setup\kiro-openai-gateway
python main.py
# Output: Server running at http://localhost:8000
```

**Terminal 2 — WSL (Router install + start karo):**
```bash
# Ek baar install (agar nahi kiya)
npm install -g @musistudio/claude-code-router

# Config banao (ek baar)
mkdir -p ~/.claude-code-router
cat > ~/.claude-code-router/config.json << 'EOF'
{
  "Providers": [
    {
      "name": "kiro",
      "api_base_url": "http://localhost:8000/v1/chat/completions",
      "api_key": "my-super-secret-password-123",
      "models": ["claude-sonnet-4-5"],
      "transformer": { "use": ["openrouter"] }
    }
  ],
  "Router": {
    "default": "kiro,claude-sonnet-4-5"
  }
}
EOF

# Router start karo
ccr start
```

**Terminal 3 — WSL (Kiro se kaam karo):**
```bash
ccr code   # Kiro credits use hoti hain
```

**Q: Daily workflow kya hoga?**

A:
```
Claude limit theek hai? → claude (normal use)

Claude limit hit? →
  1. Windows: python main.py  (gateway)
  2. WSL:     ccr start       (router)
  3. WSL:     ccr code        (use karo)
```

**Q: Yeh Silver Tier spec mein kahaan mention hai?**

A: plan.md ke Risk Analysis section mein ek line add ki gayi hai as optional mitigation — tasks mein separate task nahi banaya kyunki yeh optional/fallback feature hai, core requirement nahi.

---

*Silver Tier — AI Employee Hackathon-0*
*Guide version: 2026-02-18*
