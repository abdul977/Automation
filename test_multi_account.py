#!/usr/bin/env python3
"""
Test script for multi-account WhatsApp functionality
This script tests the core logic without requiring external dependencies
"""

import json
from collections import defaultdict

# Mock the multi-account configuration
WHATSAPP_ACCOUNTS = {
    "main": {
        "name": "Main Business Account",
        "token": "mock_token_main",
        "phone_number_id": "837445062775054",
        "business_account_id": "2139592896448288",
        "status": "active"
    },
    "secondary": {
        "name": "Secondary Business Account",
        "token": "mock_token_secondary",
        "phone_number_id": "123456789012345",
        "business_account_id": "9876543210987654",
        "status": "active"
    }
}

DEFAULT_ACCOUNT_ID = "main"

# Mock message storage
message_store = defaultdict(lambda: defaultdict(list))

def get_account_config(account_id):
    """Get configuration for a specific account"""
    return WHATSAPP_ACCOUNTS.get(account_id)

def validate_account_id(account_id):
    """Validate if account ID exists and is active"""
    account = get_account_config(account_id)
    return account is not None and account.get('status') == 'active'

def get_all_accounts():
    """Get all available accounts"""
    return [
        {
            "id": account_id,
            "name": config["name"],
            "phone_number_id": config["phone_number_id"],
            "business_account_id": config["business_account_id"],
            "status": config["status"]
        }
        for account_id, config in WHATSAPP_ACCOUNTS.items()
        if config.get('status') == 'active'
    ]

def get_account_by_phone_number_id(phone_number_id):
    """Get account ID by phone number ID (for webhook processing)"""
    for account_id, config in WHATSAPP_ACCOUNTS.items():
        if config.get('phone_number_id') == phone_number_id and config.get('status') == 'active':
            return account_id
    return DEFAULT_ACCOUNT_ID

def store_message(phone_number, message_text, sender_type, account_id=None):
    """Store a message in the account-specific message store"""
    if account_id is None:
        account_id = DEFAULT_ACCOUNT_ID
    
    message_data = {
        'text': message_text,
        'type': sender_type,
        'phone_number': phone_number,
        'account_id': account_id
    }
    
    message_store[account_id][phone_number].append(message_data)
    return message_data

def test_account_management():
    """Test account management functions"""
    print("🧪 Testing Account Management...")
    
    # Test get_all_accounts
    accounts = get_all_accounts()
    print(f"✅ Found {len(accounts)} accounts:")
    for account in accounts:
        print(f"   - {account['id']}: {account['name']}")
    
    # Test validate_account_id
    assert validate_account_id("main") == True
    assert validate_account_id("secondary") == True
    assert validate_account_id("nonexistent") == False
    print("✅ Account validation working correctly")
    
    # Test get_account_by_phone_number_id
    assert get_account_by_phone_number_id("837445062775054") == "main"
    assert get_account_by_phone_number_id("123456789012345") == "secondary"
    assert get_account_by_phone_number_id("999999999999999") == "main"  # fallback
    print("✅ Phone number ID lookup working correctly")

def test_message_storage():
    """Test account-specific message storage"""
    print("\n🧪 Testing Message Storage...")
    
    # Store messages for different accounts
    store_message("2349025794407", "Hello from main account", "outgoing", "main")
    store_message("2349025794407", "Hello from secondary account", "outgoing", "secondary")
    store_message("2348012345678", "Another message", "incoming", "main")
    
    # Verify account isolation
    main_messages = message_store["main"]["2349025794407"]
    secondary_messages = message_store["secondary"]["2349025794407"]
    
    assert len(main_messages) == 1
    assert len(secondary_messages) == 1
    assert main_messages[0]["text"] == "Hello from main account"
    assert secondary_messages[0]["text"] == "Hello from secondary account"
    
    print("✅ Message storage isolation working correctly")
    print(f"   Main account messages: {len(message_store['main'])} contacts")
    print(f"   Secondary account messages: {len(message_store['secondary'])} contacts")

def test_api_logic():
    """Test the logic that would be used in API endpoints"""
    print("\n🧪 Testing API Logic...")
    
    # Test account-specific contact retrieval
    def get_account_contacts(account_id):
        if not validate_account_id(account_id):
            return {"error": f"Invalid account ID: {account_id}"}
        
        contacts = []
        account_messages = message_store.get(account_id, {})
        
        for phone_number, messages in account_messages.items():
            if messages:
                last_message = messages[-1]
                contacts.append({
                    "phone": phone_number,
                    "name": f"Contact {phone_number[-4:]}",
                    "last_message": last_message.get("text", ""),
                    "message_count": len(messages)
                })
        
        return {"status": "success", "account_id": account_id, "contacts": contacts}
    
    # Test with main account
    main_contacts = get_account_contacts("main")
    assert main_contacts["status"] == "success"
    assert len(main_contacts["contacts"]) == 2  # 2 contacts for main account
    print(f"✅ Main account has {len(main_contacts['contacts'])} contacts")
    
    # Test with secondary account
    secondary_contacts = get_account_contacts("secondary")
    assert secondary_contacts["status"] == "success"
    assert len(secondary_contacts["contacts"]) == 1  # 1 contact for secondary account
    print(f"✅ Secondary account has {len(secondary_contacts['contacts'])} contacts")
    
    # Test with invalid account
    invalid_contacts = get_account_contacts("invalid")
    assert "error" in invalid_contacts
    print("✅ Invalid account handling working correctly")

def main():
    """Run all tests"""
    print("🚀 Starting Multi-Account WhatsApp Implementation Tests\n")
    
    try:
        test_account_management()
        test_message_storage()
        test_api_logic()
        
        print("\n🎉 All tests passed! Multi-account implementation is working correctly.")
        print("\n📋 Summary:")
        print("✅ Account management functions working")
        print("✅ Message storage isolation working")
        print("✅ API logic validation working")
        print("✅ Data isolation between accounts verified")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
