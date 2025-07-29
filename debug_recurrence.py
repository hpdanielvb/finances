#!/usr/bin/env python3
"""
Debug test for Recurrence System to identify the issue
"""

import requests
import json
from datetime import datetime

# Configuration
BACKEND_URL = "https://db4bdb91-f1ea-427f-9933-fb4ee66428b9.preview.emergentagent.com/api"

# Test credentials
TEST_USER_LOGIN = {
    "email": "hpdanielvb@gmail.com",
    "password": "123456"
}

def debug_recurrence_system():
    print("🔍 DEBUGGING RECURRENCE SYSTEM")
    
    # Authenticate
    response = requests.post(f"{BACKEND_URL}/auth/login", json=TEST_USER_LOGIN)
    if response.status_code != 200:
        print(f"❌ Authentication failed: {response.status_code}")
        return
    
    data = response.json()
    auth_token = data.get("access_token")
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    print("✅ Authentication successful")
    
    # Get accounts
    accounts_response = requests.get(f"{BACKEND_URL}/accounts", headers=headers)
    if accounts_response.status_code != 200:
        print(f"❌ Cannot get accounts: {accounts_response.status_code}")
        return
    
    accounts = accounts_response.json()
    if not accounts:
        print("❌ No accounts available")
        return
    
    account_id = accounts[0]["id"]
    print(f"✅ Using account: {accounts[0]['name']}")
    
    # Test creating a recurrence rule
    rule_data = {
        "name": "Test Salary Rule",
        "description": "Test monthly salary",
        "transaction_description": "Monthly Salary",
        "transaction_value": 5000.00,
        "transaction_type": "Receita",
        "account_id": account_id,
        "recurrence_pattern": "mensal",
        "interval": 1,
        "start_date": "2025-01-01T00:00:00",
        "auto_create": False,
        "require_confirmation": True
    }
    
    print("\n🔍 Testing recurrence rule creation...")
    print(f"Request data: {json.dumps(rule_data, indent=2)}")
    
    create_response = requests.post(f"{BACKEND_URL}/recurrence/rules", 
                                  json=rule_data, headers=headers)
    
    print(f"\nResponse status: {create_response.status_code}")
    print(f"Response headers: {dict(create_response.headers)}")
    
    try:
        response_data = create_response.json()
        print(f"Response data: {json.dumps(response_data, indent=2)}")
        
        if create_response.status_code == 200:
            print("✅ Rule creation successful")
            if 'id' in response_data:
                print(f"✅ Rule ID: {response_data['id']}")
            else:
                print("❌ No 'id' field in response")
                print(f"Available fields: {list(response_data.keys())}")
        else:
            print(f"❌ Rule creation failed: {response_data}")
    except Exception as e:
        print(f"❌ Error parsing response: {e}")
        print(f"Raw response: {create_response.text}")

if __name__ == "__main__":
    debug_recurrence_system()