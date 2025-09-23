# WhatsApp Business API Bot

A complete WhatsApp Business API bot with web chat interface, built with Python Flask.

## Features

- 📱 Send and receive WhatsApp messages
- 🌐 Web chat interface with contact management
- 🔒 Secure webhook verification
- 📊 Message delivery tracking
- 🤖 Automated responses
- 📋 Message history storage with Redis
- 🔌 Real-time WebSocket updates
- 📞 Multiple chat interfaces (simple and enhanced)

## Project Structure

```
whatsapp-bot/
├── whatsapp_bot.py              # Main comprehensive bot (recommended)
├── simple_sender.py             # Simple message sender app
├── templates/                   # Flask templates
│   ├── index.html              # Simple message form
│   ├── result.html             # Message result display
│   ├── chat.html               # Basic chat interface
│   └── enhanced_chat.html      # Advanced chat with contacts
├── static/                     # Web assets
│   ├── css/
│   │   └── style.css          # Stylesheet
│   └── js/
│       └── chat.js            # Chat functionality
├── tests/                      # Test files
│   └── whatsapp_api_test.py   # WhatsApp API functions
├── requirements.txt            # Python dependencies
├── render.yaml                # Render deployment config
├── start.sh                   # Startup script
├── README.md                  # This file
└── DEPLOY.md                  # Deployment guide
```

## Quick Deploy to Render

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

## Local Development

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables in `.env`:
   ```
   VERIFY_TOKEN=your_verify_token
   WHATSAPP_TOKEN=your_whatsapp_token
   PHONE_NUMBER_ID=your_phone_number_id
   WHATSAPP_BUSINESS_ACCOUNT_ID=your_business_account_id
   ```

3. Run the main bot (recommended):
   ```bash
   python whatsapp_bot.py
   ```

   Or run the simple sender:
   ```bash
   python simple_sender.py
   ```

## Available Applications

### 1. Main Bot (`whatsapp_bot.py`) - Recommended
- Full-featured WhatsApp bot with WebSocket support
- Redis message storage
- Enhanced chat interface with contact management
- Real-time message updates
- Comprehensive webhook handling
- Multiple chat interfaces

### 2. Simple Sender (`simple_sender.py`)
- Basic message sending functionality
- Simple web form interface
- Good for testing or minimal use cases

## Environment Variables

- `VERIFY_TOKEN`: Webhook verification token
- `WHATSAPP_TOKEN`: WhatsApp Business API access token
- `WHATSAPP_BUSINESS_ACCOUNT_ID`: Your WhatsApp Business Account ID
- `APP_ID`: Your Meta App ID
- `PHONE_NUMBER_ID`: Your WhatsApp Phone Number ID
- `REDIS_HOST`, `REDIS_PORT`, `REDIS_USERNAME`, `REDIS_PASSWORD`: Redis configuration (for main bot)
- `PORT`: Server port (automatically set by Render)

## Webhook Configuration

After deployment, configure your webhook URL in Meta Developer Console:
- Webhook URL: `https://your-app-name.onrender.com/webhook`
- Verify Token: Use the same value as `VERIFY_TOKEN`

## Usage

### Web Interfaces
1. **Main Status**: `/` - Bot status and information
2. **Simple Form**: `/` (simple_sender.py) - Basic message form
3. **Basic Chat**: `/chat` - Simple chat interface
4. **Enhanced Chat**: `/enhanced-chat` - Advanced interface with contacts

### API Endpoints
- `POST /send` - Send messages
- `POST /send-template` - Send template messages
- `POST /webhook` - Receive messages
- `GET /webhook` - Webhook verification
- `GET /api/status` - Bot status
- `GET /api/contacts` - Get contacts
- `GET /api/messages/<phone>` - Get message history

## Support

For issues and questions, check the troubleshooting guide at `/troubleshoot`
