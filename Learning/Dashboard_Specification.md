# AI Employee Dashboard — Complete Specification

This document contains the complete specification for building the Gold Tier Dashboard using Streamlit.

---

## Table of Contents

1. [Dashboard Overview](#1-dashboard-overview)
2. [Section 1: Overview Home](#2-section-1-overview-home)
3. [Section 2: Finance (Odoo)](#3-section-2-finance-odoo)
4. [Section 3: Social Media](#4-section-3-social-media)
5. [Section 4: Communications](#5-section-4-communications)
6. [Section 5: Settings](#6-section-5-settings)
7. [Section 6: Logs](#7-section-6-logs)

---

## 1. Dashboard Overview

### Purpose
Central hub to monitor and control the AI Employee system.

### Layout
- Sidebar navigation
- Main content area
- Quick stats at top

### Navigation (Sidebar)

```
┌─────────────────────────┐
│  🤖 AI EMPLOYEE       │
│                         │
│  📊 Overview          │
│  💰 Finance           │
│  📱 Social Media       │
│  💬 Communications    │
│  ⚙️ Settings          │
│  📋 Logs              │
│                         │
│  ─────────────────────│
│  Status: ● Online     │
└─────────────────────────┘
```

---

## 2. Section 1: Overview Home

### Purpose
Quick snapshot of all systems at a glance.

### Content

```
┌─────────────────────────────────────────────────────────────────────────┐
│  📊 OVERVIEW - Quick Stats                                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐    │
│  │ 💰 Revenue  │ │ 📄 Invoices │ │ ⏳ Pending  │ │ 📱 Social  │    │
│  │ This Month  │ │   Total    │ │  Approvals │ │  Accounts  │    │
│  │             │ │            │ │            │ │            │    │
│  │  PKR 285K │ │     15     │ │      2    │ │      4     │    │
│  │   ↑ 15%   │ │  8D/4P/3P  │ │            │ │  ● Online  │    │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘    │
│                                                                          │
│  [Revenue → Finance]  [Invoices → Finance]  [Pending → Approvals]     │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ 📋 RECENT ACTIVITY (Last 24 hours)                              │    │
│  │                                                                  │    │
│  │ 🟢 16:30 - Invoice #67 created - Digital Works - PKR 150K   │    │
│  │ 🟢 16:25 - Email sent to alishahzain604@gmail.com            │    │
│  │ 🟢 15:00 - Social post published - LinkedIn                    │    │
│  │ 🟡 14:30 - Approval pending - Email reply to client          │    │
│  │ 🟢 12:00 - Payment received - Ahmed Khan - PKR 50K            │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

### Data Sources

| Box | Data Source | Query |
|-----|-------------|-------|
| Revenue | Odoo | Sum of paid invoices this month |
| Invoices | Odoo | Count by status (Draft/Posted/Paid) |
| Pending | Vault | Count files in Pending_Approval/ |
| Social | All platforms | Count connected accounts |

---

## 3. Section 2: Finance (Odoo)

### Purpose
Manage all accounting operations via Odoo.

### Content

```
┌─────────────────────────────────────────────────────────────────────────┐
│  💰 FINANCE - ODOO ACCOUNTING                            [🔄 Sync]   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ MONTHLY SUMMARY (March 2026)                                    │   │
│  │                                                                  │   │
│  │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                │   │
│  │ │  REVENUE   │ │  EXPENSES  │ │   PROFIT   │                │   │
│  │ │  PKR 285K  │ │  PKR 45K   │ │  PKR 240K  │                │   │
│  │ │   ↑ 15%    │ │   ↓ 10%    │ │   ↑ 20%    │                │   │
│  │ └─────────────┘ └─────────────┘ └─────────────┘                │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ INVOICES                                            [+ Create]   │   │
│  │                                                                  │   │
│  │ Filter: [All ▼]  Status: [Any ▼]  Search...                   │   │
│  │                                                                  │   │
│  │ ┌───────────────────────────────────────────────────────────┐ │   │
│  │ │ # │ Partner        │ Amount     │ Status │ Due Date │Edit │ │   │
│  │ │ 67│ Digital Works │ PKR 150K  │ Draft  │ Mar 31  │ [⚙️]│ │   │
│  │ │ 66│ Bilal Ahmed  │ PKR 200K  │ Draft  │ Mar 15  │ [⚙️]│ │   │
│  │ │ 65│ Ahmed Khan   │ PKR 50K   │ Paid   │ Mar 5   │ [👁️]│ │   │
│  │ └───────────────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ EXPENSES                                             [+ Add]     │   │
│  │                                                                  │   │
│  │ This Month: PKR 45,000                                        │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ [📊 Generate CEO Briefing]     [📥 Export Report]               │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

### Invoice Status Explanation

| Status | Meaning | Actions Available |
|--------|---------|------------------|
| **Draft** | Just created, not sent to client | Edit, Delete, Post |
| **Posted** | Confirmed, ready to send | Send to Client, Record Payment |
| **Paid** | Payment received | View Only |

### Data Queries

```python
# Revenue - Paid invoices this month
Odoo.search(
    move_type="out_invoice",
    payment_state="paid",
    invoice_date >= "2026-03-01"
)

# Invoices - All
Odoo.search(move_type="out_invoice")

# Expenses - This month
Odoo.search(
    model="hr.expense",
    date >= "2026-03-01"
)
```

---

## 4. Section 3: Social Media

### Purpose
Manage all social media accounts and create posts.

### Platforms

| Platform | Integration | Data Available |
|----------|------------|----------------|
| Facebook | Official Meta API | Full insights, followers, likes |
| Instagram | Official Meta API | Full insights, followers, media count |
| X (Twitter) | Playwright | Limited (browser view) |
| LinkedIn | Playwright | Limited (browser view) |

### Content

```
┌─────────────────────────────────────────────────────────────────────────┐
│  📱 SOCIAL MEDIA HUB                                     [POST TO ALL]  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ 📝 CREATE NEW POST                                              │   │
│  │                                                                  │   │
│  │ Message:                                                         │   │
│  │ ┌───────────────────────────────────────────────────────────┐   │   │
│  │ │ Write your post here...                                      │   │   │
│  │ └───────────────────────────────────────────────────────────┘   │   │
│  │                                                                  │   │
│  │ Select: [☑ Facebook] [☑ Instagram] [☑ X] [ ] LinkedIn       │   │
│  │                                                                  │   │
│  │ [📷 Add Image]  [📅 Schedule]                 [POST NOW →]     │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐                │
│  │ FACEBOOK │ │INSTAGRAM │ │    X     │ │LINKEDIN │                │
│  │          │ │          │ │(Twitter) │ │          │                │
│  │ 👤12,500│ │ 👤 8,200│ │ 👤 5,100│ │ 👤 3,800│                │
│  │Followers │ │Followers │ │Followers │ │ Network  │                │
│  │          │ │          │ │          │ │          │                │
│  │[Insights]│ │[Insights]│ │ [Open]  │ │ [Open]  │                │
│  │ ●API    │ │ ●API    │ │●Browser │ │●Browser  │                │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘                │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ 📈 PERFORMANCE (This Week)                                       │   │
│  │                                                                  │   │
│  │ Platform   │ Posts │  Reach  │ Engagement │                     │
│  │ Facebook   │   3   │  45,000 │   2,500   │                     │
│  │ Instagram  │   5   │  12,000 │   1,800   │                     │
│  │ X (Twitter)│   4   │   8,500 │     450   │                     │
│  │ LinkedIn   │   2   │   3,200 │     380   │                     │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ 📋 RECENT POSTS                                                  │   │
│  │                                                                  │   │
│  │ ✅ Facebook  - "New project launch..." - 2h ago - 150 likes   │   │
│  │ ✅ Instagram - "Product showcase..." - 5h ago - 89 likes       │   │
│  │ ✅ X (Twitter) - "Exciting news..." - 1d ago - 45 likes       │   │
│  │ ✅ LinkedIn  - "Business update..." - 1d ago - 78 reactions   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Section 4: Communications

### Purpose
Manage email and WhatsApp communications.

### Platforms

| Platform | Integration | Purpose |
|----------|------------|---------|
| Email (Gmail) | Official Gmail API | Personal & business emails |
| WhatsApp | Playwright | Personal messaging |

### Content

```
┌─────────────────────────────────────────────────────────────────────────┐
│  💬 COMMUNICATIONS                                         [🔄 Refresh] │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────────────────┐  ┌──────────────────────────────┐   │
│  │         📧 GMAIL             │  │         💬 WHATSAPP          │   │
│  │                              │  │                              │   │
│  │   ● Connected              │  │   ● Session Active          │   │
│  │   alishahzain604@gmail.com│  │                              │   │
│  │                              │  │   Unread: 1               │   │
│  │   Unread: 3  |  Sent: 2   │  │   Total Chats: 12          │   │
│  │                              │  │                              │   │
│  │ [📝 Compose] [Refresh]     │  │ [💬 Open] [➕New Chat]     │   │
│  └──────────────────────────────┘  └──────────────────────────────┘   │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │ 📬 INBOX (Unread)                                                  │ │
│  │                                                                      │ │
│  │ ┌────────────────────────────────────────────────────────────────┐│ │
│  │ │ 📧 From: usmanali@client.com                                 ││ │
│  │ │ Subject: Invoice Request - Project Alpha                     ││ │
│  │ │ Preview: Please create invoice for website...                 ││ │
│  │ │ 10 minutes ago                                   [Reply →]   ││ │
│  │ ├────────────────────────────────────────────────────────────────┤│ │
│  │ │ 📧 From: bilal@techsolutions.pk                             ││ │
│  │ │ Subject: Payment Confirmation                                ││ │
│  │ │ Preview: Payment of PKR 50,000 received...                 ││ │
│  │ │ 2 hours ago                                     [Reply →]   ││ │
│  │ └────────────────────────────────────────────────────────────────┘│ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │ 📤 SENT (Recently Sent)                                             │ │
│  │                                                                      │ │
│  │ ✅ To: alishahzain604@gmail.com - Re: Invoice Request - 2h ago   │ │
│  │ ✅ To: ahmed.khan@client.com - Re: Project Update - Yesterday    │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │ 💬 WHATSAPP CONVERSATIONS                                           │ │
│  │                                                                      │ │
│  │ 👤 Ahmed Khan - "Invoice bhejna" - 5 min ago - [Reply →]          │ │
│  │ 👤 Usman Ali - "Thanks!" - 1 hour ago - [Reply →]                │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Section 5: Settings

### Purpose
Configure system, connections, and preferences.

### Content

```
┌─────────────────────────────────────────────────────────────────────────┐
│  ⚙️ SETTINGS                                              [Save]       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ 🔧 GENERAL                                                        │    │
│  │                                                                    │    │
│  │ DRY_RUN Mode:  (○ ON  ● OFF)  - Testing / Real               │    │
│  │ Poll Interval:    [60] seconds - How often to check             │    │
│  │ Claude Timeout:   [600] seconds - Max time for AI task          │    │
│  │ MCP Idle Timeout: [30] seconds - Auto-stop containers            │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ 🐳 DOCKER - ODOO                                                  │    │
│  │                                                                    │    │
│  │ Status: ● Running  |  Containers: odoo-1, postgres-1            │    │
│  │                                                                    │    │
│  │ [Start]  [Stop]  [Restart]  |  Auto-Stop: ☑ Enabled           │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ 📧 EMAIL (GMAIL)                                                  │    │
│  │                                                                    │    │
│  │ ● Connected  |  alishahzain604@gmail.com                        │    │
│  │ Last Sync: 5 minutes ago                                         │    │
│  │                                                                    │    │
│  │ [Re-authenticate]  [Test Connection]                             │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ 📱 SOCIAL ACCOUNTS                                                │    │
│  │                                                                    │    │
│  │ Facebook:    ● Connected (@yourpage)      [Reconnect]           │    │
│  │ Instagram:   ● Connected (@yourhandle)    [Reconnect]           │    │
│  │ X (Twitter): ○ Not Setup                  [Setup]              │    │
│  │ LinkedIn:    ○ Not Setup                  [Setup]              │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ 💬 WHATSAPP                                                       │    │
│  │                                                                    │    │
│  │ ● Session Active  |  Last: 10 min ago                          │    │
│  │                                                                    │    │
│  │ [Refresh Session]  [New Session]                                │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ 🔐 APPROVAL RULES                                                 │    │
│  │                                                                    │    │
│  │ Invoice Creation........... ☑ Auto-Approve  |  ☐ Require        │    │
│  │ Invoice Reply Email....... ☑ Auto-Approve  |  ☐ Require        │    │
│  │ Payment Recording........ ☐ Auto-Approve  |  ☑ Require         │    │
│  │ External Email Reply..... ☐ Auto-Approve  |  ☑ Require         │    │
│  │ Social Media Post........ ☐ Auto-Approve  |  ☑ Require         │    │
│  │                                                                    │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ 📋 LOGS & AUDIT                                                   │    │
│  │                                                                    │    │
│  │ Location: AI_Employee_Vault/Logs/                                 │    │
│  │ Retention: [90] days                                             │    │
│  │                                                                    │    │
│  │ [View Logs]  [Export]  [Clear Old]                               │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ ℹ️ ABOUT                                                          │    │
│  │                                                                    │    │
│  │ Version: Gold Tier v1.0                                          │    │
│  │ Claude: Opus 4.6                                                 │    │
│  │ Updated: March 6, 2026                                          │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

### Settings Explanation

| Setting | Description | Default |
|---------|------------|---------|
| DRY_RUN | Test mode (no real actions) | OFF |
| Poll Interval | How often watchers check for new items | 60s |
| Claude Timeout | Max time for AI to complete task | 600s |
| MCP Idle Timeout | Auto-stop Odoo after idle | 30s |
| Auto-Stop | Automatically stop Docker when idle | Enabled |

---

## 7. Section 6: Logs

### Purpose
View all system activities and audit trail.

### Content

```
┌─────────────────────────────────────────────────────────────────────────┐
│  📋 ACTIVITY LOGS                                                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Filter: [All ▼]  Date: [Today ▼]  Search: [____________]            │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │ 🟢 16:30 - Invoice Created                                     │    │
│  │    Digital Works - PKR 150,000                                 │    │
│  │    Source: Email | Approval: Auto-Approved                     │    │
│  ├────────────────────────────────────────────────────────────────┤    │
│  │ 🟢 16:25 - Email Sent                                         │    │
│  │    To: alishahzain604@gmail.com                               │    │
│  │    Subject: Re: Invoice Request                               │    │
│  ├────────────────────────────────────────────────────────────────┤    │
│  │ 🟡 15:45 - Approval Pending                                   │    │
│  │    Email reply to client                                      │    │
│  │    Reason: External contact                                    │    │
│  ├────────────────────────────────────────────────────────────────┤    │
│  │ 🔴 14:30 - Error                                              │    │
│  │    Odoo connection failed                                     │    │
│  │    Message: Connection timeout                                │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  Showing 4 of 47 entries                               [Export Logs]    │
└─────────────────────────────────────────────────────────────────────────┘
```

### Log Entry Format

```json
{
  "timestamp": "2026-03-06T16:30:00Z",
  "action_type": "invoice_created",
  "source": "email_responder",
  "status": "success",
  "target_file": "Needs_Action/EMAIL_abc123.md",
  "details": {
    "partner": "Digital Works",
    "amount": 150000,
    "invoice_id": 67
  },
  "approval_status": "auto_approved",
  "domain": ["email", "odoo"]
}
```

### Log Status Colors

| Color | Meaning |
|-------|---------|
| 🟢 Green | Success - action completed |
| 🟡 Yellow | Warning - attention needed |
| 🔴 Red | Error - action failed |

---

## Implementation Notes

### Tech Stack
- **Framework:** Streamlit
- **Language:** Python
- **Data:** From Odoo (JSON-RPC), Gmail (API), Vault (files)

### Key Functions Needed

```python
# Odoo Functions
get_revenue_this_month()
get_invoices(status="all")
get_expenses()
create_invoice(partner, lines, due_date)
get_weekly_summary()

# Gmail Functions
get_unread_emails()
get_sent_emails()
send_email(to, subject, body)

# Social Functions
get_social_stats(platform)
create_post(platforms, message)
get_recent_posts()

# System Functions
get_approval_count()
get_recent_activity()
start_odoo_containers()
stop_odoo_containers()
```

---

## File Information

- **Created:** March 6, 2026
- **Version:** 1.0
- **Purpose:** Dashboard Specification
