# Meta Graph API — Complete Setup Guide (Facebook + Instagram)

**Date:** 2026-03-03
**Author:** Shahzain Bangash + Claude Opus 4.6
**Status:** FULLY WORKING — Facebook (Post/Comment/Reply) + Instagram (Post/Comment/Reply)

---

## Overview

Ye guide step-by-step batati hai ke kaise Meta Graph API setup karke Facebook Page aur Instagram pe automated posting, commenting, aur replying ki ja sakti hai.

### Kya Kya Automate Ho Sakta Hai?

| Platform | Post | Comment | Reply | Account Type |
|---|---|---|---|---|
| Facebook Page | YES | YES | YES | Page (not personal) |
| Instagram | YES | YES | YES | Creator/Business account |

### Important Limitations
- **Facebook Personal Profile pe API se post NAHI ho sakta** — Meta ne 2018 mein band kiya
- **Instagram Personal account pe API se kuch NAHI ho sakta** — Creator/Business chahiye
- **Instagram API Facebook ke through kaam karta hai** — Page connection zaroori hai

---

## Prerequisites (Ye Pehle Se Hona Chahiye)

1. Facebook account (personal — login ke liye)
2. Facebook Page (content posting ke liye)
3. Instagram Creator/Business account
4. Instagram account Facebook Page se connected

---

## Phase 1: Facebook Page Banana

### Steps:
1. Facebook open karo → Login karo
2. Left sidebar mein **"Pages"** click karo
3. **"Create New Page"** click karo
4. Page details fill karo:
   - **Page Name:** Jo bhi naam chahiye (e.g., "Agentive Solutions")
   - **Category:** Jo tumhare content se match kare (e.g., "Science & Tech")
   - **Bio:** Short description likho
5. **"Create Page"** click karo
6. Profile picture aur cover photo upload karo (optional)

**Result:** Facebook Page ban gaya.

---

## Phase 2: Instagram Creator Account Banana

### Steps:
1. **Instagram App** open karo phone pe
2. Apni **Profile** pe jao (bottom right corner)
3. **Hamburger menu** (three lines) tap karo — top right
4. **"Settings and privacy"** tap karo
5. Scroll down → **"Account type and tools"** tap karo
6. **"Switch to professional account"** tap karo
7. **"Creator"** select karo (Business nahi, Creator recommended)
8. Category choose karo (e.g., "Digital Creator", "Blogger")
9. Contact info add karo ya **"Don't use my contact info"** select karo
10. **"Done"** tap karo

### Creator vs Business vs Personal:
| Feature | Personal | Creator | Business |
|---|---|---|---|
| API access | NO | YES | YES |
| Insights/Analytics | No | Yes | Yes |
| Contact button | No | Yes | Yes |
| Facebook Page connect | No | YES | YES |
| Best for | Normal use | Influencers, content creators | Brands, shops |

**Recommendation:** Creator account lo — API access milta hai aur profile personal jaisi dikhti hai.

**Result:** Instagram Creator account ready.

---

## Phase 3: Instagram Ko Facebook Page Se Connect Karna

### Steps:
1. **Instagram App** open karo
2. **Profile** pe jao → **"Edit Profile"** tap karo
3. **"Page"** option dhundo (Public business information ke under)
4. **"Connect or Create"** tap karo
5. Facebook login karo agar puche
6. Apna **Facebook Page select karo** (e.g., "Agentive Solutions")
7. **"Done"** tap karo

### Verify (Facebook side se):
1. **Facebook** open karo desktop pe
2. Apna **Page** open karo
3. **"Settings"** jao
4. **"Linked Accounts"** ya **"Instagram"** click karo
5. Instagram account dikhna chahiye connected

**Result:** Instagram aur Facebook Page connected.

---

## Phase 4: Meta Developer App Banana

### 4.1 — Developer Portal Pe Jao
1. Browser open karo (Desktop use karo)
2. URL: **developers.facebook.com**
3. Facebook account se automatically login ho jayega
4. **"Get Started"** ya **"My Apps"** click karo
5. Developer terms accept karo

### 4.2 — New App Create Karo
1. **"Create App"** button click karo
2. **App name** likho → e.g., `FTE Social Manager`
3. **Contact email** confirm karo
4. **"Next"** click karo

### 4.3 — Use Case Select Karo
1. **"Other"** select karo
2. **"Next"** click karo
3. App type: **"Business"** select karo (NOT Consumer)
4. **"Next"** click karo

### 4.4 — App Details
1. **App Name:** `FTE Social Manager`
2. **Contact Email:** tumhara email
3. **Business Account:** skip ya "No Business Manager"
4. **"Create App"** click karo
5. Password confirm karo

**Result:** Developer App ban gaya — App ID aur App Secret milte hain.

### 4.5 — Facebook Login Product Add Karo
1. App Dashboard → left side **"Add Product"**
2. **"Facebook Login for Business"** add karo → **"Set Up"** click karo

### 4.6 — Permissions Check Karo
1. Left side: **"App Review"** → **"Permissions and Features"**
2. Ye permissions search karo — sab "Ready to use" honi chahiye:

| Permission | Purpose | Status Needed |
|---|---|---|
| `pages_manage_posts` | Page pe post karna | Ready to use |
| `pages_read_engagement` | Comments padhna | Ready to use |
| `pages_manage_engagement` | Comments reply karna | Ready to use |
| `pages_show_list` | Pages ki list dekhna | Ready to use |
| `instagram_basic` | Instagram account access | Ready to use |
| `instagram_content_publish` | Instagram pe post karna | Ready to use |
| `instagram_manage_comments` | Instagram comments manage | Ready to use |

**Note:** Development mode mein ye sab permissions bina App Review ke kaam karti hain (sirf tumhare account pe).

---

## Phase 5: Business Portfolio Se App Connect Karna

### IMPORTANT — Ye Step Zaroori Hai!

Agar tumhara Facebook Page "New Pages Experience" pe hai (jo 2024+ mein default hai), toh Page **Business Portfolio** ke through managed hota hai. Is case mein normal `me/accounts` API call empty data return karti hai.

### Problem Jo Hum Ne Face Ki:
- Graph API Explorer mein `me/accounts` empty `{"data": []}` return karta tha
- Direct Page ID se query karne pe "does not exist or missing permissions" error aata tha
- Token generate hota tha lekin Page access nahi milta tha

### Solution — App Ko Business Portfolio Se Connect Karo:

1. Browser mein jao: **business.facebook.com/settings/**
2. Left side mein **Accounts** → **"Apps"** click karo
3. **"+ Add"** click karo
4. Apna **App ID** paste karo (developers.facebook.com → App Dashboard → Settings → Basic se copy karo)
5. App add ho jayegi

### Page Ko Instagram Se Connect Karo (Business Portfolio mein):
1. Left side mein **"Pages"** click karo
2. **"Agentive Solutions"** pe click karo
3. **"Connected assets"** tab pe jao
4. **"Connect assets"** click karo
5. **"Instagram account"** select karo
6. Apna Instagram account connect karo

**Result:** App Business Portfolio se connected, Page aur Instagram bhi linked.

---

## Phase 6: Page Access Token Generate Karna

### CRITICAL: Do Tarah Ki Page IDs

Humein pata chala ke New Pages Experience mein **do different IDs** hoti hain:

| ID Type | Example | Kahan Milti Hai |
|---|---|---|
| New Pages Experience ID | `61585031032595` | Facebook URL bar mein |
| Business Portfolio Page ID | `1044367502088758` | Business Settings → Pages mein |

**API ke liye Business Portfolio Page ID use karo!** (`1044367502088758`)

### Token Generate Karne Ka Correct Method:

1. Jao: **developers.facebook.com/tools/explorer/**
2. **Meta App:** FTE Social Manager select karo
3. **User or Page:** User Token rakho
4. **Permissions** add karo:
   - `pages_show_list`
   - `pages_read_engagement`
   - `pages_read_user_content`
   - `pages_manage_posts`
   - `pages_manage_engagement`
5. **"Generate Access Token"** click karo
6. Popup mein:
   - "Continue as [Name]" click karo
   - Sab permissions allow karo
   - **"Agentive Solutions"** Page select karo (checkbox ON)
   - Save/Done click karo

### Page Token Nikalna:
1. **GET** mode mein (POST nahi!) URL likho:
```
1044367502088758?fields=access_token
```
2. Submit karo
3. Response mein **access_token** aayega — ye **Page Access Token** hai
4. Ye token copy karo — isse posting ke liye use hoga

---

## Phase 7: Facebook Page Pe Post Karna (API Test)

### Working Method:

1. Graph API Explorer mein **GET** mode mein:
```
1044367502088758?fields=access_token
```
2. Submit karo — Page token milega

3. **Access Token field mein Page token paste karo** (purana User token replace karo)

4. **POST** mode select karo

5. URL mein likho:
```
1044367502088758/feed?message=Test post from API
```

6. Submit karo

### Expected Success Response:
```json
{
  "id": "1044367502088758_122094486825167701"
}
```

**Ye post ID hai — iska matlab POST SUCCESSFUL!**

### Verify:
- Facebook pe Agentive Solutions Page kholo
- "Test post from API" post dikhni chahiye

---

## Problems Faced & Solutions

### Problem 1: `me/accounts` Returns Empty Data
```json
{"data": []}
```
**Cause:** Page Business Portfolio ke through managed hai, normal User Token se accessible nahi.
**Solution:** Business Portfolio mein app add karo (Phase 5), aur direct Page ID use karo (`1044367502088758`).

### Problem 2: "Object does not exist" Error
```json
{"error": {"message": "Object with ID '61585031032595' does not exist..."}}
```
**Cause:** New Pages Experience ID use ki — ye API mein kaam nahi karti.
**Solution:** Business Portfolio Page ID use karo: `1044367502088758` (Business Settings → Pages mein milti hai).

### Problem 3: "(#200) requires pages_read_engagement and pages_manage_posts"
```json
{"error": {"message": "(#200) If posting to a page, requires both pages_read_engagement and pages_manage_posts..."}}
```
**Cause:** User Token se post kar rahe the, Page Token chahiye.
**Solution:** Pehle GET se Page token nikalo (`1044367502088758?fields=access_token`), phir wo token use karke POST karo.

### Problem 4: "(#283) Requires pages_manage_metadata"
```json
{"error": {"message": "(#283) Requires pages_manage_metadata permission..."}}
```
**Cause:** POST mode mein token fetch karne ki koshish ki.
**Solution:** Token fetch karte waqt hamesha **GET** mode use karo, **POST** nahi.

### Problem 5: App Ko Page Access Nahi Mil Raha
**Cause:** FTE Social Manager app Business Portfolio se connected nahi thi.
**Solution:**
1. `business.facebook.com/settings/` jao
2. Accounts → Apps → "+ Add" → App ID paste karo
3. App add hone ke baad Pages section mein Page ko app se connect karo

### Problem 6: Token Generate Karte Waqt Page Select Ka Option Nahi Aata
**Cause:** Purani permissions cached hain.
**Solution:**
1. Facebook Settings → Business Integrations → App Remove karo
2. Graph Explorer pe wapas jao
3. Dobara "Generate Access Token" karo
4. Is baar popup mein Page select karne ka option aayega

---

## Key IDs & Credentials (Save Karo)

| Item | Value |
|---|---|
| App Name | FTE Social Manager |
| App ID | 2091840678329336 |
| Business Portfolio ID | 1445731533861239 |
| Facebook Page Name | Agentive Solutions |
| Facebook Page ID (API) | 1044367502088758 |
| Facebook Page ID (URL) | 61585031032595 |
| Instagram Username | shahzain_ali5512 |
| App Mode | Development |

**IMPORTANT:** App Secret aur Access Tokens ko kabhi public mat karo. `.env` file mein store karo.

---

## API Endpoints Quick Reference

### Facebook Page Operations:

| Action | Method | Endpoint |
|---|---|---|
| Get Page Info | GET | `{page_id}?fields=id,name` |
| Get Page Token | GET | `{page_id}?fields=access_token` |
| Create Post | POST | `{page_id}/feed?message=YOUR_MESSAGE` |
| Get Posts | GET | `{page_id}/feed` |
| Comment on Post | POST | `{post_id}/comments?message=YOUR_COMMENT` |
| Reply to Comment | POST | `{comment_id}/comments?message=YOUR_REPLY` |
| Get Comments | GET | `{post_id}/comments` |

### Instagram Operations (coming next):

| Action | Method | Endpoint |
|---|---|---|
| Get IG Account | GET | `{page_id}?fields=instagram_business_account` |
| Create Media | POST | `{ig_id}/media?image_url=URL&caption=TEXT` |
| Publish Media | POST | `{ig_id}/media_publish?creation_id=ID` |
| Get Comments | GET | `{media_id}/comments` |
| Reply Comment | POST | `{comment_id}/replies?message=TEXT` |

---

## Phase 8: Instagram API Setup (WORKING)

### 8.1 — Instagram Tester Role Add Karna

Instagram API use karne ke liye pehle app mein Instagram Tester role add karna padta hai.

1. **developers.facebook.com** → **My Apps** → **FTE Social Manager**
2. Left side: **"App roles"** → **"Roles"**
3. **"Instagram Testers"** tab click karo
4. **"Add People"** click karo
5. **"Instagram Tester"** role select karo
6. Instagram username type karo: `shahzain_ali5512`
7. **"Add"** click karo

### 8.2 — Instagram Se Invite Accept Karo

1. **Instagram App** open karo phone pe
2. **Settings and privacy** → **"Apps and Websites"**
3. **"Tester Invites"** tab mein **"FTE Social Manager-IG"** dikhega
4. Click karo aur **"Accept"** karo

### 8.3 — Instagram Permissions Add Karo

Graph API Explorer mein ye permissions add karo:
- `instagram_basic`
- `instagram_content_publish`
- `instagram_manage_comments`
- `instagram_manage_insights`

**"Generate Access Token"** click karo aur sab allow karo.

**Note:** Ye permissions "Instagram" product add karne ke baad hi milti hain. Pehle App Dashboard mein "Add Product" → "Instagram" add karo.

### 8.4 — Instagram Business Account ID Nikalna

GET mode mein:
```
1044367502088758?fields=instagram_business_account
```

Response:
```json
{
  "instagram_business_account": {
    "id": "17841477106514810"
  },
  "id": "1044367502088758"
}
```

**Instagram Business Account ID:** `17841477106514810`

### 8.5 — Instagram Pe Post Karna (2-Step Process)

Instagram pe posting **2 steps** mein hoti hai (Facebook se different):

**Step 1: Media Container Banao**

POST mode mein:
- URL: `17841477106514810/media`
- Parameter 1: `image_url` = `https://cdn.pixabay.com/photo/2015/04/23/22/00/tree-736885_1280.jpg`
- Parameter 2: `caption` = `Hello from FTE Social Manager!`

**IMPORTANT:** Parameters ko URL mein mat likho. "Add parameter" button use karke separately add karo. Warna "Only photo or video can be accepted" error aayega.

Response:
```json
{
  "id": "17869164552570218"
}
```

**Step 2: Publish Karo**

POST mode mein:
- URL: `17841477106514810/media_publish`
- Parameter: `creation_id` = `17869164552570218` (Step 1 se mili ID)

Response:
```json
{
  "id": "18194284255350604"
}
```

**Post successful! Instagram pe photo aur caption dikh jayega.**

### Instagram Posting Problems & Solutions

#### Problem 1: "Only photo or video can be accepted"
```json
{"error": {"message": "Only photo or video can be accepted as media type."}}
```
**Cause:** Image URL parameters ko URL string mein directly likha.
**Solution:** Parameters ko "Add parameter" button se separately add karo. URL mein sirf `17841477106514810/media` likho.

#### Problem 2: `instagram_business_account` nahi aa raha
**Cause:** Instagram permissions token mein add nahi hain.
**Solution:**
1. App Dashboard mein "Add Product" → "Instagram" add karo
2. Instagram Tester role add karo aur accept karo
3. `instagram_basic` permission add karo Graph Explorer mein
4. Naya token generate karo

#### Problem 3: Instagram permissions Graph Explorer mein nahi milti
**Cause:** Instagram product app mein add nahi hua.
**Solution:** developers.facebook.com → App Dashboard → "Add Product" → "Instagram" → "Set Up"

---

## Key IDs & Credentials (Updated)

| Item | Value |
|---|---|
| App Name | FTE Social Manager |
| App ID | 2091840678329336 |
| Instagram App ID | 1308042924482400 |
| Business Portfolio ID | 1445731533861239 |
| Facebook Page Name | Agentive Solutions |
| Facebook Page ID (API) | 1044367502088758 |
| Facebook Page ID (URL) | 61585031032595 |
| Instagram Username | shahzain_ali5512 |
| Instagram Business Account ID | 17841477106514810 |
| App Mode | Development |

**IMPORTANT:** App Secret aur Access Tokens ko kabhi public mat karo. `.env` file mein store karo.

---

## Complete API Endpoints Reference

### Facebook Page Operations:

| Action | Method | Endpoint |
|---|---|---|
| Get Page Info | GET | `{page_id}?fields=id,name` |
| Get Page Token | GET | `{page_id}?fields=access_token` |
| Create Post | POST | `{page_id}/feed` + param: `message` |
| Get Posts | GET | `{page_id}/feed` |
| Comment on Post | POST | `{post_id}/comments` + param: `message` |
| Reply to Comment | POST | `{comment_id}/comments` + param: `message` |
| Get Comments | GET | `{post_id}/comments` |

### Instagram Operations:

| Action | Method | Endpoint |
|---|---|---|
| Get IG Account | GET | `{page_id}?fields=instagram_business_account` |
| Get IG Profile | GET | `{ig_id}?fields=id,username,name,profile_picture_url` |
| Create Media Container | POST | `{ig_id}/media` + params: `image_url`, `caption` |
| Publish Media | POST | `{ig_id}/media_publish` + param: `creation_id` |
| Get Comments | GET | `{media_id}/comments` |
| Reply to Comment | POST | `{comment_id}/replies` + param: `message` |

---

## Token Guide — Kab Kaunsa Token Use Karna Hai

### Simple Rule:

| Platform | Token Type | Kyun? |
|---|---|---|
| **Facebook Page** (post, comment, reply, read) | **Page Token** | Page ek alag entity hai, uska apna token hota hai |
| **Instagram** (post, comment, reply, read) | **User Token** | Instagram tumhare personal account se linked hai |

### Token Kaise Check Karein?

**GET** mode mein ye submit karo:

```
me?fields=id,name
```

| Response | Matlab |
|---|---|
| `"name": "Shahzain Bangash"` | **User Token** active hai — Instagram ke liye use karo |
| Error: "Object with ID 'me' does not exist" | **Page Token** active hai — Facebook ke liye use karo |

### Page Token Kaise Set Karein (Facebook ke liye):

1. Pehle **User Token** active karo ("User or Page" → "Get User Access Token" → "Generate Access Token")
2. **GET** mode mein: `1044367502088758?fields=access_token`
3. Response mein jo `access_token` aaye wo **copy** karo
4. Right side mein **Access Token** field mein **paste** karo (purana replace)
5. Ab sab Facebook API calls Page Token se hongi

### User Token Kaise Set Karein (Instagram ke liye):

1. "User or Page" dropdown → **"Get User Access Token"** select karo
2. **"Generate Access Token"** click karo
3. Permissions allow karo
4. Ab sab Instagram API calls User Token se hongi

### Workflow Summary:

```
Facebook pe kaam karna hai?
  → Page Token set karo
  → Sab Facebook calls karo (post, comment, reply)

Instagram pe kaam karna hai?
  → User Token set karo
  → Sab Instagram calls karo (post, comment, reply)
```

**TIP:** Agar ek session mein dono platforms pe kaam karna hai toh pehle ek platform ke sab kaam karo, phir token switch karo aur doosre platform ke kaam karo. Baar baar switch mat karo.

---

## Phase 9: Complete Verification — Sab Kuch Test Karna

### Facebook Verification (Page Token se):

**Step 1: Page Token set karo** (upar "Page Token Kaise Set Karein" dekho)

**Step 2: Post banao**
- **POST** mode
- URL: `1044367502088758/feed`
- Parameter: `message` = `Verification test post`
- Expected: `{"id": "1044367502088758_XXXXXXXXX"}`
- **Facebook Page pe verify karo ke post dikh rahi hai**

**Step 3: Comment karo**
- **POST** mode
- URL: `{post_id}/comments` (Step 2 se mili post ID use karo)
- Parameter: `message` = `Verification test comment`
- Expected: `{"id": "XXXXXXXXX_XXXXXXXXX"}`
- **Facebook Page pe verify karo ke comment dikh raha hai**

**Step 4: Reply karo**
- **POST** mode
- URL: `{comment_id}/comments` (Step 3 se mili comment ID use karo)
- Parameter: `message` = `Verification test reply`
- Expected: `{"id": "XXXXXXXXX_XXXXXXXXX"}`
- **Facebook Page pe verify karo ke reply dikh raha hai**

### Instagram Verification (User Token se):

**Step 1: User Token set karo** ("User or Page" → "Get User Access Token" → "Generate Access Token")

**Step 2: Post banao (2-step process)**
- **POST** mode
- URL: `17841477106514810/media`
- Parameters: `image_url` = `any_public_image_url`, `caption` = `Verification test`
- Expected: `{"id": "XXXXXXXXX"}` (creation_id)

- **POST** mode
- URL: `17841477106514810/media_publish`
- Parameter: `creation_id` = (upar se mili ID)
- Expected: `{"id": "XXXXXXXXX"}` (media_id)
- **Instagram pe verify karo ke post dikh rahi hai**

**Step 3: Comment karo**
- **POST** mode
- URL: `{media_id}/comments` (Step 2 se mili media ID use karo)
- Parameter: `message` = `Verification test comment`
- Expected: `{"id": "XXXXXXXXX"}`
- **Instagram pe verify karo ke comment dikh raha hai**

**Step 4: Reply karo**
- **POST** mode
- URL: `{comment_id}/replies` (Step 3 se mili comment ID use karo)
- Parameter: `message` = `Verification test reply`
- Expected: `{"id": "XXXXXXXXX"}`
- **Instagram pe verify karo ke reply dikh raha hai**

### Verification Checklist:

```
FACEBOOK (Page Token):
✅ Post    — ID milta hai + Page pe dikhta hai
✅ Comment — ID milta hai + Post ke neeche dikhta hai
✅ Reply   — ID milta hai + Comment ke neeche dikhta hai

INSTAGRAM (User Token):
✅ Post    — 2-step (media + publish) — Profile pe dikhta hai
✅ Comment — ID milta hai + Post ke neeche dikhta hai
✅ Reply   — ID milta hai + Comment ke neeche dikhta hai
```

**Agar koi bhi step fail ho toh Problems & Solutions section dekho.**

---

## Phase 10: Long-Lived Tokens Banana (Production Ke Liye ZAROORI)

### Kyun Zaroori Hai?

Graph API Explorer se jo token milta hai wo **1-2 ghante** mein expire ho jata hai. Production/automation ke liye **long-lived tokens** chahiye.

| Token Type | Expiry | Kiske Liye |
|---|---|---|
| Short-lived User Token | 1-2 hours | Graph Explorer testing |
| **Long-lived User Token** | **60 days** | **Instagram automation (IG_ACCESS_TOKEN)** |
| **Long-lived Page Token** | **Never expires** | **Facebook automation (FB_PAGE_ACCESS_TOKEN)** |

### Step 1: App Secret Nikalo

1. **developers.facebook.com** → **My Apps** → **FTE Social Manager**
2. Left side: **"App settings"** → **"Basic"**
3. **"App Secret"** ke saamne **"Show"** click karo
4. Password daalo agar puche
5. **App Secret copy** karo — ye safe rakho, kisi ko mat batao

### Step 2: Long-Lived User Token Banao (IG_ACCESS_TOKEN — 60 days)

1. Graph API Explorer mein **"User or Page"** → **"Get User Access Token"** select karo
2. Ye permissions add karo:
   - `pages_show_list`
   - `pages_read_engagement`
   - `pages_manage_posts`
   - `pages_manage_engagement`
   - `instagram_basic`
   - `instagram_content_publish`
   - `instagram_manage_comments`
   - `instagram_manage_insights`
3. **"Generate Access Token"** click karo — sab allow karo + Page select karo
4. Ye **short-lived User Token** hai — isse copy karo

5. **Naye browser tab** mein ye URL paste karo:

```
https://graph.facebook.com/v25.0/oauth/access_token?grant_type=fb_exchange_token&client_id=2091840678329336&client_secret=YAHAN_APP_SECRET_PASTE_KARO&fb_exchange_token=YAHAN_SHORT_LIVED_USER_TOKEN_PASTE_KARO
```

6. **Replace karo:**
   - `YAHAN_APP_SECRET_PASTE_KARO` → App Secret (Step 1 se)
   - `YAHAN_SHORT_LIVED_USER_TOKEN_PASTE_KARO` → Graph Explorer ka short-lived token (Step 4 se)

7. **Enter** press karo
8. Response aayega:
```json
{
  "access_token": "EAAxxxxxxx_BOHOT_LAMBA_TOKEN_xxxxxxx",
  "token_type": "bearer",
  "expires_in": 5184000
}
```

9. `expires_in: 5184000` = **60 din** — ye confirm karta hai ke long-lived token ban gaya
10. **Ye token copy karo** — ye tumhara **IG_ACCESS_TOKEN** hai
11. `.env` file mein `IG_ACCESS_TOKEN=` ke baad paste karo

### Step 3: Never-Expiring Page Token Banao (FB_PAGE_ACCESS_TOKEN)

1. Step 2 ka **long-lived User Token** Graph API Explorer ke **Access Token** field mein paste karo
2. **GET** mode mein ye likho:

```
1044367502088758?fields=access_token
```

3. **Submit** karo
4. Response mein jo `access_token` aaye — ye **never-expiring Page Token** hai

```json
{
  "access_token": "EAAxxxxxxx_PAGE_TOKEN_xxxxxxx",
  "id": "1044367502088758"
}
```

5. **Ye token copy karo** — ye tumhara **FB_PAGE_ACCESS_TOKEN** hai
6. `.env` file mein `FB_PAGE_ACCESS_TOKEN=` ke baad paste karo

### Kyun Never-Expiring?

| User Token Type | Se Nikala Page Token |
|---|---|
| Short-lived User Token (1-2 hours) | Short-lived Page Token (1-2 hours) |
| **Long-lived User Token (60 days)** | **Never-expiring Page Token** |

Jab long-lived User Token se Page Token nikaalte ho toh wo **kabhi expire nahi hota** — ye Meta ki official documentation mein confirmed hai.

### Token Verify Karna

Apna token verify karne ke liye browser mein ye URL open karo:

```
https://graph.facebook.com/v25.0/debug_token?input_token=YAHAN_TOKEN_PASTE_KARO&access_token=YAHAN_TOKEN_PASTE_KARO
```

Response mein `expires_at: 0` aaye toh **never-expiring** hai.

### Token Renewal Reminder

| Token | Expiry | Kab Renew Karein |
|---|---|---|
| **FB_PAGE_ACCESS_TOKEN** | Never | Kabhi nahi (jab tak app delete na ho) |
| **IG_ACCESS_TOKEN** | 60 days | Har 50 din mein (10 din pehle) — Step 2 dobara follow karo |

### .env File Mein Kaise Save Karein

```env
# Facebook — Never-expiring Page Token
FB_PAGE_ACCESS_TOKEN=EAAxxxxxxx_PAGE_TOKEN_xxxxxxx

# Instagram — 60-day User Token (renew every 50 days)
IG_ACCESS_TOKEN=EAAxxxxxxx_USER_TOKEN_xxxxxxx
```

**IMPORTANT:** Ye tokens kabhi git mein push mat karo. `.env` file `.gitignore` mein honi chahiye (humari hai).

---

## Next Steps

1. **Python Integration** — Code mein API calls integrate karna
2. **MCP Server** — Claude ke liye Meta MCP server banana
3. **Twitter API Setup** — Next platform
4. **LinkedIn API Setup** — Next platform

---

## Video Script Notes

Jab video banao toh ye points cover karo:
1. Pehle 3 phases (Page, Instagram, Connection) — 5 min
2. Developer App creation — 3 min
3. **Business Portfolio connection** — ye sabse important hai, 5 min
4. **Two Page IDs ka concept** — ye unique insight hai, 3 min
5. Token generation aur testing — 5 min
6. Common errors aur solutions — 5 min

**Total estimated video: 25-30 min**
