#!/usr/bin/env python3
import requests
import json

BACKEND_URL = "https://c8483016-28e3-4c32-82b5-fe040e32c737.preview.emergentagent.com/api"

# Login first
user_login = {
    "email": "hpdanielvb@gmail.com",
    "password": "123456"
}

response = requests.post(f"{BACKEND_URL}/auth/login", json=user_login)
if response.status_code == 200:
    auth_token = response.json().get("access_token")
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Test invalid type
    invalid_type_data = {
        "tipo": "invalid_type",
        "nome": "Test Invalid Type",
        "valor_total": 10000.00,
        "parcela_mensal": 500.00,
        "quantidade_parcelas": 24,
        "juros_mensal": 1.0,
        "taxa_administrativa": 100.00,
        "seguro": 50.00,
        "data_inicio": "2024-01-01T00:00:00",
        "data_vencimento": "2026-01-01T00:00:00"
    }
    
    print("Testing invalid type...")
    invalid_response = requests.post(f"{BACKEND_URL}/contratos", json=invalid_type_data, headers=headers)
    print(f"Status: {invalid_response.status_code}")
    print(f"Response: {invalid_response.text}")
    
else:
    print("Login failed")