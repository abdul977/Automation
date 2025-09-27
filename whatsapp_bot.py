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
import redis
import threading
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from dotenv import load_dotenv
from datetime import datetime
from collections import defaultdict

# Load environment variables
load_dotenv()

# Redis key for storing accounts
REDIS_ACCOUNTS_KEY = "whatsapp_accounts"

# In-memory store for accounts, loaded on startup
WHATSAPP_ACCOUNTS = {}

# Legacy Configuration (for backward compatibility)
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "whatsapp_verify_token_2024")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://automation-9lq8.onrender.com/webhook")
APP_ID = os.getenv("APP_ID", "1130477048497555")
APP_SECRET = os.getenv("APP_SECRET", "your_app_secret")
GRAPH_API_VERSION = "v18.0"
DEFAULT_ACCOUNT_ID = "main"

# Redis Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "redis-15049.c274.us-east-1-3.ec2.redns.redis-cloud.com")
REDIS_PORT = int(os.getenv("REDIS_PORT", "15049"))
REDIS_USERNAME = os.getenv("REDIS_USERNAME", "default")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "kJovVpgJkDeeZVvL5A6vhCznvWQ06kHU")

# Initialize Flask app and SocketIO
app = Flask(__name__)
app.config['SECRET_KEY'] = 'whatsapp_bot_secret_key'
CORS(app)  # Enable CORS for all routes
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize Redis connection
try:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        decode_responses=True,
        username=REDIS_USERNAME,
        password=REDIS_PASSWORD,
    )
    redis_client.ping()
    print("✅ Redis connection successful!")
except Exception as e:
    print(f"❌ Redis connection failed: {e}")
    redis_client = None

# Message storage system (fallback to in-memory if Redis fails)
message_store = defaultdict(lambda: defaultdict(list))

# --- Multi-Account Management ---

def load_accounts_from_env():
    """Loads the default accounts from environment variables."""
    return {
        "main": {
            "name": "Main Business Account",
            "token": os.getenv("WHATSAPP_TOKEN", "EAAQEKbLnBZAMBPetZCCPqKZALn7S5D1LswpqvOQhDajKepWyaMzZAdzHDwLYsDVK5ZCbR0nhxU2nYM7UvdMvVcWBahJA4iIuZBVPIP2vqGN8apucWAj9Dnp21vuKDS4PP78qFB87Xf330gmjECckjo7Owq4ank8ZA5ZB659by2Vz7ZAOZAub7B05yi6OrfGwvikQZDZD"),
            "phone_number_id": os.getenv("PHONE_NUMBER_ID", "837445062775054"),
            "business_account_id": os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID", "2139592896448288"),
            "status": "active"
        },
        "secondary": {
            "name": "Secondary Business Account",
            "token": os.getenv("WHATSAPP_TOKEN_2", "EAAQEKbLnBZAMBPetZCCPqKZALn7S5D1LswpqvOQhDajKepWyaMzZAdzHDwLYsDVK5ZCbR0nhxU2nYM7UvdMvVcWBahJA4iIuZBVPIP2vqGN8apucWAj9Dnp21vuKDS4PP78qFB87Xf330gmjECckjo7Owq4ank8ZA5ZB659by2Vz7ZAOZAub7B05yi6OrfGwvikQZDZD"),
            "phone_number_id": os.getenv("PHONE_NUMBER_ID_2", "712795768594387"),
            "business_account_id": os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID_2", "1840273509923388"),
            "status": "active"
        }
    }

def load_accounts():
    """Load accounts from environment variables and then from Redis."""
    global WHATSAPP_ACCOUNTS
    accounts = load_accounts_from_env()
    if redis_client:
        try:
            stored_accounts = redis_client.get(REDIS_ACCOUNTS_KEY)
            if stored_accounts:
                accounts.update(json.loads(stored_accounts))
                print("✅ Loaded additional accounts from Redis.")
        except Exception as e:
            print(f"⚠️ Could not load accounts from Redis: {e}")
    WHATSAPP_ACCOUNTS = accounts

def save_accounts():
    """Save the current accounts dictionary to Redis."""
    if redis_client:
        try:
            redis_client.set(REDIS_ACCOUNTS_KEY, json.dumps(WHATSAPP_ACCOUNTS))
            print("✅ Saved accounts to Redis.")
        except Exception as e:
            print(f"⚠️ Could not save accounts to Redis: {e}")

def get_account_config(account_id):
    return WHATSAPP_ACCOUNTS.get(account_id)

def get_account_api_url(account_id):
    account = get_account_config(account_id)
    if not account:
        return None
    return f"https://graph.facebook.com/{GRAPH_API_VERSION}/{account['phone_number_id']}/messages"

def validate_account_id(account_id):
    account = get_account_config(account_id)
    return account is not None and account.get('status') == 'active'

def get_all_accounts():
    return [
        {
            "id": account_id,
            "name": config["name"],
            "phone_number_id": config["phone_number_id"],
            "business_account_id": config["business_account_id"],
            "status": config["status"]
        }
        for account_id, config in WHATSAPP_ACCOUNTS.items()
    ]

def get_account_by_phone_number_id(phone_number_id):
    for account_id, config in WHATSAPP_ACCOUNTS.items():
        if config.get('phone_number_id') == phone_number_id:
            return account_id
    return None

def get_account_by_ids(business_account_id, phone_number_id):
    """Get account ID by business_account_id and phone_number_id."""
    for account_id, config in WHATSAPP_ACCOUNTS.items():
        if config.get('business_account_id') == business_account_id and config.get('phone_number_id') == phone_number_id:
            return account_id
    return None

# ... (rest of the helper functions like normalize_phone_number, store_message, etc.)


# --- API Endpoints ---

@app.route("/api/accounts", methods=["GET"])
def get_accounts_api():
    """Get all available WhatsApp accounts."""
    return jsonify({"status": "success", "accounts": get_all_accounts()})

@app.route("/api/accounts/add", methods=["POST"])
def add_account_api():
    """Add a new WhatsApp account."""
    data = request.get_json()
    if not data or not all(k in data for k in ['id', 'name', 'token', 'phone_number_id', 'business_account_id']):
        return jsonify({"status": "error", "message": "Missing required account data"}), 400

    account_id = data['id']
    if account_id in WHATSAPP_ACCOUNTS:
        return jsonify({"status": "error", "message": f"Account with ID '{account_id}' already exists"}), 409

    new_account = {
        "name": data['name'],
        "token": data['token'],
        "phone_number_id": data['phone_number_id'],
        "business_account_id": data['business_account_id'],
        "status": data.get('status', 'active')
    }
    WHATSAPP_ACCOUNTS[account_id] = new_account
    save_accounts()
    return jsonify({"status": "success", "message": "Account added successfully", "account": new_account}), 201

@app.route("/api/accounts/<account_id>/update", methods=["PUT"])
def update_account_api(account_id):
    """Update an existing WhatsApp account."""
    if account_id not in WHATSAPP_ACCOUNTS:
        return jsonify({"status": "error", "message": "Account not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No update data provided"}), 400

    # Update only the provided fields
    for key in ['name', 'token', 'phone_number_id', 'business_account_id', 'status']:
        if key in data:
            WHATSAPP_ACCOUNTS[account_id][key] = data[key]
    
    save_accounts()
    return jsonify({"status": "success", "message": "Account updated successfully", "account": WHATSAPP_ACCOUNTS[account_id]})

@app.route("/api/accounts/<account_id>/delete", methods=["DELETE"])
def delete_account_api(account_id):
    """Delete a WhatsApp account."""
    if account_id not in WHATSAPP_ACCOUNTS:
        return jsonify({"status": "error", "message": "Account not found"}), 404

    # Prevent deletion of the default 'main' account for safety
    if account_id == DEFAULT_ACCOUNT_ID:
        return jsonify({"status": "error", "message": "Cannot delete the default main account"}), 403

    deleted_account = WHATSAPP_ACCOUNTS.pop(account_id)
    save_accounts()
    return jsonify({"status": "success", "message": f"Account '{deleted_account['name']}' deleted successfully"})


# ... (rest of the file from send_whatsapp_message onwards, with modifications to use account_id)

# In initialize_bot():
# ...
# load_accounts()
# ...

if __name__ == "__main__":
    load_accounts()
    port = int(os.getenv("PORT", 8000))
    print(f"🚀 Starting server with WebSocket support on port {port}")
    socketio.run(app, host="0.0.0.0", port=port, debug=False, allow_unsafe_werkzeug=True)


def normalize_phone_number(phone_number):
    """
    Normalize phone number to consistent format for Nigerian numbers

    Examples:
    - 09025794407 → 2349025794407
    - +2349025794407 → 2349025794407
    - 2349025794407 → 2349025794407
    """
    if not phone_number:
        return phone_number

    # Remove all non-digit characters
    digits_only = ''.join(filter(str.isdigit, phone_number))

    # Handle Nigerian numbers
    if digits_only.startswith('234'):
        # Already in international format without +
        return digits_only
    elif digits_only.startswith('0') and len(digits_only) == 11:
        # Local Nigerian format (0XXXXXXXXXX) → international (234XXXXXXXXXX)
        return '234' + digits_only[1:]
    elif len(digits_only) == 10:
        # Missing leading 0, assume Nigerian local format
        return '234' + digits_only
    else:
        # Return as-is for other formats
        return digits_only

def store_message(phone_number, message_text, sender_type, message_id=None, timestamp=None, account_id=None):
    """
    Store a message in both Redis and in-memory store, then emit WebSocket event

    Args:
        phone_number: The phone number (without + prefix for consistency)
        message_text: The message content
        sender_type: 'incoming' or 'outgoing'
        message_id: WhatsApp message ID (optional)
        timestamp: Message timestamp (optional, defaults to now)
        account_id: Account ID for multi-account support (optional, defaults to main)
    """
    if timestamp is None:
        timestamp = datetime.now().isoformat()

    if account_id is None:
        account_id = DEFAULT_ACCOUNT_ID

    # Normalize phone number using comprehensive normalization
    normalized_phone = normalize_phone_number(phone_number)

    message_data = {
        'id': message_id or f"{sender_type}_{len(message_store[account_id][normalized_phone])}_{timestamp}",
        'text': message_text,
        'type': sender_type,
        'timestamp': timestamp,
        'phone_number': normalized_phone,
        'account_id': account_id
    }

    # Store in in-memory store (fallback)
    message_store[account_id][normalized_phone].append(message_data)

    # Store in Redis if available
    if redis_client:
        try:
            # Store message in Redis list with account-specific key
            redis_key = f"messages:{account_id}:{normalized_phone}"
            redis_client.lpush(redis_key, json.dumps(message_data))

            # Keep only last 100 messages per contact
            redis_client.ltrim(redis_key, 0, 99)

            # Publish real-time update with account information
            redis_client.publish('message_updates', json.dumps({
                'type': 'new_message',
                'account_id': account_id,
                'phone_number': normalized_phone,
                'message': message_data
            }))

        except Exception as e:
            print(f"⚠️ Redis storage failed: {e}")

    print(f"📝 Stored {sender_type} message for {normalized_phone} (Account: {account_id}): '{message_text[:50]}...'")

    # Emit WebSocket event for real-time updates with account information
    try:
        socketio.emit('new_message', {
            'account_id': account_id,
            'phone_number': normalized_phone,
            'message': message_data
        })
    except Exception as e:
        print(f"⚠️ WebSocket emit failed: {e}")

    return message_data

def get_messages_from_redis(phone_number, account_id=None):
    """
    Get messages for a phone number from Redis for a specific account
    """
    if not redis_client:
        return []

    if account_id is None:
        account_id = DEFAULT_ACCOUNT_ID

    try:
        normalized_phone = normalize_phone_number(phone_number)
        redis_key = f"messages:{account_id}:{normalized_phone}"

        # Get messages from Redis (they're stored in reverse order)
        message_strings = redis_client.lrange(redis_key, 0, -1)
        messages = []

        for msg_str in reversed(message_strings):  # Reverse to get chronological order
            try:
                message_data = json.loads(msg_str)
                messages.append(message_data)
            except json.JSONDecodeError:
                continue

        return messages
    except Exception as e:
        print(f"⚠️ Redis get messages failed: {e}")
        return []

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

def send_whatsapp_message(to_phone_number, message_text, message_type="text", account_id=None):
    """
    Send a message via WhatsApp Business API

    Args:
        to_phone_number (str): Recipient's phone number (with country code, no + sign)
        message_text (str): Message content to send
        message_type (str): Type of message ("text" or "template")
        account_id (str): Account ID to send from (optional, defaults to main)

    Returns:
        dict: API response with detailed status
    """
    if account_id is None:
        account_id = DEFAULT_ACCOUNT_ID

    # Get account configuration
    account_config = get_account_config(account_id)
    if not account_config:
        return {
            "success": False,
            "error": f"Invalid account ID: {account_id}",
            "phone_number": to_phone_number
        }

    headers = {
        "Authorization": f"Bearer {account_config['token']}",
        "Content-Type": "application/json"
    }

    # Format phone number for WhatsApp API (needs + prefix and international format)
    normalized_phone = normalize_phone_number(to_phone_number)
    formatted_phone = f"+{normalized_phone}"

    if message_type == "template":
        # Send template message (for first contact)
        payload = {
            "messaging_product": "whatsapp",
            "to": formatted_phone,
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
            "to": formatted_phone,
            "type": "text",
            "text": {
                "body": message_text
            }
        }

    try:
        # Get account-specific API URL
        api_url = get_account_api_url(account_id)

        print(f"Sending {message_type} message to {formatted_phone} (normalized from {to_phone_number}) via account {account_id}")
        print(f"API URL: {api_url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")

        response = requests.post(api_url, headers=headers, json=payload)
        response_data = response.json()

        print(f"API Response Status: {response.status_code}")
        print(f"API Response: {json.dumps(response_data, indent=2)}")

        if response.status_code == 200:
            print(f"✅ Message sent successfully to {formatted_phone}")
            return {
                "success": True,
                "response": response_data,
                "message_id": response_data.get("messages", [{}])[0].get("id"),
                "phone_number": formatted_phone
            }
        else:
            error_msg = response_data.get("error", {}).get("message", "Unknown error")
            print(f"❌ Failed to send message: {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "response": response_data,
                "phone_number": formatted_phone
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
                    "phone_number": formatted_phone
                }
            except:
                print(f"Raw Error Response: {e.response.text}")

        return {
            "success": False,
            "error": error_msg,
            "phone_number": formatted_phone
        }

# Auto-reply function removed - no longer generating automatic responses

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

                        # Extract phone number ID to determine which account received the message
                        metadata = value.get("metadata", {})
                        phone_number_id = metadata.get("phone_number_id")
                        account_id = get_account_by_phone_number_id(phone_number_id) if phone_number_id else DEFAULT_ACCOUNT_ID

                        print(f"📱 Found {len(messages)} message(s) for account {account_id} (phone_number_id: {phone_number_id})")

                        for message in messages:
                            # Extract sender information
                            sender_phone = message.get("from")
                            message_id = message.get("id")
                            message_type = message.get("type")

                            print(f"📨 Received {message_type} message from {sender_phone} (ID: {message_id}) for account {account_id}")

                            # Only process text messages
                            if message_type == "text":
                                message_text = message.get("text", {}).get("body", "")
                                print(f"💬 Message content: '{message_text}'")

                                # Store incoming message with account ID
                                store_message(
                                    phone_number=sender_phone,
                                    message_text=message_text,
                                    sender_type='incoming',
                                    message_id=message_id,
                                    timestamp=datetime.now().isoformat(),
                                    account_id=account_id
                                )

                                print(f"✅ Message received and stored successfully from {sender_phone}")
                                # Auto-reply functionality removed - messages are received and stored only
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
    Manual endpoint to send messages (supports multi-account)
    Usage: POST /send with JSON body: {"to": "phone_number", "message": "text", "type": "text|template", "business_id": "your_business_id", "phone_id": "your_phone_id"}
    """
    try:
        data = request.get_json()
        to_phone = data.get("to")
        message = data.get("message", "")
        message_type = data.get("type", "text")
        business_id = data.get("business_id")
        phone_id = data.get("phone_id")

        if not to_phone:
            return jsonify({"error": "Missing 'to' parameter"}), 400

        if not business_id or not phone_id:
            return jsonify({"error": "Missing 'business_id' or 'phone_id' parameter"}), 400

        if message_type == "text" and not message:
            return jsonify({"error": "Missing 'message' parameter for text messages"}), 400

        account_id = get_account_by_ids(business_id, phone_id)

        if not account_id:
            return jsonify({"error": f"No account found for business_id {business_id} and phone_id {phone_id}"}), 404

        result = send_whatsapp_message(to_phone, message, message_type, account_id)

        if result["success"]:
            # Store outgoing message with account ID
            store_message(
                phone_number=to_phone,
                message_text=message,
                sender_type='outgoing',
                message_id=result.get('message_id'),
                timestamp=datetime.now().isoformat(),
                account_id=account_id
            )

            return jsonify({
                "status": "success",
                "result": result["response"],
                "message_id": result.get("message_id"),
                "phone_number": result["phone_number"],
                "account_id": account_id,
                "delivery_info": "Message accepted by WhatsApp API. Delivery depends on recipient's opt-in status and 24-hour messaging window."
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": result["error"],
                "phone_number": result["phone_number"],
                "account_id": account_id,
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

@app.route('/test-incoming', methods=['POST'])
def test_incoming_message():
    """Test endpoint to simulate an incoming WhatsApp message"""
    print("🧪 [TEST] Simulating incoming WhatsApp message...")

    # Simulate incoming message data
    test_message_data = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "2139592896448288",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {
                        "display_phone_number": "837445062775054",
                        "phone_number_id": "837445062775054"
                    },
                    "messages": [{
                        "from": "2349025794407",
                        "id": "wamid.TEST123456789",
                        "timestamp": "1726662000",
                        "text": {
                            "body": "Hello! Testing incoming message."
                        },
                        "type": "text"
                    }]
                },
                "field": "messages"
            }]
        }]
    }

    print(f"🧪 [TEST] Simulated message data: {json.dumps(test_message_data, indent=2)}")

    # Process the simulated message using the same logic as the real webhook
    try:
        for entry in test_message_data.get('entry', []):
            for change in entry.get('changes', []):
                if change.get('field') == 'messages':
                    value = change.get('value', {})
                    messages = value.get('messages', [])

                    for message in messages:
                        # Extract sender information
                        sender_phone = message.get("from")
                        message_id = message.get("id")
                        message_type = message.get("type")

                        print(f"🧪 [TEST] Processing {message_type} message from {sender_phone} (ID: {message_id})")

                        # Only process text messages
                        if message_type == "text":
                            message_text = message.get("text", {}).get("body", "")
                            print(f"🧪 [TEST] Message content: '{message_text}'")

                            # Store incoming message
                            store_message(
                                phone_number=sender_phone,
                                message_text=message_text,
                                sender_type='incoming',
                                message_id=message_id,
                                timestamp=datetime.now().isoformat()
                            )
                            print(f"🧪 [TEST] Stored incoming message from {sender_phone}")
                            print(f"🧪 [TEST] Auto-reply functionality removed - message received and stored only")

        return jsonify({"status": "success", "message": "Test message processed and stored"}), 200

    except Exception as e:
        print(f"🧪 [TEST] Error processing test message: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

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

# Multi-Account Management APIs
@app.route("/api/accounts", methods=["GET"])
def get_accounts_api():
    """
    Get all available WhatsApp accounts
    """
    try:
        accounts = get_all_accounts()
        return jsonify({
            "status": "success",
            "accounts": accounts,
            "count": len(accounts)
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/accounts/add", methods=["POST"])
def add_account_api():
    """
    Add a new WhatsApp account
    """
    try:
        data = request.get_json()
        account_id = data.get("id")
        account_name = data.get("name")
        account_token = data.get("token")
        account_phone_number_id = data.get("phone_number_id")
        account_business_account_id = data.get("business_account_id")

        if not all([account_id, account_name, account_token, account_phone_number_id, account_business_account_id]):
            return jsonify({"status": "error", "message": "Missing required account data"}), 400

        if account_id in WHATSAPP_ACCOUNTS:
            return jsonify({"status": "error", "message": f"Account with ID '{account_id}' already exists"}), 400

        WHATSAPP_ACCOUNTS[account_id] = {
            "name": account_name,
            "token": account_token,
            "phone_number_id": account_phone_number_id,
            "business_account_id": account_business_account_id,
            "status": "active"
        }

        return jsonify({
            "status": "success",
            "message": f"Account '{account_name}' added successfully",
            "account": {
                "id": account_id,
                "name": account_name,
                "phone_number_id": account_phone_number_id,
                "business_account_id": account_business_account_id,
                "status": "active"
            }
        }), 201

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/accounts/<account_id>/send", methods=["POST"])
def send_message_from_account_api(account_id):
    """
    Send message from specific account
    Usage: POST /api/accounts/{account_id}/send with JSON body: {"to": "phone_number", "message": "text", "type": "text|template"}
    """
    try:
        # Validate account ID
        if not validate_account_id(account_id):
            return jsonify({"error": f"Invalid or inactive account ID: {account_id}"}), 400

        data = request.get_json()
        to_phone = data.get("to")
        message = data.get("message", "")
        message_type = data.get("type", "text")

        if not to_phone:
            return jsonify({"error": "Missing 'to' parameter"}), 400

        if message_type == "text" and not message:
            return jsonify({"error": "Missing 'message' parameter for text messages"}), 400

        # Send message using specific account
        result = send_whatsapp_message(to_phone, message, message_type, account_id)

        if result["success"]:
            # Store outgoing message with account ID
            store_message(
                phone_number=to_phone,
                message_text=message,
                sender_type='outgoing',
                message_id=result.get('message_id'),
                timestamp=datetime.now().isoformat(),
                account_id=account_id
            )

            return jsonify({
                "status": "success",
                "result": result["response"],
                "message_id": result.get("message_id"),
                "phone_number": result["phone_number"],
                "account_id": account_id,
                "delivery_info": "Message accepted by WhatsApp API. Delivery depends on recipient's opt-in status and 24-hour messaging window."
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": result["error"],
                "phone_number": result["phone_number"],
                "account_id": account_id,
                "details": result.get("response", {})
            }), 400

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/accounts/<account_id>/messages/<phone_number>", methods=["GET"])
def get_account_messages(account_id, phone_number):
    """
    Get message history for a specific phone number from a specific account
    """
    try:
        # Validate account ID
        if not validate_account_id(account_id):
            return jsonify({"error": f"Invalid or inactive account ID: {account_id}"}), 400

        # Normalize phone number
        normalized_phone = normalize_phone_number(phone_number)

        # Try to get messages from Redis first
        messages = get_messages_from_redis(normalized_phone, account_id)

        # Fallback to in-memory store if Redis is unavailable or empty
        if not messages:
            messages = message_store.get(account_id, {}).get(normalized_phone, [])

        return jsonify({
            "status": "success",
            "account_id": account_id,
            "phone_number": normalized_phone,
            "messages": messages,
            "count": len(messages)
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/accounts/<account_id>/contacts", methods=["GET"])
def get_account_contacts(account_id):
    """
    Get all contacts with message history for a specific account
    """
    try:
        # Validate account ID
        if not validate_account_id(account_id):
            return jsonify({"error": f"Invalid or inactive account ID: {account_id}"}), 400

        contacts = []

        # Get contacts from in-memory store for this account
        account_messages = message_store.get(account_id, {})
        for phone_number, messages in account_messages.items():
            if messages:  # Only include contacts with messages
                last_message = messages[-1]  # Get most recent message
                contacts.append({
                    "phone": phone_number,
                    "name": f"Contact {phone_number[-4:]}",  # Simple name based on last 4 digits
                    "last_message": last_message.get("text", ""),
                    "last_message_time": last_message.get("timestamp", ""),
                    "message_count": len(messages),
                    "last_message_type": last_message.get("type", "")
                })

        # Sort contacts by last message time (most recent first)
        contacts.sort(key=lambda x: x["last_message_time"], reverse=True)

        return jsonify({
            "status": "success",
            "account_id": account_id,
            "contacts": contacts,
            "count": len(contacts)
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# API endpoints for Enhanced Chat Interface (Legacy - maintained for backward compatibility)
@app.route("/api/messages/<phone_number>", methods=["GET"])
def get_messages(phone_number):
    """
    Get message history for a specific phone number (supports account_id parameter for multi-account)
    Usage: GET /api/messages/{phone_number}?account_id=main
    """
    try:
        # Get account_id from query parameters (defaults to main for backward compatibility)
        account_id = request.args.get('account_id', DEFAULT_ACCOUNT_ID)

        # Validate account ID if provided
        if account_id != DEFAULT_ACCOUNT_ID and not validate_account_id(account_id):
            return jsonify({"error": f"Invalid or inactive account ID: {account_id}"}), 400

        # Normalize phone number using comprehensive normalization
        normalized_phone = normalize_phone_number(phone_number)

        # Try to get messages from Redis first
        messages = get_messages_from_redis(normalized_phone, account_id)

        # Fallback to in-memory store if Redis is unavailable or empty
        if not messages:
            messages = message_store.get(account_id, {}).get(normalized_phone, [])

        return jsonify({
            "status": "success",
            "account_id": account_id,
            "phone_number": normalized_phone,
            "messages": messages,
            "count": len(messages)
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/contacts", methods=["GET"])
def get_contacts():
    """
    Get all contacts that have message history (supports account_id parameter for multi-account)
    Usage: GET /api/contacts?account_id=main
    """
    try:
        # Get account_id from query parameters (defaults to main for backward compatibility)
        account_id = request.args.get('account_id', DEFAULT_ACCOUNT_ID)

        # Validate account ID if provided
        if account_id != DEFAULT_ACCOUNT_ID and not validate_account_id(account_id):
            return jsonify({"error": f"Invalid or inactive account ID: {account_id}"}), 400

        contacts = []
        account_messages = message_store.get(account_id, {})

        for phone_number, messages in account_messages.items():
            if messages:  # Only include contacts with messages
                last_message = messages[-1]  # Get most recent message
                contacts.append({
                    "phone_number": phone_number,
                    "display_name": f"+{phone_number}",  # Could be enhanced with actual names
                    "last_message": last_message["text"][:50] + "..." if len(last_message["text"]) > 50 else last_message["text"],
                    "last_message_time": last_message["timestamp"],
                    "last_message_type": last_message["type"],
                    "message_count": len(messages)
                })

        # Sort by most recent message
        contacts.sort(key=lambda x: x["last_message_time"], reverse=True)

        return jsonify({
            "status": "success",
            "account_id": account_id,
            "contacts": contacts,
            "count": len(contacts)
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/messages", methods=["GET"])
def get_all_messages():
    """
    Get all messages across all contacts (for debugging)
    """
    try:
        all_messages = []
        for phone_number, messages in message_store.items():
            for message in messages:
                message_copy = message.copy()
                message_copy["contact_phone"] = phone_number
                all_messages.append(message_copy)

        # Sort by timestamp
        all_messages.sort(key=lambda x: x["timestamp"], reverse=True)

        return jsonify({
            "status": "success",
            "messages": all_messages,
            "count": len(all_messages)
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

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

# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    print('🔌 Client connected to WebSocket')

@socketio.on('disconnect')
def handle_disconnect():
    print('🔌 Client disconnected from WebSocket')

@socketio.on('join_room')
def handle_join_room(data):
    """Join a room for a specific phone number to receive real-time updates"""
    phone_number = data.get('phone_number')
    if phone_number:
        normalized_phone = normalize_phone_number(phone_number)
        socketio.join_room(f"chat_{normalized_phone}")
        print(f'📱 Client joined room for {normalized_phone}')

if __name__ == "__main__":
    # Initialize bot configuration
    initialize_bot()

    # Run Flask app with SocketIO
    port = int(os.getenv("PORT", 8000))  # Render uses PORT environment variable
    print(f"🚀 Starting server with WebSocket support on port {port}")

    # Use allow_unsafe_werkzeug for production deployment
    # In a real production environment, you'd use a proper WSGI server
    socketio.run(app, host="0.0.0.0", port=port, debug=False, allow_unsafe_werkzeug=True)
