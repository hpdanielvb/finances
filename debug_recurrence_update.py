#!/usr/bin/env python3
"""
Debug test for Recurrence System UPDATE operation
"""

import requests
import json

# Configuration
BACKEND_URL = "https://2353e19b-098e-4c36-9781-1e4f6c502504.preview.emergentagent.com/api"

# Test credentials
TEST_USER_LOGIN = {
    "email": "hpdanielvb@gmail.com",
    "password": "123456"
}

def debug_recurrence_update():
    print("🔍 DEBUGGING RECURRENCE UPDATE")
    
    # Authenticate
    response = requests.post(f"{BACKEND_URL}/auth/login", json=TEST_USER_LOGIN)
    data = response.json()
    auth_token = data.get("access_token")
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Get existing rules
    list_response = requests.get(f"{BACKEND_URL}/recurrence/rules", headers=headers)
    if list_response.status_code != 200:
        print(f"❌ Cannot get rules: {list_response.status_code}")
        return
    
    rules = list_response.json()
    if not rules:
        print("❌ No rules available")
        return
    
    rule_id = rules[0]["id"]
    print(f"✅ Using rule ID: {rule_id}")
    
    # Test updating the rule
    update_data = {
        "name": "Updated Rule Name",
        "transaction_value": 5500.00,
        "observation": "Updated observation"
    }
    
    print(f"\n🔍 Testing rule update...")
    print(f"Update data: {json.dumps(update_data, indent=2)}")
    
    update_response = requests.put(f"{BACKEND_URL}/recurrence/rules/{rule_id}", 
                                 json=update_data, headers=headers)
    
    print(f"\nUpdate response status: {update_response.status_code}")
    
    try:
        response_data = update_response.json()
        print(f"Update response data: {json.dumps(response_data, indent=2)}")
        
        if update_response.status_code == 200:
            print("✅ Rule update successful")
            if 'name' in response_data:
                print(f"✅ Updated name: {response_data['name']}")
            else:
                print("❌ No 'name' field in response")
                print(f"Available fields: {list(response_data.keys())}")
        else:
            print(f"❌ Rule update failed: {response_data}")
    except Exception as e:
        print(f"❌ Error parsing response: {e}")
        print(f"Raw response: {update_response.text}")

if __name__ == "__main__":
    debug_recurrence_update()