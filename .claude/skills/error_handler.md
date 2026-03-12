# Skill: Error Handler

## Purpose
Handle errors with intelligent retry, graceful degradation, and owner notifications for critical failures.

## Platform
general

## Inputs
- Error context: component, error type, error message, action being attempted

## Steps

1. **Classify the error**:
   - **Transient**: ConnectionError, TimeoutError, rate limit → retry with backoff
   - **Permanent**: AuthenticationError, PermissionDenied, NotFound → do not retry
   - **Critical**: Component completely down, repeated failures → notify owner

2. **Apply retry logic for transient errors**:
   - Use `retry_with_backoff` from `src/utils/retry.py`
   - Exponential delays: 1s, 2s, 4s (max 3 attempts)
   - **NEVER auto-retry payment/financial operations** (FR-026)

3. **Update component health registry**:
   - Call `ComponentHealthRegistry.update_health(domain, success=False, error=msg)`
   - Track consecutive failures
   - Status transitions: healthy → degraded (1-2 failures) → down (3+)

4. **Create notification for critical failures**:
   - When component transitions to `down` status
   - Create `NOTIFICATION_component_down_{timestamp}.md` in `Needs_Action/`
   - Include: component name, error details, suggested action

5. **Graceful degradation**:
   - When Odoo is down: Email/WhatsApp continue working
   - When Facebook is down: Other domains continue
   - When Instagram is down: Other domains continue
   - Always log what's degraded in the Dashboard

## Escalation Rules
- 1-2 failures: Log warning, mark degraded, continue
- 3+ failures: Mark down, create notification, skip domain
- Payment errors: Always notify, never retry
- Token expiration: Create notification immediately

## Output Format
- Health state updated in `.state/health.json`
- Notification files in `Needs_Action/` for critical issues
- All errors logged in `Logs/YYYY-MM-DD.json`
