#!/usr/bin/env python3
"""
OrçaZenFinanceiro Backend API Testing Suite - COMPLETE ENHANCED VERSION
Tests all backend endpoints with Brazilian test data including:
- Enhanced JWT Authentication with Session Persistence
- Advanced Account Management with Credit Card Support
- Advanced Transaction Management with Recurrence
- Transfer Between Accounts System
- Budget Management System
- File Upload System
- Enhanced Dashboard API with Analytics
- Advanced Reports and Analytics API
- Comprehensive Brazilian Categories System
"""

import requests
import json
from datetime import datetime, timedelta
import uuid
import base64
import io

# Configuration
BACKEND_URL = "https://d760404c-d8e2-4b6c-a73d-a54db14f2378.preview.emergentagent.com/api"

# Test data with Brazilian names and content
TEST_USER_DATA = {
    "name": "Maria Silva Santos",
    "email": "maria.silva@email.com.br",
    "password": "MinhaSenh@123",
    "confirm_password": "MinhaSenh@123"
}

TEST_USER_LOGIN = {
    "email": "maria.silva@email.com.br", 
    "password": "MinhaSenh@123"
}

# Global variables to store test data
auth_token = None
user_id = None
account_id = None
credit_card_account_id = None
category_id = None
expense_category_id = None
transaction_id = None
budget_id = None

def print_test_result(test_name, success, details=""):
    """Print formatted test results"""
    status = "✅ PASSOU" if success else "❌ FALHOU"
    print(f"\n{status} - {test_name}")
    if details:
        print(f"   Detalhes: {details}")

def test_user_registration():
    """Test enhanced user registration endpoint with password confirmation"""
    global auth_token, user_id
    
    print("\n" + "="*60)
    print("TESTANDO REGISTRO DE USUÁRIO APRIMORADO")
    print("="*60)
    
    try:
        # Test password confirmation validation
        invalid_data = TEST_USER_DATA.copy()
        invalid_data["confirm_password"] = "senhadiferente"
        
        invalid_response = requests.post(f"{BACKEND_URL}/auth/register", json=invalid_data)
        if invalid_response.status_code == 400:
            print_test_result("Validação de confirmação de senha", True, "Rejeitou senhas diferentes")
        else:
            print_test_result("Validação de confirmação de senha", False, "Não rejeitou senhas diferentes")
        
        # Test valid registration
        response = requests.post(f"{BACKEND_URL}/auth/register", json=TEST_USER_DATA)
        
        if response.status_code == 200:
            data = response.json()
            auth_token = data.get("access_token")
            user_info = data.get("user", {})
            user_id = user_info.get("id")
            expires_in = data.get("expires_in")
            
            print_test_result("Registro de usuário", True, 
                            f"Token recebido, usuário: {user_info.get('name')}")
            
            # Verify 30-day token expiry
            if expires_in == 30 * 24 * 3600:  # 30 days in seconds
                print_test_result("Token de 30 dias", True, f"Expiração configurada para 30 dias")
            else:
                print_test_result("Token de 30 dias", False, f"Expiração: {expires_in} segundos")
            
            # Verify token structure
            if auth_token and user_id:
                print_test_result("Token JWT gerado", True, f"Token válido recebido")
                return True
            else:
                print_test_result("Token JWT gerado", False, "Token ou user_id não recebido")
                return False
                
        else:
            print_test_result("Registro de usuário", False, 
                            f"Status: {response.status_code}, Erro: {response.text}")
            return False
            
    except Exception as e:
        print_test_result("Registro de usuário", False, f"Exceção: {str(e)}")
        return False

def test_user_login():
    """Test user login endpoint"""
    global auth_token, user_id
    
    print("\n" + "="*60)
    print("TESTANDO LOGIN DE USUÁRIO")
    print("="*60)
    
    try:
        response = requests.post(f"{BACKEND_URL}/auth/login", json=TEST_USER_LOGIN)
        
        if response.status_code == 200:
            data = response.json()
            auth_token = data.get("access_token")
            user_info = data.get("user", {})
            user_id = user_info.get("id")
            
            print_test_result("Login de usuário", True, 
                            f"Login bem-sucedido para: {user_info.get('name')}")
            
            # Test with wrong password
            wrong_login = TEST_USER_LOGIN.copy()
            wrong_login["password"] = "senhaerrada"
            
            wrong_response = requests.post(f"{BACKEND_URL}/auth/login", json=wrong_login)
            if wrong_response.status_code == 401:
                print_test_result("Validação de senha incorreta", True, "Rejeitou senha incorreta")
            else:
                print_test_result("Validação de senha incorreta", False, "Não rejeitou senha incorreta")
            
            return True
        else:
            print_test_result("Login de usuário", False, 
                            f"Status: {response.status_code}, Erro: {response.text}")
            return False
            
    except Exception as e:
        print_test_result("Login de usuário", False, f"Exceção: {str(e)}")
        return False

def test_jwt_refresh_token():
    """Test JWT token refresh endpoint"""
    print("\n" + "="*60)
    print("TESTANDO REFRESH DE TOKEN JWT")
    print("="*60)
    
    if not auth_token:
        print_test_result("Refresh de token", False, "Token não disponível")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        response = requests.post(f"{BACKEND_URL}/auth/refresh", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            new_token = data.get("access_token")
            expires_in = data.get("expires_in")
            
            if new_token and expires_in == 30 * 24 * 3600:
                print_test_result("Refresh de token", True, "Novo token gerado com 30 dias de validade")
                return True
            else:
                print_test_result("Refresh de token", False, "Token ou expiração inválidos")
                return False
        else:
            print_test_result("Refresh de token", False, 
                            f"Status: {response.status_code}, Erro: {response.text}")
            return False
        
    except Exception as e:
        print_test_result("Refresh de token", False, f"Exceção: {str(e)}")
        return False

def test_jwt_authentication():
    """Test JWT token validation"""
    print("\n" + "="*60)
    print("TESTANDO AUTENTICAÇÃO JWT")
    print("="*60)
    
    if not auth_token:
        print_test_result("Autenticação JWT", False, "Token não disponível")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        # Test with valid token
        response = requests.get(f"{BACKEND_URL}/accounts", headers=headers)
        
        if response.status_code in [200, 404]:  # 404 is ok if no accounts exist yet
            print_test_result("Token JWT válido", True, "Token aceito pelo servidor")
        else:
            print_test_result("Token JWT válido", False, 
                            f"Token rejeitado: {response.status_code}")
            return False
        
        # Test with invalid token
        invalid_headers = {"Authorization": "Bearer token_invalido"}
        invalid_response = requests.get(f"{BACKEND_URL}/accounts", headers=invalid_headers)
        
        if invalid_response.status_code == 401:
            print_test_result("Rejeição de token inválido", True, "Token inválido rejeitado")
        else:
            print_test_result("Rejeição de token inválido", False, "Token inválido aceito")
        
        return True
        
    except Exception as e:
        print_test_result("Autenticação JWT", False, f"Exceção: {str(e)}")
        return False

def test_comprehensive_categories():
    """Test comprehensive Brazilian categories system"""
    global category_id, expense_category_id
    
    print("\n" + "="*60)
    print("TESTANDO SISTEMA ABRANGENTE DE CATEGORIAS BRASILEIRAS")
    print("="*60)
    
    if not auth_token:
        print_test_result("Categorias", False, "Token não disponível")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        response = requests.get(f"{BACKEND_URL}/categories", headers=headers)
        
        if response.status_code == 200:
            categories = response.json()
            
            if len(categories) >= 40:  # Should have 40+ categories
                print_test_result("40+ categorias brasileiras", True, 
                                f"Encontradas {len(categories)} categoria(s)")
            else:
                print_test_result("40+ categorias brasileiras", False, 
                                f"Apenas {len(categories)} categorias encontradas")
            
            # Check for specific Brazilian categories
            category_names = [cat.get("name") for cat in categories]
            expected_categories = [
                "Salário", "Freelance/PJ", "Aluguel", "Condomínio", "IPTU", 
                "Água", "Luz", "Gás", "Internet", "Combustível", "Transporte Público",
                "Uber/99", "Supermercado", "Restaurantes", "Delivery", "Plano de Saúde",
                "Moradia", "Transporte", "Alimentação", "Saúde", "Lazer"
            ]
            
            found_categories = [cat for cat in expected_categories if cat in category_names]
            
            if len(found_categories) >= 15:
                print_test_result("Categorias específicas brasileiras", True, 
                                f"Encontradas {len(found_categories)}/20: {', '.join(found_categories[:10])}...")
            else:
                print_test_result("Categorias específicas brasileiras", False, 
                                f"Poucas categorias específicas: {found_categories}")
            
            # Check parent/child relationships
            parent_categories = [cat for cat in categories if not cat.get("parent_category_id")]
            child_categories = [cat for cat in categories if cat.get("parent_category_id")]
            
            if len(parent_categories) > 0 and len(child_categories) > 0:
                print_test_result("Hierarquia de categorias (pai/filho)", True, 
                                f"Pais: {len(parent_categories)}, Filhos: {len(child_categories)}")
            else:
                print_test_result("Hierarquia de categorias (pai/filho)", False, 
                                "Hierarquia não encontrada")
            
            # Get category IDs for testing
            salary_category = next((cat for cat in categories if cat.get("name") == "Salário"), None)
            if salary_category:
                category_id = salary_category.get("id")
            
            alimentacao_category = next((cat for cat in categories if cat.get("name") == "Alimentação"), None)
            if alimentacao_category:
                expense_category_id = alimentacao_category.get("id")
            
            # Check income and expense categories
            income_cats = [cat for cat in categories if cat.get("type") == "Receita"]
            expense_cats = [cat for cat in categories if cat.get("type") == "Despesa"]
            
            if len(income_cats) >= 5 and len(expense_cats) >= 30:
                print_test_result("Distribuição receitas/despesas", True, 
                                f"Receitas: {len(income_cats)}, Despesas: {len(expense_cats)}")
            else:
                print_test_result("Distribuição receitas/despesas", False, 
                                f"Distribuição inadequada - Receitas: {len(income_cats)}, Despesas: {len(expense_cats)}")
            
            return True
        else:
            print_test_result("Listagem de categorias", False, 
                            f"Status: {response.status_code}, Erro: {response.text}")
            return False
        
    except Exception as e:
        print_test_result("Categorias", False, f"Exceção: {str(e)}")
        return False

def test_advanced_account_management():
    """Test advanced account management with credit card support"""
    global account_id, credit_card_account_id
    
    print("\n" + "="*60)
    print("TESTANDO GESTÃO AVANÇADA DE CONTAS COM CARTÃO DE CRÉDITO")
    print("="*60)
    
    if not auth_token:
        print_test_result("Gestão avançada de contas", False, "Token não disponível")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        # Test regular account creation
        account_data = {
            "name": "Conta Corrente Banco do Brasil",
            "type": "Conta Corrente",
            "institution": "Banco do Brasil",
            "initial_balance": 2500.75,
            "color_hex": "#00A859"
        }
        
        response = requests.post(f"{BACKEND_URL}/accounts", json=account_data, headers=headers)
        
        if response.status_code == 200:
            account = response.json()
            account_id = account.get("id")
            print_test_result("Criação de conta corrente", True, 
                            f"Conta: {account.get('name')}, Saldo: R$ {account.get('current_balance')}")
        else:
            print_test_result("Criação de conta corrente", False, 
                            f"Status: {response.status_code}, Erro: {response.text}")
            return False
        
        # Test credit card account creation
        credit_card_data = {
            "name": "Cartão de Crédito Nubank",
            "type": "Cartão de Crédito",
            "institution": "Nubank",
            "initial_balance": 0.0,
            "credit_limit": 5000.0,
            "invoice_due_date": "15",
            "color_hex": "#8A05BE"
        }
        
        cc_response = requests.post(f"{BACKEND_URL}/accounts", json=credit_card_data, headers=headers)
        
        if cc_response.status_code == 200:
            cc_account = cc_response.json()
            credit_card_account_id = cc_account.get("id")
            print_test_result("Criação de cartão de crédito", True, 
                            f"Cartão: {cc_account.get('name')}, Limite: R$ {cc_account.get('credit_limit')}")
            
            # Verify credit card specific fields
            if cc_account.get("credit_limit") == 5000.0 and cc_account.get("invoice_due_date") == "15":
                print_test_result("Campos específicos do cartão", True, "Limite e vencimento configurados")
            else:
                print_test_result("Campos específicos do cartão", False, "Campos não configurados corretamente")
        else:
            print_test_result("Criação de cartão de crédito", False, 
                            f"Status: {cc_response.status_code}")
            return False
        
        # Test account listing and CRUD operations
        list_response = requests.get(f"{BACKEND_URL}/accounts", headers=headers)
        
        if list_response.status_code == 200:
            accounts = list_response.json()
            if len(accounts) >= 2:
                print_test_result("Listagem de contas múltiplas", True, 
                                f"Encontradas {len(accounts)} conta(s)")
                
                # Test account update
                update_data = account_data.copy()
                update_data["name"] = "Conta Corrente BB - Atualizada"
                update_data["initial_balance"] = 3000.0
                
                update_response = requests.put(f"{BACKEND_URL}/accounts/{account_id}", 
                                             json=update_data, headers=headers)
                
                if update_response.status_code == 200:
                    print_test_result("Atualização de conta", True, "Conta atualizada com sucesso")
                else:
                    print_test_result("Atualização de conta", False, 
                                    f"Status: {update_response.status_code}")
            else:
                print_test_result("Listagem de contas múltiplas", False, 
                                f"Poucas contas: {len(accounts)}")
        
        return True
        
    except Exception as e:
        print_test_result("Gestão avançada de contas", False, f"Exceção: {str(e)}")
        return False

def test_advanced_transaction_management():
    """Test advanced transaction management with recurrence"""
    global transaction_id
    
    print("\n" + "="*60)
    print("TESTANDO GESTÃO AVANÇADA DE TRANSAÇÕES COM RECORRÊNCIA")
    print("="*60)
    
    if not auth_token or not account_id:
        print_test_result("Transações avançadas", False, "Token ou conta não disponível")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        # Test recurring transaction
        recurring_transaction = {
            "description": "Salário Mensal Recorrente",
            "value": 4500.00,
            "type": "Receita",
            "transaction_date": datetime.now().isoformat(),
            "account_id": account_id,
            "category_id": category_id,
            "observation": "Salário com recorrência mensal",
            "is_recurring": True,
            "recurrence_interval": "Mensal",
            "recurrence_start_date": datetime.now().isoformat(),
            "recurrence_end_date": (datetime.now() + timedelta(days=365)).isoformat(),
            "status": "Pago"
        }
        
        response = requests.post(f"{BACKEND_URL}/transactions", json=recurring_transaction, headers=headers)
        
        if response.status_code == 200:
            transaction = response.json()
            transaction_id = transaction.get("id")
            print_test_result("Transação recorrente", True, 
                            f"Transação: {transaction.get('description')}, Recorrência: {transaction.get('recurrence_interval')}")
            
            # Verify recurrence fields
            if (transaction.get("is_recurring") and 
                transaction.get("recurrence_interval") == "Mensal"):
                print_test_result("Campos de recorrência", True, "Recorrência configurada corretamente")
            else:
                print_test_result("Campos de recorrência", False, "Recorrência não configurada")
        else:
            print_test_result("Transação recorrente", False, 
                            f"Status: {response.status_code}, Erro: {response.text}")
            return False
        
        # Test pending transaction
        pending_transaction = {
            "description": "Conta de Luz - Fevereiro",
            "value": 180.50,
            "type": "Despesa",
            "transaction_date": (datetime.now() + timedelta(days=5)).isoformat(),
            "account_id": account_id,
            "category_id": expense_category_id,
            "status": "Pendente"
        }
        
        pending_response = requests.post(f"{BACKEND_URL}/transactions", json=pending_transaction, headers=headers)
        
        if pending_response.status_code == 200:
            pending_trans = pending_response.json()
            print_test_result("Transação pendente", True, 
                            f"Transação: {pending_trans.get('description')}, Status: {pending_trans.get('status')}")
        else:
            print_test_result("Transação pendente", False, 
                            f"Status: {pending_response.status_code}")
        
        # Test transaction update
        if transaction_id:
            update_data = recurring_transaction.copy()
            update_data["description"] = "Salário Mensal Recorrente - Atualizado"
            update_data["value"] = 4800.00
            
            update_response = requests.put(f"{BACKEND_URL}/transactions/{transaction_id}", 
                                         json=update_data, headers=headers)
            
            if update_response.status_code == 200:
                print_test_result("Atualização de transação", True, "Transação atualizada com sucesso")
            else:
                print_test_result("Atualização de transação", False, 
                                f"Status: {update_response.status_code}")
        
        return True
        
    except Exception as e:
        print_test_result("Transações avançadas", False, f"Exceção: {str(e)}")
        return False

def test_transfer_system():
    """Test transfer between accounts system"""
    print("\n" + "="*60)
    print("TESTANDO SISTEMA DE TRANSFERÊNCIAS ENTRE CONTAS")
    print("="*60)
    
    if not auth_token or not account_id or not credit_card_account_id:
        print_test_result("Sistema de transferências", False, "Contas não disponíveis")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        # Get initial balances
        accounts_response = requests.get(f"{BACKEND_URL}/accounts", headers=headers)
        if accounts_response.status_code != 200:
            print_test_result("Sistema de transferências", False, "Não foi possível obter saldos")
            return False
        
        accounts = accounts_response.json()
        from_account = next((acc for acc in accounts if acc.get("id") == account_id), None)
        to_account = next((acc for acc in accounts if acc.get("id") == credit_card_account_id), None)
        
        if not from_account or not to_account:
            print_test_result("Sistema de transferências", False, "Contas não encontradas")
            return False
        
        initial_from_balance = from_account.get("current_balance")
        initial_to_balance = to_account.get("current_balance")
        
        # Test transfer
        transfer_data = {
            "from_account_id": account_id,
            "to_account_id": credit_card_account_id,
            "value": 500.00,
            "description": "Pagamento de fatura do cartão",
            "transaction_date": datetime.now().isoformat()
        }
        
        response = requests.post(f"{BACKEND_URL}/transfers", json=transfer_data, headers=headers)
        
        if response.status_code == 200:
            print_test_result("Criação de transferência", True, 
                            f"Transferência de R$ {transfer_data['value']} realizada")
            
            # Verify balance updates
            updated_accounts_response = requests.get(f"{BACKEND_URL}/accounts", headers=headers)
            if updated_accounts_response.status_code == 200:
                updated_accounts = updated_accounts_response.json()
                updated_from = next((acc for acc in updated_accounts if acc.get("id") == account_id), None)
                updated_to = next((acc for acc in updated_accounts if acc.get("id") == credit_card_account_id), None)
                
                if updated_from and updated_to:
                    new_from_balance = updated_from.get("current_balance")
                    new_to_balance = updated_to.get("current_balance")
                    
                    expected_from = initial_from_balance - transfer_data["value"]
                    expected_to = initial_to_balance + transfer_data["value"]
                    
                    if (abs(new_from_balance - expected_from) < 0.01 and 
                        abs(new_to_balance - expected_to) < 0.01):
                        print_test_result("Atualização de saldos na transferência", True, 
                                        f"Origem: R$ {initial_from_balance} → R$ {new_from_balance}, "
                                        f"Destino: R$ {initial_to_balance} → R$ {new_to_balance}")
                    else:
                        print_test_result("Atualização de saldos na transferência", False, 
                                        f"Saldos incorretos")
            
            # Verify linked transactions were created
            transactions_response = requests.get(f"{BACKEND_URL}/transactions", headers=headers)
            if transactions_response.status_code == 200:
                transactions = transactions_response.json()
                transfer_transactions = [t for t in transactions if "Transferência" in t.get("description", "")]
                
                if len(transfer_transactions) >= 2:
                    print_test_result("Transações vinculadas da transferência", True, 
                                    f"Criadas {len(transfer_transactions)} transações vinculadas")
                else:
                    print_test_result("Transações vinculadas da transferência", False, 
                                    "Transações vinculadas não criadas")
        else:
            print_test_result("Criação de transferência", False, 
                            f"Status: {response.status_code}, Erro: {response.text}")
            return False
        
        return True
        
    except Exception as e:
        print_test_result("Sistema de transferências", False, f"Exceção: {str(e)}")
        return False

def test_budget_management():
    """Test budget management system"""
    global budget_id
    
    print("\n" + "="*60)
    print("TESTANDO SISTEMA DE GESTÃO DE ORÇAMENTOS")
    print("="*60)
    
    if not auth_token or not expense_category_id:
        print_test_result("Sistema de orçamentos", False, "Token ou categoria não disponível")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        # Create budget
        current_month = datetime.now().strftime("%Y-%m")
        budget_data = {
            "category_id": expense_category_id,
            "budget_amount": 800.00,
            "month_year": current_month
        }
        
        response = requests.post(f"{BACKEND_URL}/budgets", json=budget_data, headers=headers)
        
        if response.status_code == 200:
            budget = response.json()
            budget_id = budget.get("id")
            print_test_result("Criação de orçamento", True, 
                            f"Orçamento: R$ {budget.get('budget_amount')} para {current_month}")
            
            # Verify budget fields
            if (budget.get("budget_amount") == 800.00 and 
                budget.get("month_year") == current_month):
                print_test_result("Campos do orçamento", True, "Orçamento configurado corretamente")
            else:
                print_test_result("Campos do orçamento", False, "Campos incorretos")
        else:
            print_test_result("Criação de orçamento", False, 
                            f"Status: {response.status_code}, Erro: {response.text}")
            return False
        
        # Test budget listing
        list_response = requests.get(f"{BACKEND_URL}/budgets", 
                                   params={"month_year": current_month}, headers=headers)
        
        if list_response.status_code == 200:
            budgets = list_response.json()
            if len(budgets) > 0:
                print_test_result("Listagem de orçamentos", True, 
                                f"Encontrados {len(budgets)} orçamento(s)")
                
                # Check spent amount tracking
                first_budget = budgets[0]
                if "spent_amount" in first_budget:
                    print_test_result("Rastreamento de gastos", True, 
                                    f"Gasto atual: R$ {first_budget.get('spent_amount')}")
                else:
                    print_test_result("Rastreamento de gastos", False, "Campo spent_amount ausente")
            else:
                print_test_result("Listagem de orçamentos", False, "Nenhum orçamento encontrado")
        else:
            print_test_result("Listagem de orçamentos", False, 
                            f"Status: {list_response.status_code}")
        
        return True
        
    except Exception as e:
        print_test_result("Sistema de orçamentos", False, f"Exceção: {str(e)}")
        return False

def test_file_upload_system():
    """Test file upload system for proofs"""
    print("\n" + "="*60)
    print("TESTANDO SISTEMA DE UPLOAD DE ARQUIVOS")
    print("="*60)
    
    if not auth_token:
        print_test_result("Sistema de upload", False, "Token não disponível")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        # Create a simple test file (base64 encoded image)
        test_file_content = b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        
        # Prepare multipart form data
        files = {
            'file': ('comprovante.png', base64.b64decode(test_file_content), 'image/png')
        }
        
        response = requests.post(f"{BACKEND_URL}/upload", files=files, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            file_url = data.get("file_url")
            filename = data.get("filename")
            
            if file_url and filename:
                print_test_result("Upload de arquivo", True, 
                                f"Arquivo: {filename}, URL gerada")
                
                # Verify base64 format
                if file_url.startswith("data:image/png;base64,"):
                    print_test_result("Formato base64", True, "Arquivo convertido para base64")
                else:
                    print_test_result("Formato base64", False, "Formato incorreto")
            else:
                print_test_result("Upload de arquivo", False, "URL ou filename não retornados")
                return False
        else:
            print_test_result("Upload de arquivo", False, 
                            f"Status: {response.status_code}, Erro: {response.text}")
            return False
        
        return True
        
    except Exception as e:
        print_test_result("Sistema de upload", False, f"Exceção: {str(e)}")
        return False

def test_enhanced_dashboard():
    """Test enhanced dashboard API with analytics"""
    print("\n" + "="*60)
    print("TESTANDO DASHBOARD APRIMORADO COM ANALYTICS")
    print("="*60)
    
    if not auth_token:
        print_test_result("Dashboard aprimorado", False, "Token não disponível")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        response = requests.get(f"{BACKEND_URL}/dashboard/summary", headers=headers)
        
        if response.status_code == 200:
            summary = response.json()
            
            # Check enhanced fields
            required_fields = [
                "total_balance", "monthly_income", "monthly_expenses", "monthly_net", 
                "accounts", "expense_by_category", "income_by_category", "pending_transactions"
            ]
            missing_fields = [field for field in required_fields if field not in summary]
            
            if not missing_fields:
                print_test_result("Campos aprimorados do dashboard", True, "Todos os campos presentes")
                
                # Check category breakdowns
                expense_by_category = summary.get("expense_by_category", {})
                income_by_category = summary.get("income_by_category", {})
                
                if len(expense_by_category) > 0 or len(income_by_category) > 0:
                    print_test_result("Breakdown por categorias", True, 
                                    f"Despesas: {len(expense_by_category)} cats, Receitas: {len(income_by_category)} cats")
                else:
                    print_test_result("Breakdown por categorias", False, "Nenhum breakdown encontrado")
                
                # Check pending transactions
                pending_transactions = summary.get("pending_transactions", [])
                print_test_result("Transações pendentes (próximos 15 dias)", True, 
                                f"Encontradas {len(pending_transactions)} transação(ões) pendente(s)")
                
                # Check account summaries with enhanced fields
                accounts = summary.get("accounts", [])
                if len(accounts) > 0:
                    first_account = accounts[0]
                    account_fields = ["id", "name", "balance", "color", "type"]
                    missing_account_fields = [field for field in account_fields if field not in first_account]
                    
                    if not missing_account_fields:
                        print_test_result("Resumo aprimorado de contas", True, "Todos os campos das contas presentes")
                    else:
                        print_test_result("Resumo aprimorado de contas", False, 
                                        f"Campos faltando: {missing_account_fields}")
                
                print(f"   📊 Saldo Total: R$ {summary.get('total_balance')}")
                print(f"   📈 Receitas do Mês: R$ {summary.get('monthly_income')}")
                print(f"   📉 Despesas do Mês: R$ {summary.get('monthly_expenses')}")
                print(f"   💰 Saldo Líquido: R$ {summary.get('monthly_net')}")
                print(f"   🏦 Contas: {len(accounts)}")
                print(f"   📋 Pendentes: {len(pending_transactions)}")
                
            else:
                print_test_result("Campos aprimorados do dashboard", False, 
                                f"Campos faltando: {missing_fields}")
                return False
        else:
            print_test_result("Dashboard aprimorado", False, 
                            f"Status: {response.status_code}, Erro: {response.text}")
            return False
        
        return True
        
    except Exception as e:
        print_test_result("Dashboard aprimorado", False, f"Exceção: {str(e)}")
        return False

def test_reports_analytics():
    """Test advanced reports and analytics API"""
    print("\n" + "="*60)
    print("TESTANDO RELATÓRIOS E ANALYTICS AVANÇADOS")
    print("="*60)
    
    if not auth_token:
        print_test_result("Relatórios avançados", False, "Token não disponível")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        # Test cash flow report
        start_date = (datetime.now() - timedelta(days=30)).isoformat()
        end_date = datetime.now().isoformat()
        
        params = {
            "start_date": start_date,
            "end_date": end_date
        }
        
        response = requests.get(f"{BACKEND_URL}/reports/cash-flow", params=params, headers=headers)
        
        if response.status_code == 200:
            report = response.json()
            
            # Check report structure
            if "monthly_data" in report and "transactions" in report:
                print_test_result("Estrutura do relatório de fluxo de caixa", True, "Campos presentes")
                
                monthly_data = report.get("monthly_data", {})
                transactions = report.get("transactions", [])
                
                print_test_result("Dados mensais agregados", True, 
                                f"Encontrados {len(monthly_data)} mês(es) de dados")
                
                print_test_result("Transações do período", True, 
                                f"Encontradas {len(transactions)} transação(ões)")
                
                # Verify monthly data structure
                if monthly_data:
                    first_month = list(monthly_data.values())[0]
                    required_month_fields = ["income", "expenses", "net"]
                    
                    if all(field in first_month for field in required_month_fields):
                        print_test_result("Estrutura dos dados mensais", True, 
                                        "Campos income, expenses, net presentes")
                    else:
                        print_test_result("Estrutura dos dados mensais", False, 
                                        "Campos mensais incompletos")
                
                print(f"   📅 Período: {len(monthly_data)} mês(es)")
                print(f"   📊 Transações: {len(transactions)}")
                
            else:
                print_test_result("Estrutura do relatório de fluxo de caixa", False, 
                                "Campos monthly_data ou transactions ausentes")
                return False
        else:
            print_test_result("Relatório de fluxo de caixa", False, 
                            f"Status: {response.status_code}, Erro: {response.text}")
            return False
        
        return True
        
    except Exception as e:
        print_test_result("Relatórios avançados", False, f"Exceção: {str(e)}")
        return False

def run_all_enhanced_tests():
    """Run all enhanced backend tests in sequence"""
    print("🇧🇷 INICIANDO TESTES COMPLETOS DO BACKEND ORÇAZENFINANCEIRO")
    print("=" * 80)
    print(f"URL do Backend: {BACKEND_URL}")
    print("=" * 80)
    
    test_results = {}
    
    # Enhanced test sequence
    test_results["registration"] = test_user_registration()
    test_results["login"] = test_user_login()
    test_results["jwt_refresh"] = test_jwt_refresh_token()
    test_results["jwt_auth"] = test_jwt_authentication()
    test_results["comprehensive_categories"] = test_comprehensive_categories()
    test_results["advanced_accounts"] = test_advanced_account_management()
    test_results["advanced_transactions"] = test_advanced_transaction_management()
    test_results["transfer_system"] = test_transfer_system()
    test_results["budget_management"] = test_budget_management()
    test_results["file_upload"] = test_file_upload_system()
    test_results["enhanced_dashboard"] = test_enhanced_dashboard()
    test_results["reports_analytics"] = test_reports_analytics()
    
    # Summary
    print("\n" + "="*80)
    print("RESUMO COMPLETO DOS TESTES")
    print("="*80)
    
    passed_tests = sum(1 for result in test_results.values() if result)
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{status} - {test_name.replace('_', ' ').title()}")
    
    print(f"\nResultado Final: {passed_tests}/{total_tests} testes passaram")
    
    if passed_tests == total_tests:
        print("🎉 TODOS OS TESTES PASSARAM! Backend OrçaZenFinanceiro funcionando perfeitamente.")
        print("✨ Sistema completo com todas as funcionalidades avançadas testadas e aprovadas!")
    else:
        print("⚠️  ALGUNS TESTES FALHARAM. Verifique os detalhes acima.")
    
    return test_results

if __name__ == "__main__":
    run_all_enhanced_tests()