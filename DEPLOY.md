# 🚀 Deploy WhatsApp Bot to Render

## Step-by-Step Deployment Guide

### 1. Prepare Your Repository

First, make sure all files are ready:
- ✅ `whatsapp_bot.py` - Main bot code
- ✅ `requirements.txt` - Python dependencies
- ✅ `render.yaml` - Render configuration
- ✅ `.env` - Environment variables (for local development)
- ✅ `README.md` - Documentation

### 2. Create GitHub Repository

1. Go to [GitHub](https://github.com) and create a new repository
2. Upload all your files to the repository
3. Make sure the repository is public (or upgrade to Render paid plan for private repos)

### 3. Deploy to Render

#### Option A: One-Click Deploy
1. Click the "Deploy to Render" button in README.md
2. Connect your GitHub account
3. Select your repository
4. Render will automatically detect the `render.yaml` configuration

#### Option B: Manual Deploy
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Name**: `whatsapp-bot`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python whatsapp_bot.py`

### 4. Set Environment Variables

In Render dashboard, add these environment variables:
```
VERIFY_TOKEN=whatsapp_verify_token_2024
WHATSAPP_TOKEN=EAAQEKbLnBZAMBPetZCCPqKZALn7S5D1LswpqvOQhDajKepWyaMzZAdzHDwLYsDVK5ZCbR0nhxU2nYM7UvdMvVcWBahJA4iIuZBVPIP2vqGN8apucWAj9Dnp21vuKDS4PP78qFB87Xf330gmjECckjo7Owq4ank8ZA5ZB659by2Vz7ZAOZAub7B05yi6OrfGwvikQZDZD
WHATSAPP_BUSINESS_ACCOUNT_ID=2139592896448288
APP_ID=1130477048497555
PHONE_NUMBER_ID=837445062775054
```

### 5. Deploy and Get URL

1. Click "Create Web Service"
2. Wait for deployment (5-10 minutes)
3. Your bot will be available at: `https://your-app-name.onrender.com`

### 6. Update WhatsApp Webhook

1. Go to [Meta Developer Console](https://developers.facebook.com)
2. Navigate to your WhatsApp app
3. Go to WhatsApp → Configuration
4. Update webhook URL to: `https://your-app-name.onrender.com/webhook`
5. Set verify token to: `whatsapp_verify_token_2024`
6. Subscribe to "messages" field

### 7. Test Your Bot

1. Visit `https://your-app-name.onrender.com` to see the status page
2. Use the web chat interface at `/enhanced-chat`
3. Send a message to your WhatsApp Business number
4. Check Render logs to see incoming webhooks

## 🎯 Benefits of Render Deployment

- ✅ **Free Tier**: Perfect for testing and small projects
- ✅ **Automatic HTTPS**: Secure webhook endpoints
- ✅ **Auto-Deploy**: Updates automatically from GitHub
- ✅ **Logs**: Easy debugging with built-in logs
- ✅ **Custom Domains**: Use your own domain (paid plans)
- ✅ **Environment Variables**: Secure credential management

## 🔧 Troubleshooting

### Common Issues:

1. **Build Fails**: Check `requirements.txt` for correct package versions
2. **App Won't Start**: Verify `PORT` environment variable usage
3. **Webhook Not Working**: Ensure URL is correct and HTTPS
4. **Environment Variables**: Double-check all tokens and IDs

### Useful Commands:

```bash
# Check logs
render logs --service your-service-id

# Restart service
render restart --service your-service-id
```

## 📱 After Deployment

Your WhatsApp bot will be live at:
- **Main App**: `https://your-app-name.onrender.com`
- **Chat Interface**: `https://your-app-name.onrender.com/enhanced-chat`
- **Webhook Endpoint**: `https://your-app-name.onrender.com/webhook`
- **API Status**: `https://your-app-name.onrender.com/api/status`

Remember to update your webhook URL in Meta Developer Console!
