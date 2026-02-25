import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const CREDENTIALS_PATH = path.resolve(__dirname, '../../.secrets/gmail_credentials.json');
const TOKEN_PATH = path.resolve(__dirname, '../../.secrets/gmail_token.json');

class EmailMCPServer {
  constructor() {
    this.server = new Server(
      { name: 'fte-email', version: '1.0.0' },
      { capabilities: { tools: {} } },
    );
    this.gmail = null;
    this.setupHandlers();
  }

  async initializeGmail() {
    try {
      // Lazy import — googleapis is huge, loading at startup causes timeout
      const { google } = await import('googleapis');
      const credentials = JSON.parse(await fs.readFile(CREDENTIALS_PATH, 'utf-8'));
      const { client_secret, client_id, redirect_uris } = credentials.installed || credentials.web;
      const oAuth2Client = new google.auth.OAuth2(client_id, client_secret, redirect_uris[0]);
      const token = JSON.parse(await fs.readFile(TOKEN_PATH, 'utf-8'));
      oAuth2Client.setCredentials(token);
      this.gmail = google.gmail({ version: 'v1', auth: oAuth2Client });
      return true;
    } catch (error) {
      console.error('Gmail init error:', error.message);
      return false;
    }
  }

  createEmailMessage(to, subject, body) {
    const message = [`To: ${to}`, `Subject: ${subject}`, 'MIME-Version: 1.0', 'Content-Type: text/plain; charset=utf-8', '', body].join('\n');
    return Buffer.from(message).toString('base64').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
  }

  setupHandlers() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: 'send_email_tool',
          description: 'Send an email via Gmail API',
          inputSchema: {
            type: 'object',
            properties: {
              to: { type: 'string', description: 'Recipient email address (e.g. client@example.com)' },
              subject: { type: 'string', description: 'Email subject line' },
              body: { type: 'string', description: 'Plain text email body content' },
            },
            required: ['to', 'subject', 'body'],
          },
        },
        {
          name: 'draft_email_tool',
          description: 'Preview an email without sending it. Returns the formatted email for review.',
          inputSchema: {
            type: 'object',
            properties: {
              to: { type: 'string', description: 'Recipient email address' },
              subject: { type: 'string', description: 'Email subject line' },
              body: { type: 'string', description: 'Plain text email body content' },
            },
            required: ['to', 'subject', 'body'],
          },
        },
      ],
    }));

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      if (!this.gmail) {
        const ok = await this.initializeGmail();
        if (!ok) throw new Error('Failed to initialize Gmail API');
      }

      const { name, arguments: args } = request.params;

      if (name === 'send_email_tool') {
        return await this.handleSendEmail(args);
      } else if (name === 'draft_email_tool') {
        return await this.handleDraftEmail(args);
      }
      throw new Error(`Unknown tool: ${name}`);
    });
  }

  async handleSendEmail({ to, subject, body }) {
    try {
      const raw = this.createEmailMessage(to, subject, body);
      const res = await this.gmail.users.messages.send({
        userId: 'me',
        requestBody: { raw },
      });
      return {
        content: [{ type: 'text', text: `Email sent successfully to ${to} (Gmail ID: ${res.data.id})` }],
      };
    } catch (error) {
      return {
        content: [{ type: 'text', text: `Error sending email: ${error.message}` }],
        isError: true,
      };
    }
  }

  async handleDraftEmail({ to, subject, body }) {
    try {
      const raw = this.createEmailMessage(to, subject, body);
      const res = await this.gmail.users.drafts.create({
        userId: 'me',
        requestBody: { message: { raw } },
      });

      const preview = `--- EMAIL DRAFT (saved to Gmail) ---\nTo: ${to}\nSubject: ${subject}\n---\n${body}\n---\nDraft ID: ${res.data.id}\n\nDraft saved in your Gmail Drafts folder. Use send_email_tool to send it.`;

      return {
        content: [{ type: 'text', text: preview }],
      };
    } catch (error) {
      return {
        content: [{ type: 'text', text: `Error creating draft: ${error.message}` }],
        isError: true,
      };
    }
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Email MCP Server running on stdio');
  }
}

const server = new EmailMCPServer();
server.run().catch(err => { console.error('FATAL:', err); process.exit(1); });
