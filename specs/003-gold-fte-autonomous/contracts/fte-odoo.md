# MCP Server Contract: fte-odoo

**Server Name**: `fte-odoo`
**Transport**: stdio
**Language**: Python (mcp SDK)
**Source**: `src/mcp/odoo_server.py`
**Backend**: Odoo Community Edition via JSON-RPC (`http://localhost:8069/jsonrpc`)

---

## Tools

### 1. create_invoice

**Description**: Create a new customer invoice in Odoo.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "partner_name": {
      "type": "string",
      "description": "Client/partner name (will be matched or created in Odoo)"
    },
    "lines": {
      "type": "array",
      "description": "Invoice line items",
      "items": {
        "type": "object",
        "properties": {
          "description": { "type": "string" },
          "quantity": { "type": "number", "default": 1 },
          "price_unit": { "type": "number" }
        },
        "required": ["description", "price_unit"]
      }
    },
    "due_date": {
      "type": "string",
      "description": "Due date in YYYY-MM-DD format (optional)"
    }
  },
  "required": ["partner_name", "lines"]
}
```

**Success Response**: `"Invoice created: ID={id}, Partner={name}, Total={amount}, Status=Draft"`

**Error Response**: `"Error creating invoice: {error_message}"`

---

### 2. get_invoices

**Description**: List invoices from Odoo with optional filters.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "status": {
      "type": "string",
      "enum": ["draft", "posted", "paid", "all"],
      "default": "all",
      "description": "Filter by invoice status"
    },
    "limit": {
      "type": "integer",
      "default": 20,
      "description": "Maximum number of invoices to return"
    }
  }
}
```

**Success Response**: JSON-formatted list of invoices with id, partner, amount, status, date.

---

### 3. mark_payment_received

**Description**: Record payment received for an invoice.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "invoice_id": {
      "type": "integer",
      "description": "Odoo invoice ID"
    },
    "amount": {
      "type": "number",
      "description": "Payment amount (optional, defaults to full invoice amount)"
    },
    "payment_date": {
      "type": "string",
      "description": "Payment date in YYYY-MM-DD format (optional, defaults to today)"
    }
  },
  "required": ["invoice_id"]
}
```

**Success Response**: `"Payment recorded: Invoice {id} marked as Paid. Amount={amount}"`

**Error Response**: `"Error recording payment: {error_message}"`

---

### 4. get_weekly_summary

**Description**: Get financial summary for the current or specified week.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "week_start": {
      "type": "string",
      "description": "Week start date YYYY-MM-DD (optional, defaults to current week's Monday)"
    }
  }
}
```

**Success Response**: JSON with total_revenue, total_expenses, pending_invoices_count, outstanding_balance, recent_transactions.

---

### 5. get_expenses

**Description**: List expenses from Odoo.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "limit": {
      "type": "integer",
      "default": 20,
      "description": "Maximum number of expenses to return"
    }
  }
}
```

**Success Response**: JSON-formatted list of expenses with id, description, amount, date, status.

---

### 6. create_expense

**Description**: Record a new expense in Odoo.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "description": {
      "type": "string",
      "description": "Expense description"
    },
    "amount": {
      "type": "number",
      "description": "Expense amount"
    },
    "category": {
      "type": "string",
      "description": "Expense category (e.g., 'Office Supplies', 'Travel')"
    },
    "date": {
      "type": "string",
      "description": "Expense date YYYY-MM-DD (optional, defaults to today)"
    }
  },
  "required": ["description", "amount"]
}
```

**Success Response**: `"Expense created: ID={id}, Amount={amount}, Category={category}"`

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ODOO_URL` | Yes | Odoo server URL (default: `http://localhost:8069`) |
| `ODOO_DB` | Yes | Odoo database name |
| `ODOO_USER` | Yes | Odoo username |
| `ODOO_PASSWORD` | Yes | Odoo password |

## Error Handling

- Connection refused → Return error text, mark component as `down`
- Authentication failed → Return error text, create notification file
- JSON-RPC error → Return Odoo error message as text
- All errors logged to audit with `mcp_server: "fte-odoo"`
