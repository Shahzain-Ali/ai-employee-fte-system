#!/bin/bash
# Run the FTE AI Employee Dashboard

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "🚀 Starting FTE AI Employee Dashboard..."
echo "📍 Project: $PROJECT_ROOT"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found"
    echo "   Dashboard will run with limited functionality"
    echo ""
fi

# Check if Odoo is running
if docker ps | grep -q odoo; then
    echo "✅ Odoo containers are running"
else
    echo "⚠️  Odoo containers are not running"
    echo "   Start with: cd docker/odoo && docker-compose up -d"
fi

echo ""
echo "🌐 Dashboard will open at: http://localhost:8501"
echo "🛑 Press Ctrl+C to stop"
echo ""

# Run Streamlit
uv run streamlit run src/dashboard/app.py \
    --server.port 8501 \
    --server.address localhost \
    --browser.gatherUsageStats false \
    --theme.base light \
    --theme.primaryColor "#2d5a87"
