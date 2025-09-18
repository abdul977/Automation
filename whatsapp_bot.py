#!/usr/bin/env python3
"""
Simple WhatsApp Business API Bot
A one-page Python script to receive and send WhatsApp messages using Flask and Meta's WhatsApp Business API.

Requirements:
- pip install flask requests python-dotenv

Setup Instructions:
1. Get your Phone Number ID from WhatsApp Business API dashboard
2. Update the configuration variables below
3. Set up webhook URL in Meta Developer Console
4. Run the script: python whatsapp_bot.py
"""

import os
import json
import hmac
import hashlib
import requests
from flask import Flask, request, jsonify, render_template, send_from_directory
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration - Update these with your actual values
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "EAAQEKbLnBZAMBPetZCCPqKZALn7S5D1LswpqvOQhDajKepWyaMzZAdzHDwLYsDVK5ZCbR0nhxU2nYM7UvdMvVcWBahJA4iIuZBVPIP2vqGN8apucWAj9Dnp21vuKDS4PP78qFB87Xf330gmjECckjo7Owq4ank8ZA5ZB659by2Vz7ZAOZAub7B05yi6OrfGwvikQZDZD")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "whatsapp_verify_token_2024")  # Set this in your webhook config
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID", "YOUR_PHONE_NUMBER_ID")  # Get from WhatsApp Business API dashboard
WHATSAPP_BUSINESS_ACCOUNT_ID = os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID", "2139592896448288")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://automation-9lq8.onrender.com/webhook")
APP_ID = os.getenv("APP_ID", "1130477048497555")
APP_SECRET = os.getenv("APP_SECRET", "your_app_secret")  # For webhook verification

# WhatsApp API Configuration
GRAPH_API_VERSION = "v18.0"
WHATSAPP_API_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{PHONE_NUMBER_ID}/messages"

# Initialize Flask app
app = Flask(__name__)

def get_phone_number_id():
    """
    Automatically get Phone Number ID from WhatsApp Business API
    """
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{WHATSAPP_BUSINESS_ACCOUNT_ID}/phone_numbers"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        if data.get("data") and len(data["data"]) > 0:
            phone_number_id = data["data"][0]["id"]
            print(f"Found Phone Number ID: {phone_number_id}")
            return phone_number_id
        else:
            print("No phone numbers found in your WhatsApp Business Account")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error getting phone number ID: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response: {e.response.text}")
        return None

def verify_webhook_signature(payload, signature):
    """
    Verify webhook signature for security
    """
    if not APP_SECRET:
        return True  # Skip verification if no app secret is set
    
    expected_signature = hmac.new(
        APP_SECRET.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(f"sha256={expected_signature}", signature)

def send_whatsapp_message(to_phone_number, message_text, message_type="text"):
    """
    Send a message via WhatsApp Business API

    Args:
        to_phone_number (str): Recipient's phone number (with country code, no + sign)
        message_text (str): Message content to send
        message_type (str): Type of message ("text" or "template")

    Returns:
        dict: API response with detailed status
    """
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    # Clean phone number (remove + if present)
    clean_phone = to_phone_number.replace("+", "").strip()

    if message_type == "template":
        # Send template message (for first contact)
        payload = {
            "messaging_product": "whatsapp",
            "to": clean_phone,
            "type": "template",
            "template": {
                "name": "hello_world",  # Default template
                "language": {
                    "code": "en_US"
                }
            }
        }
    else:
        # Send regular text message
        payload = {
            "messaging_product": "whatsapp",
            "to": clean_phone,
            "type": "text",
            "text": {
                "body": message_text
            }
        }

    try:
        print(f"Sending {message_type} message to {clean_phone}")
        print(f"Payload: {json.dumps(payload, indent=2)}")

        response = requests.post(WHATSAPP_API_URL, headers=headers, json=payload)
        response_data = response.json()

        print(f"API Response Status: {response.status_code}")
        print(f"API Response: {json.dumps(response_data, indent=2)}")

        if response.status_code == 200:
            print(f"✅ Message sent successfully to {clean_phone}")
            return {
                "success": True,
                "response": response_data,
                "message_id": response_data.get("messages", [{}])[0].get("id"),
                "phone_number": clean_phone
            }
        else:
            error_msg = response_data.get("error", {}).get("message", "Unknown error")
            print(f"❌ Failed to send message: {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "response": response_data,
                "phone_number": clean_phone
            }

    except requests.exceptions.RequestException as e:
        error_msg = f"Network error: {str(e)}"
        print(f"❌ {error_msg}")
        if hasattr(e, 'response') and e.response:
            try:
                error_response = e.response.json()
                print(f"Error Response: {json.dumps(error_response, indent=2)}")
                return {
                    "success": False,
                    "error": error_response.get("error", {}).get("message", error_msg),
                    "response": error_response,
                    "phone_number": clean_phone
                }
            except:
                print(f"Raw Error Response: {e.response.text}")

        return {
            "success": False,
            "error": error_msg,
            "phone_number": clean_phone
        }

def process_whatsapp_message(message_data):
    """
    Process incoming WhatsApp message and generate response
    
    Args:
        message_data (dict): Message data from webhook
    
    Returns:
        str: Response message
    """
    # Extract message text
    message_text = message_data.get("text", {}).get("body", "").lower()
    sender_name = message_data.get("profile", {}).get("name", "User")
    
    # Simple response logic - customize this as needed
    if "hello" in message_text or "hi" in message_text:
        return f"Hello {sender_name}! How can I help you today?"
    elif "help" in message_text:
        return "I'm a WhatsApp bot. You can ask me questions or just say hello!"
    elif "bye" in message_text or "goodbye" in message_text:
        return f"Goodbye {sender_name}! Have a great day!"
    else:
        return f"Thanks for your message: '{message_text}'. I'm still learning how to respond better!"

@app.route("/webhook", methods=["GET"])
def verify_webhook():
    """
    Webhook verification endpoint for WhatsApp
    """
    print("🔍 Webhook verification request received!")
    print(f"Request args: {request.args}")

    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    print(f"Mode: {mode}, Token: {token}, Challenge: {challenge}")
    print(f"Expected token: {VERIFY_TOKEN}")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("✅ Webhook verified successfully!")
        return challenge
    else:
        print("❌ Webhook verification failed!")
        print(f"Expected: mode='subscribe', token='{VERIFY_TOKEN}'")
        print(f"Received: mode='{mode}', token='{token}'")
        return "Verification failed", 403

@app.route("/webhook", methods=["POST"])
def handle_webhook():
    """
    Handle incoming WhatsApp messages
    """
    print("📨 Incoming webhook request received!")
    print(f"Headers: {dict(request.headers)}")
    print(f"Content-Type: {request.content_type}")

    # Verify webhook signature
    signature = request.headers.get("X-Hub-Signature-256", "")
    print(f"Signature: {signature}")

    if not verify_webhook_signature(request.data, signature):
        print("❌ Invalid webhook signature!")
        return "Invalid signature", 403

    try:
        data = request.get_json()
        print(f"📋 Received webhook data: {json.dumps(data, indent=2)}")

        # Process webhook data
        if data.get("object") == "whatsapp_business_account":
            print("✅ WhatsApp Business Account webhook detected")
            entries = data.get("entry", [])

            for entry in entries:
                print(f"Processing entry: {entry.get('id')}")
                changes = entry.get("changes", [])

                for change in changes:
                    print(f"Change field: {change.get('field')}")
                    if change.get("field") == "messages":
                        value = change.get("value", {})
                        messages = value.get("messages", [])

                        print(f"📱 Found {len(messages)} message(s)")

                        for message in messages:
                            # Extract sender information
                            sender_phone = message.get("from")
                            message_id = message.get("id")
                            message_type = message.get("type")

                            print(f"📨 Received {message_type} message from {sender_phone} (ID: {message_id})")

                            # Only process text messages
                            if message_type == "text":
                                message_text = message.get("text", {}).get("body", "")
                                print(f"💬 Message content: '{message_text}'")

                                # Generate response
                                response_text = process_whatsapp_message(message)
                                print(f"🤖 Generated response: '{response_text}'")

                                # Send response back
                                if sender_phone and response_text:
                                    print(f"📤 Sending response to {sender_phone}")
                                    result = send_whatsapp_message(sender_phone, response_text)
                                    if not result["success"]:
                                        print(f"❌ Failed to send response: {result['error']}")
                                    else:
                                        print(f"✅ Response sent successfully!")
                            else:
                                print(f"⚠️ Unsupported message type: {message_type}")
        else:
            print(f"⚠️ Unknown webhook object: {data.get('object')}")

        return jsonify({"status": "success"}), 200

    except Exception as e:
        print(f"❌ Error processing webhook: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/send", methods=["POST"])
def send_message_endpoint():
    """
    Manual endpoint to send messages
    Usage: POST /send with JSON body: {"to": "phone_number", "message": "text", "type": "text|template"}
    """
    try:
        data = request.get_json()
        to_phone = data.get("to")
        message = data.get("message", "")
        message_type = data.get("type", "text")

        if not to_phone:
            return jsonify({"error": "Missing 'to' parameter"}), 400

        if message_type == "text" and not message:
            return jsonify({"error": "Missing 'message' parameter for text messages"}), 400

        result = send_whatsapp_message(to_phone, message, message_type)

        if result["success"]:
            return jsonify({
                "status": "success",
                "result": result["response"],
                "message_id": result.get("message_id"),
                "phone_number": result["phone_number"],
                "delivery_info": "Message accepted by WhatsApp API. Delivery depends on recipient's opt-in status and 24-hour messaging window."
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": result["error"],
                "phone_number": result["phone_number"],
                "details": result.get("response", {})
            }), 400

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/send-template", methods=["POST"])
def send_template_message_endpoint():
    """
    Send template message (for first contact)
    Usage: POST /send-template with JSON body: {"to": "phone_number"}
    """
    try:
        data = request.get_json()
        to_phone = data.get("to")

        if not to_phone:
            return jsonify({"error": "Missing 'to' parameter"}), 400

        result = send_whatsapp_message(to_phone, "", "template")

        if result["success"]:
            return jsonify({
                "status": "success",
                "result": result["response"],
                "message_id": result.get("message_id"),
                "phone_number": result["phone_number"],
                "info": "Template message sent. User can now receive regular messages for 24 hours."
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": result["error"],
                "phone_number": result["phone_number"],
                "details": result.get("response", {})
            }), 400

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/test-webhook", methods=["POST"])
def test_webhook():
    """
    Test endpoint to simulate incoming webhook
    """
    print("🧪 Test webhook called!")
    print(f"Headers: {dict(request.headers)}")
    print(f"Data: {request.get_json()}")
    return jsonify({"status": "test webhook received", "data": request.get_json()}), 200

@app.route("/webhook-status")
def webhook_status():
    """
    Check webhook configuration status
    """
    return f"""
    <h1>🔗 Webhook Configuration Status</h1>

    <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0;">
        <h2>Current Configuration:</h2>
        <ul>
            <li><strong>Bot Server:</strong> http://localhost:8000</li>
            <li><strong>Webhook URL in Meta:</strong> {WEBHOOK_URL}</li>
            <li><strong>Verify Token:</strong> {VERIFY_TOKEN}</li>
            <li><strong>Phone Number ID:</strong> {PHONE_NUMBER_ID}</li>
        </ul>
    </div>

    <div style="background: #ffebee; padding: 20px; border-radius: 10px; margin: 20px 0; border-left: 4px solid #f44336;">
        <h2>❌ Problem Detected:</h2>
        <p><strong>Your webhook URL doesn't point to your bot!</strong></p>
        <p>WhatsApp is sending messages to <code>{WEBHOOK_URL}</code> but your bot is running on <code>http://localhost:8000</code></p>
    </div>

    <div style="background: #e8f5e8; padding: 20px; border-radius: 10px; margin: 20px 0; border-left: 4px solid #4caf50;">
        <h2>✅ Solutions:</h2>

        <h3>Option 1: Use ngrok (Recommended for testing)</h3>
        <ol>
            <li>Install ngrok: <a href="https://ngrok.com/download" target="_blank">https://ngrok.com/download</a></li>
            <li>Run: <code>ngrok http 8000</code></li>
            <li>Copy the https URL (e.g., https://abc123.ngrok.io)</li>
            <li>Update webhook URL in Meta Developer Console to: <code>https://abc123.ngrok.io/webhook</code></li>
        </ol>

        <h3>Option 2: Deploy to public server</h3>
        <ol>
            <li>Deploy your bot to Heroku, Railway, or similar</li>
            <li>Update webhook URL to your public server</li>
        </ol>

        <h3>Option 3: Use BotSailor webhook forwarding</h3>
        <ol>
            <li>Configure BotSailor to forward webhooks to your local server</li>
            <li>Or run your bot on BotSailor's infrastructure</li>
        </ol>
    </div>

    <h3>🧪 Test Your Webhook:</h3>
    <p>Once configured, test with:</p>
    <pre>curl -X POST http://localhost:8000/test-webhook -H "Content-Type: application/json" -d '{{"test": "message"}}'</pre>

    <p><a href="/troubleshoot">📋 Full Troubleshooting Guide</a></p>
    """

@app.route("/troubleshoot", methods=["GET"])
def troubleshoot():
    """
    Troubleshooting guide for message delivery issues
    """
    return """
    <h1>📱 WhatsApp Message Delivery Troubleshooting</h1>

    <h2>🔍 Why Some Messages Don't Deliver (Even When API Shows Success)</h2>

    <h3>📋 WhatsApp Business API Rules:</h3>
    <ul>
        <li><strong>24-Hour Window:</strong> You can only send free-form messages within 24 hours after a user messages you first</li>
        <li><strong>Template Messages:</strong> For first contact or after 24-hour window, you must use approved template messages</li>
        <li><strong>Opt-in Required:</strong> Users must have opted in to receive messages from your business</li>
        <li><strong>Valid WhatsApp Number:</strong> The phone number must be registered with WhatsApp</li>
    </ul>

    <h3>🛠️ Solutions:</h3>
    <ol>
        <li><strong>For First Contact:</strong> Use template messages first
            <pre>curl -X POST http://127.0.0.1:8000/send-template \\
  -H "Content-Type: application/json" \\
  -d '{"to": "+2349025794407"}'</pre>
        </li>
        <li><strong>Ask Users to Message First:</strong> Have users send "Hi" to your WhatsApp Business number</li>
        <li><strong>Check Message Window:</strong> Send messages within 24 hours of user's last message</li>
        <li><strong>Use Enhanced Logging:</strong> Check console for detailed error messages</li>
    </ol>

    <h3>📊 Test Your Numbers:</h3>
    <p><strong>Working:</strong> +2348144493361 (likely messaged you first)</p>
    <p><strong>Not Working:</strong> +2349025794407 (needs template message first)</p>

    <h3>🔗 Useful Endpoints:</h3>
    <ul>
        <li><a href="/enhanced-chat">Enhanced Chat Interface</a></li>
        <li><strong>POST /send-template</strong> - Send template message for first contact</li>
        <li><strong>POST /send</strong> - Send regular message (24-hour window required)</li>
    </ul>

    <h3>🎯 Quick Fix for Your Current Issue:</h3>
    <div style="background: #e8f5e8; padding: 15px; border-radius: 5px; margin: 10px 0;">
        <p><strong>For +2349025794407 to receive messages:</strong></p>
        <ol>
            <li>Ask them to send "Hi" to your WhatsApp Business number: <strong>+234 837 445 0627</strong></li>
            <li>Wait for them to message you first</li>
            <li>Then you can send regular messages for 24 hours</li>
        </ol>
    </div>

    <p><em>💡 Tip: Always ask new contacts to message your business number first. This is how WhatsApp Business API works!</em></p>
    """

@app.route("/user-guide")
def user_guide():
    """
    Guide for users on how to receive messages
    """
    return f"""
    <h1>📱 How to Receive Messages from Our WhatsApp Bot</h1>

    <div style="background: #e3f2fd; padding: 20px; border-radius: 10px; margin: 20px 0;">
        <h2>🚀 Quick Setup (Takes 30 seconds)</h2>
        <ol style="font-size: 18px; line-height: 1.6;">
            <li><strong>Open WhatsApp</strong> on your phone</li>
            <li><strong>Send "Hi"</strong> to this number: <strong style="color: #25D366;">+234 837 445 0627</strong></li>
            <li><strong>That's it!</strong> You can now receive messages from our bot for 24 hours</li>
        </ol>
    </div>

    <h3>❓ Why Do I Need to Message First?</h3>
    <p>WhatsApp Business API requires users to opt-in by messaging the business first. This prevents spam and ensures you want to receive messages.</p>

    <h3>⏰ How Long Does It Last?</h3>
    <p>Once you message us, you can receive messages for 24 hours. After that, just send another "Hi" to reset the window.</p>

    <h3>📞 Our WhatsApp Business Number:</h3>
    <div style="background: #25D366; color: white; padding: 15px; border-radius: 10px; text-align: center; font-size: 24px; font-weight: bold;">
        +234 837 445 0627
    </div>

    <p style="text-align: center; margin-top: 20px;">
        <em>Save this number and send "Hi" to get started! 🚀</em>
    </p>
    """

@app.route("/", methods=["GET"])
def home():
    """
    Home page with bot status
    """
    return """
    <h1>WhatsApp Business API Bot</h1>
    <p>Bot is running successfully!</p>
    <h3>Configuration Status:</h3>
    <ul>
        <li>Phone Number ID: {}</li>
        <li>Webhook URL: {}</li>
        <li>Business Account ID: {}</li>
    </ul>
    <h3>Available Interfaces:</h3>
    <ul>
        <li><a href="/enhanced-chat" target="_blank">🚀 Enhanced Chat Interface</a> (Recommended)</li>
        <li><a href="/chat" target="_blank">🌐 Simple Chat Interface</a></li>
        <li><a href="/troubleshoot" target="_blank">🔧 Message Delivery Troubleshooting</a></li>
        <li><a href="/user-guide" target="_blank">📋 User Guide - How to Receive Messages</a></li>
        <li><a href="/webhook-status" target="_blank">🔗 Webhook Configuration Status</a></li>
        <li>GET /webhook - Webhook verification</li>
        <li>POST /webhook - Receive messages</li>
        <li>POST /send - Send messages manually</li>
        <li>POST /send-template - Send template messages (first contact)</li>
    </ul>
    """.format(
        PHONE_NUMBER_ID if PHONE_NUMBER_ID != "YOUR_PHONE_NUMBER_ID" else "⚠️ NOT CONFIGURED",
        WEBHOOK_URL,
        WHATSAPP_BUSINESS_ACCOUNT_ID
    )

@app.route("/chat")
def chat_interface():
    """
    Simple web chat interface
    """
    return render_template("chat.html")

@app.route("/enhanced-chat")
def enhanced_chat_interface():
    """
    Enhanced web chat interface with contacts and message history
    """
    return render_template("enhanced_chat.html")

@app.route("/api/status")
def api_status():
    """
    API endpoint to check bot status
    """
    return jsonify({
        "status": "online",
        "phone_number_id": PHONE_NUMBER_ID,
        "business_account_id": WHATSAPP_BUSINESS_ACCOUNT_ID,
        "webhook_url": WEBHOOK_URL
    })

def initialize_bot():
    """Initialize bot configuration"""
    global PHONE_NUMBER_ID, WHATSAPP_API_URL

    print("Starting WhatsApp Business API Bot...")
    print(f"Webhook URL: {WEBHOOK_URL}")
    print(f"Business Account ID: {WHATSAPP_BUSINESS_ACCOUNT_ID}")
    print(f"App ID: {APP_ID}")

    # Auto-detect Phone Number ID if not set
    if PHONE_NUMBER_ID == "YOUR_PHONE_NUMBER_ID":
        print("\n🔍 Phone Number ID not set, attempting to auto-detect...")
        detected_id = get_phone_number_id()
        if detected_id:
            PHONE_NUMBER_ID = detected_id
            WHATSAPP_API_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{PHONE_NUMBER_ID}/messages"
            print(f"✅ Phone Number ID set to: {PHONE_NUMBER_ID}")
        else:
            print("❌ Could not auto-detect Phone Number ID. Please set it manually in .env file.")
            print("You can find it in your WhatsApp Business API dashboard.")
    else:
        print(f"Phone Number ID: {PHONE_NUMBER_ID}")

    print(f"\n🚀 Bot is ready!")
    print("Available endpoints:")
    print("  - GET  /         : Status page")
    print("  - GET  /webhook  : Webhook verification")
    print("  - POST /webhook  : Receive messages")
    print("  - POST /send     : Send messages manually")
    print("\n" + "="*50)

if __name__ == "__main__":
    # Initialize bot configuration
    initialize_bot()

    # Run Flask app
    port = int(os.getenv("PORT", 8000))  # Render uses PORT environment variable
    app.run(host="0.0.0.0", port=port, debug=False)  # Disable debug in production
