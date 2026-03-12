# Lessons Learned: Gold Tier Development

## Technology Decisions

### Python for All MCP Servers
- **Decision**: Use Python mcp SDK for all new servers (Odoo, Facebook, Instagram)
- **Why**: Single language ecosystem, direct library imports, consistent patterns
- **Outcome**: Shared `_meta_client.py` between Facebook and Instagram servers reduced duplication

### Shared Meta Graph API Client
- **Decision**: Extract `_meta_client.py` as shared HTTP client
- **Benefit**: Rate limit detection, token expiration handling, retry logic — written once, used by two servers

### JSON-RPC for Odoo (not REST)
- **Decision**: Direct JSON-RPC via `requests` instead of OdooRPC library
- **Why**: No extra dependency, stateless calls, full control over error handling
- **Consideration**: Odoo 19 may have REST API improvements — worth revisiting for Platinum

### Instagram Creator Accounts
- **Discovery**: Instagram Platform API (July 2024) supports Creator accounts, not just Business
- **Impact**: Broadened options for users who prefer Creator over Business account type

## Integration Challenges

### Facebook Personal Profile
- **Challenge**: No official API for personal profile posting (removed since 2018)
- **Solution**: Pages API for business, Playwright (optional) for personal
- **Lesson**: Always verify API capabilities before planning features

### Cross-Domain Workflow Complexity
- **Challenge**: Linking actions across multiple domains with traceability
- **Solution**: WorkflowEngine with UUID workflow_id linking all audit log entries
- **Lesson**: File-based action creation works well for async, approval-gated workflows

## Security Considerations

- All credentials in `.env` (never in vault or committed files)
- Custom MCP servers only — no third-party community servers
- Audit logs scrub sensitive data (tokens, passwords)
- HITL approval required for all external-facing actions

## Recommendations for Platinum Tier

1. **Cloud Deployment**: Move Odoo to cloud VM with HTTPS
2. **Agent-to-Agent**: Implement A2A protocol for multi-agent coordination
3. **Vault Sync**: Cloud-local vault synchronization
4. **Real-time**: Replace polling with WebSocket/SSE for faster response
5. **Testing**: Add comprehensive integration test suite with mock MCP servers
