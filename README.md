# WhatsApp Business API Bot

A complete WhatsApp Business API bot with web chat interface, built with Python Flask.

## Features

- 📱 Send and receive WhatsApp messages
- 🌐 Web chat interface with contact management
- 🔒 Secure webhook verification
- 📊 Message delivery tracking
- 🤖 Automated responses
- 📋 Message history storage

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
   ```

3. Run the bot:
   ```bash
   python whatsapp_bot.py
   ```

## Environment Variables

- `VERIFY_TOKEN`: Webhook verification token
- `WHATSAPP_TOKEN`: WhatsApp Business API access token
- `WHATSAPP_BUSINESS_ACCOUNT_ID`: Your WhatsApp Business Account ID
- `APP_ID`: Your Meta App ID
- `PHONE_NUMBER_ID`: Your WhatsApp Phone Number ID
- `PORT`: Server port (automatically set by Render)

## Webhook Configuration

After deployment, configure your webhook URL in Meta Developer Console:
- Webhook URL: `https://your-app-name.onrender.com/webhook`
- Verify Token: Use the same value as `VERIFY_TOKEN`

## Usage

1. **Web Interface**: Visit your deployed URL for the chat interface
2. **API Endpoints**:
   - `POST /send` - Send messages
   - `POST /webhook` - Receive messages
   - `GET /webhook` - Webhook verification

## Support

For issues and questions, check the troubleshooting guide at `/troubleshoot`
