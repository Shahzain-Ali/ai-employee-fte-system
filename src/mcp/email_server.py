"""MCP Email Server — gives Claude Code a send_email tool via Model Context Protocol."""
import asyncio
import logging
import sys
from pathlib import Path

# Ensure project root is on sys.path so `src.*` imports work regardless of cwd
_project_root = str(Path(__file__).resolve().parent.parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.stdio

from src.utils.email_sender import send_email

logger = logging.getLogger(__name__)

# Create MCP server instance
server = Server("fte-email")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available email tools."""
    return [
        Tool(
            name="send_email_tool",
            description="Send an email via Gmail API",
            inputSchema={
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string",
                        "description": "Recipient email address (e.g. client@example.com)",
                    },
                    "subject": {
                        "type": "string",
                        "description": "Email subject line",
                    },
                    "body": {
                        "type": "string",
                        "description": "Plain text email body content",
                    },
                },
                "required": ["to", "subject", "body"],
            },
        ),
        Tool(
            name="draft_email_tool",
            description="Preview an email without sending it. Returns the formatted email for review.",
            inputSchema={
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string",
                        "description": "Recipient email address",
                    },
                    "subject": {
                        "type": "string",
                        "description": "Email subject line",
                    },
                    "body": {
                        "type": "string",
                        "description": "Plain text email body content",
                    },
                },
                "required": ["to", "subject", "body"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    if name == "send_email_tool":
        try:
            to = arguments["to"]
            subject = arguments["subject"]
            body = arguments["body"]
            result = send_email(to=to, subject=subject, body=body)
            msg_id = result.get("id", "unknown")
            return [
                TextContent(
                    type="text",
                    text=f"Email sent successfully to {to} (Gmail ID: {msg_id})",
                )
            ]
        except Exception as e:
            logger.error("MCP send_email failed: %s", e)
            return [TextContent(type="text", text=f"Error sending email: {e}")]

    elif name == "draft_email_tool":
        to = arguments["to"]
        subject = arguments["subject"]
        body = arguments["body"]
        draft = (
            f"--- EMAIL DRAFT (not sent) ---\n"
            f"To: {to}\n"
            f"Subject: {subject}\n"
            f"---\n"
            f"{body}\n"
            f"---\n"
            f"Use send_email_tool to actually send this email."
        )
        return [TextContent(type="text", text=draft)]

    else:
        raise ValueError(f"Unknown tool: {name}")


async def main():
    """Run the MCP server using stdio transport."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
