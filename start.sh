#!/bin/bash
# Production startup script for Render

echo "🚀 Starting WhatsApp Bot on Render..."
echo "Port: $PORT"
echo "Environment: Production"

# Start the Flask app with Gunicorn for production
if [ "$PORT" ]; then
    echo "Using Gunicorn for production..."
    gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 whatsapp_bot:app
else
    echo "Using Flask development server..."
    python whatsapp_bot.py
fi
