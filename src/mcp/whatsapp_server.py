"""MCP WhatsApp Server — sends WhatsApp messages via file-based queue.

When WhatsApp watcher is running (holds browser session), messages are queued
as JSON files in .state/whatsapp_queue/. The watcher picks them up and sends
via its already-open browser. If watcher is NOT running, sends directly.
"""
import asyncio
import json
import logging
import os
import sys
import time
import uuid
from pathlib import Path

# Ensure project root is on sys.path so `src.*` imports work regardless of cwd
_project_root = str(Path(__file__).resolve().parent.parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from dotenv import load_dotenv
load_dotenv()

from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.stdio

logger = logging.getLogger(__name__)

QUEUE_DIR = Path(_project_root) / ".state" / "whatsapp_queue"

# Create MCP server instance
server = Server("fte-whatsapp")


def _queue_message(contact_name: str, message: str) -> dict:
    """Write a message request to the queue directory for the watcher to pick up."""
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)

    request_id = str(uuid.uuid4())[:8]
    ts = int(time.time())
    filename = f"send_{ts}_{request_id}.json"
    request_file = QUEUE_DIR / filename

    request = {
        "id": request_id,
        "contact_name": contact_name,
        "message": message,
        "created_at": time.time(),
        "status": "pending",
    }
    request_file.write_text(json.dumps(request, indent=2), encoding="utf-8")
    logger.info("Queued WhatsApp message for '%s' → %s", contact_name, filename)

    # Wait for watcher to process (poll for result file or status change)
    result_file = QUEUE_DIR / f"result_{request_id}.json"
    timeout = 120  # 2 minutes max
    start = time.time()

    while time.time() - start < timeout:
        # Check if result file was created by watcher
        if result_file.exists():
            result = json.loads(result_file.read_text(encoding="utf-8"))
            # Cleanup
            request_file.unlink(missing_ok=True)
            result_file.unlink(missing_ok=True)
            return result

        # Check if request was processed (status changed)
        if request_file.exists():
            current = json.loads(request_file.read_text(encoding="utf-8"))
            if current.get("status") in ("sent", "failed"):
                request_file.unlink(missing_ok=True)
                return current

        time.sleep(2)

    # Timeout — try direct send as fallback
    request_file.unlink(missing_ok=True)
    logger.warning("Queue timeout — trying direct send to '%s'", contact_name)
    return _direct_send(contact_name, message)


def _direct_send(contact_name: str, message: str) -> dict:
    """Send directly via Playwright (when watcher is NOT running)."""
    from src.utils.whatsapp_sender import send_whatsapp_reply
    return send_whatsapp_reply(sender_name=contact_name, message=message)


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available WhatsApp tools."""
    return [
        Tool(
            name="send_whatsapp_message",
            description="Send a WhatsApp message to a contact via WhatsApp Web (Playwright)",
            inputSchema={
                "type": "object",
                "properties": {
                    "contact_name": {
                        "type": "string",
                        "description": "The contact name to search for in WhatsApp (e.g. 'Accounts Team')",
                    },
                    "message": {
                        "type": "string",
                        "description": "The message text to send",
                    },
                },
                "required": ["contact_name", "message"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    if name == "send_whatsapp_message":
        try:
            contact_name = arguments["contact_name"]
            message = arguments["message"]

            # Use queue-based approach (non-blocking for async)
            result = await asyncio.to_thread(
                _queue_message,
                contact_name=contact_name,
                message=message,
            )

            status = result.get("status", "unknown")
            return [
                TextContent(
                    type="text",
                    text=f"WhatsApp message sent to '{contact_name}' (status: {status})",
                )
            ]
        except Exception as e:
            logger.error("MCP send_whatsapp failed: %s", e)
            return [TextContent(type="text", text=f"Error sending WhatsApp message: {e}")]

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
