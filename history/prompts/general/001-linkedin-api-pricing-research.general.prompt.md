---
id: "001"
title: LinkedIn API Pricing and Access Research 2026
stage: general
date: 2026-03-03
surface: agent
model: claude-sonnet-4-6
feature: none
branch: 002-silver-fte-foundation
user: architext
command: research LinkedIn API pricing and access
labels: ["linkedin", "api", "research", "pricing", "social-media", "automation"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - none
tests:
  - none
---

## Prompt

Research LinkedIn API pricing and access for posting, commenting, and automation in 2026. I need FACTUAL, VERIFIED information:

1. Can you post on LinkedIn via official API for FREE?
2. What are the LinkedIn API tiers and their costs?
3. What permissions/products are needed for posting (Share on LinkedIn, Community Management API, Marketing Developer Platform)?
4. Is there a free tier that allows posting?
5. What's the approval process - can anyone get access or do you need LinkedIn partner approval?
6. Any recent 2025-2026 changes to LinkedIn API access?
7. Compare: LinkedIn API free access vs Twitter API (which requires $5+ credits)

Search multiple sources and cross-verify. Give me the honest truth - is LinkedIn API posting realistically free for individual developers or small businesses?

## Response snapshot

Cross-verified from LinkedIn official Microsoft Learn docs (updated Feb 2026), LinkedIn developer portal, and multiple third-party developer sources.

KEY FINDING: LinkedIn has ONE genuinely free path for posting — the "Share on LinkedIn" product granting the `w_member_social` permission — which allows posting, commenting, and liking on behalf of individual member accounts with no cost and self-serve approval. This is verified in official LinkedIn docs last updated 2026-02-18.

Compared to Twitter/X: LinkedIn's free tier is more developer-friendly for posting. Twitter's free tier is write-only (1,500 posts/month, no reads). LinkedIn's free tier also has no published monthly post limit (only rate limits of ~100 req/day per token) but works for member posts without partner approval.

Community Management API (for company page posting) requires registered legal entity status and a full approval process but still has NO stated cost — it is free if approved.

## Outcome

- Impact: Clarified LinkedIn API access model for the FTE project's LinkedIn automation strategy
- Tests: none
- Files: none
- Next prompts: Decide whether to use w_member_social (free, member posts) or pursue Community Management API (company page posts, free but approval required)
- Reflection: The "LinkedIn API is expensive/partner-only" narrative in many blog posts is outdated or refers to advanced tiers (Advertising API, Sales Navigator). The basic posting path is genuinely free.

## Evaluation notes (flywheel)

- Failure modes observed: Many third-party blog posts conflate ALL LinkedIn APIs as requiring partner approval — this is false for the Share on LinkedIn product
- Graders run and results (PASS/FAIL): Cross-checked against official Microsoft Learn docs (li-lms-2026-02 version), developer.linkedin.com product catalog, and first-hand developer blog (Marcus Noble, Feb 2025)
- Prompt variant (if applicable): none
- Next experiment: Test the actual w_member_social token flow against the /rest/posts endpoint to confirm it works without Community Management API approval
