import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "EAAQEKbLnBZAMBPetZCCPqKZALn7S5D1LswpqvOQhDajKepWyaMzZAdzHDwLYsDVK5ZCbR0nhxU2nYM7UvdMvVcWBahJA4iIuZBVPIP2vqGN8apucWAj9Dnp21vuKDS4PP78qFB87Xf330gmjECckjo7Owq4ank8ZA5ZB659by2Vz7ZAOZAub7B05yi6OrfGwvikQZDZD")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID", "837445062775054")
GRAPH_API_VERSION = "v18.0"
WHATSAPP_API_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{PHONE_NUMBER_ID}/messages"

def normalize_phone_number(phone_number):
    """
    Normalize phone number to consistent format for Nigerian numbers
    """
    if not phone_number:
        return phone_number

    # Remove all non-digit characters
    digits_only = ''.join(filter(str.isdigit, phone_number))

    # Handle Nigerian numbers
    if digits_only.startswith('234'):
        return digits_only
    elif digits_only.startswith('0') and len(digits_only) == 11:
        return '234' + digits_only[1:]
    elif len(digits_only) == 10:
        return '234' + digits_only
    else:
        return digits_only

def send_whatsapp_message(to_phone_number, message_text, message_type="text"):
    """
    Send a message via WhatsApp Business API

    Args:
        to_phone_number (str): Recipient's phone number
        message_text (str): Message content to send
        message_type (str): Type of message ("text" or "template")

    Returns:
        requests.Response: API response object
    """
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    # Format phone number for WhatsApp API
    normalized_phone = normalize_phone_number(to_phone_number)
    formatted_phone = f"+{normalized_phone}"

    if message_type == "template":
        payload = {
            "messaging_product": "whatsapp",
            "to": formatted_phone,
            "type": "template",
            "template": {
                "name": "hello_world",
                "language": {"code": "en_US"}
            }
        }
    else:
        payload = {
            "messaging_product": "whatsapp",
            "to": formatted_phone,
            "type": "text",
            "text": {"body": message_text}
        }

    try:
        response = requests.post(WHATSAPP_API_URL, headers=headers, json=payload)
        return response
    except requests.exceptions.RequestException as e:
        print(f"Error sending message: {e}")
        return None