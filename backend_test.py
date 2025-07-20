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
    "name": "Teste Debug User",
    "email": "teste.debug@email.com",
    "password": "MinhaSenh@123",
    "confirm_password": "MinhaSenh@123"
}

TEST_USER_LOGIN = {
    "email": "teste.debug@email.com", 
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
goal_id = None
goal_contribution_id = None

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

def test_account_management():
    """Test account creation and listing"""
    global account_id
    
    print("\n" + "="*60)
    print("TESTANDO GESTÃO DE CONTAS")
    print("="*60)
    
    if not auth_token:
        print_test_result("Gestão de contas", False, "Token não disponível")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Test account creation
    account_data = {
        "name": "Conta Corrente Banco do Brasil",
        "type": "Conta Corrente",
        "institution": "Banco do Brasil",
        "initial_balance": 1500.50,
        "color_hex": "#00A859"
    }
    
    try:
        # Create account
        response = requests.post(f"{BACKEND_URL}/accounts", json=account_data, headers=headers)
        
        if response.status_code == 200:
            account = response.json()
            account_id = account.get("id")
            
            print_test_result("Criação de conta", True, 
                            f"Conta criada: {account.get('name')}, Saldo: R$ {account.get('current_balance')}")
            
            # Verify initial balance equals current balance
            if account.get("initial_balance") == account.get("current_balance"):
                print_test_result("Saldo inicial da conta", True, "Saldo inicial = saldo atual")
            else:
                print_test_result("Saldo inicial da conta", False, "Saldos não coincidem")
        else:
            print_test_result("Criação de conta", False, 
                            f"Status: {response.status_code}, Erro: {response.text}")
            return False
        
        # Test account listing
        list_response = requests.get(f"{BACKEND_URL}/accounts", headers=headers)
        
        if list_response.status_code == 200:
            accounts = list_response.json()
            if len(accounts) > 0:
                print_test_result("Listagem de contas", True, 
                                f"Encontradas {len(accounts)} conta(s)")
                
                # Verify our created account is in the list
                found_account = any(acc.get("id") == account_id for acc in accounts)
                if found_account:
                    print_test_result("Conta criada na listagem", True, "Conta encontrada na lista")
                else:
                    print_test_result("Conta criada na listagem", False, "Conta não encontrada na lista")
            else:
                print_test_result("Listagem de contas", False, "Nenhuma conta encontrada")
        else:
            print_test_result("Listagem de contas", False, 
                            f"Status: {list_response.status_code}")
        
        return True
        
    except Exception as e:
        print_test_result("Gestão de contas", False, f"Exceção: {str(e)}")
        return False

def test_categories():
    """Test categories listing and default category creation"""
    global category_id
    
    print("\n" + "="*60)
    print("TESTANDO CATEGORIAS")
    print("="*60)
    
    if not auth_token:
        print_test_result("Categorias", False, "Token não disponível")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        response = requests.get(f"{BACKEND_URL}/categories", headers=headers)
        
        if response.status_code == 200:
            categories = response.json()
            
            if len(categories) > 0:
                print_test_result("Listagem de categorias", True, 
                                f"Encontradas {len(categories)} categoria(s)")
                
                # Check for Brazilian default categories
                category_names = [cat.get("name") for cat in categories]
                expected_categories = ["Salário", "Alimentação", "Transporte", "Moradia"]
                
                found_categories = [cat for cat in expected_categories if cat in category_names]
                
                if len(found_categories) >= 3:
                    print_test_result("Categorias padrão brasileiras", True, 
                                    f"Encontradas: {', '.join(found_categories)}")
                    
                    # Get a category ID for transaction testing
                    salary_category = next((cat for cat in categories if cat.get("name") == "Salário"), None)
                    if salary_category:
                        category_id = salary_category.get("id")
                else:
                    print_test_result("Categorias padrão brasileiras", False, 
                                    f"Poucas categorias encontradas: {found_categories}")
                
                # Check for income and expense categories
                income_cats = [cat for cat in categories if cat.get("type") == "Receita"]
                expense_cats = [cat for cat in categories if cat.get("type") == "Despesa"]
                
                if len(income_cats) > 0 and len(expense_cats) > 0:
                    print_test_result("Categorias de receita e despesa", True, 
                                    f"Receitas: {len(income_cats)}, Despesas: {len(expense_cats)}")
                else:
                    print_test_result("Categorias de receita e despesa", False, 
                                    "Tipos de categoria insuficientes")
            else:
                print_test_result("Listagem de categorias", False, "Nenhuma categoria encontrada")
                return False
        else:
            print_test_result("Listagem de categorias", False, 
                            f"Status: {response.status_code}, Erro: {response.text}")
            return False
        
        return True
        
    except Exception as e:
        print_test_result("Categorias", False, f"Exceção: {str(e)}")
        return False

def test_transaction_management():
    """Test transaction creation and automatic balance updates"""
    print("\n" + "="*60)
    print("TESTANDO GESTÃO DE TRANSAÇÕES")
    print("="*60)
    
    if not auth_token or not account_id:
        print_test_result("Gestão de transações", False, "Token ou conta não disponível")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Get initial account balance
    accounts_response = requests.get(f"{BACKEND_URL}/accounts", headers=headers)
    if accounts_response.status_code != 200:
        print_test_result("Gestão de transações", False, "Não foi possível obter saldo inicial")
        return False
    
    accounts = accounts_response.json()
    initial_account = next((acc for acc in accounts if acc.get("id") == account_id), None)
    if not initial_account:
        print_test_result("Gestão de transações", False, "Conta não encontrada")
        return False
    
    initial_balance = initial_account.get("current_balance")
    print(f"   Saldo inicial da conta: R$ {initial_balance}")
    
    # Test income transaction
    income_transaction = {
        "description": "Salário Janeiro 2025",
        "value": 3500.00,
        "type": "Receita",
        "transaction_date": datetime.now().isoformat(),
        "account_id": account_id,
        "category_id": category_id,
        "observation": "Pagamento mensal"
    }
    
    try:
        # Create income transaction
        response = requests.post(f"{BACKEND_URL}/transactions", json=income_transaction, headers=headers)
        
        if response.status_code == 200:
            transaction = response.json()
            print_test_result("Criação de transação (receita)", True, 
                            f"Transação: {transaction.get('description')}, Valor: R$ {transaction.get('value')}")
            
            # Check balance update
            updated_accounts_response = requests.get(f"{BACKEND_URL}/accounts", headers=headers)
            if updated_accounts_response.status_code == 200:
                updated_accounts = updated_accounts_response.json()
                updated_account = next((acc for acc in updated_accounts if acc.get("id") == account_id), None)
                
                if updated_account:
                    new_balance = updated_account.get("current_balance")
                    expected_balance = initial_balance + income_transaction["value"]
                    
                    if abs(new_balance - expected_balance) < 0.01:  # Allow for floating point precision
                        print_test_result("Atualização automática de saldo (receita)", True, 
                                        f"Saldo atualizado: R$ {initial_balance} → R$ {new_balance}")
                    else:
                        print_test_result("Atualização automática de saldo (receita)", False, 
                                        f"Esperado: R$ {expected_balance}, Atual: R$ {new_balance}")
                else:
                    print_test_result("Atualização automática de saldo (receita)", False, "Conta não encontrada")
        else:
            print_test_result("Criação de transação (receita)", False, 
                            f"Status: {response.status_code}, Erro: {response.text}")
            return False
        
        # Test expense transaction
        expense_transaction = {
            "description": "Supermercado Extra",
            "value": 250.75,
            "type": "Despesa", 
            "transaction_date": datetime.now().isoformat(),
            "account_id": account_id,
            "observation": "Compras mensais"
        }
        
        # Get current balance before expense
        current_accounts_response = requests.get(f"{BACKEND_URL}/accounts", headers=headers)
        current_accounts = current_accounts_response.json()
        current_account = next((acc for acc in current_accounts if acc.get("id") == account_id), None)
        balance_before_expense = current_account.get("current_balance")
        
        # Create expense transaction
        expense_response = requests.post(f"{BACKEND_URL}/transactions", json=expense_transaction, headers=headers)
        
        if expense_response.status_code == 200:
            expense_trans = expense_response.json()
            print_test_result("Criação de transação (despesa)", True, 
                            f"Transação: {expense_trans.get('description')}, Valor: R$ {expense_trans.get('value')}")
            
            # Check balance update for expense
            final_accounts_response = requests.get(f"{BACKEND_URL}/accounts", headers=headers)
            if final_accounts_response.status_code == 200:
                final_accounts = final_accounts_response.json()
                final_account = next((acc for acc in final_accounts if acc.get("id") == account_id), None)
                
                if final_account:
                    final_balance = final_account.get("current_balance")
                    expected_final_balance = balance_before_expense - expense_transaction["value"]
                    
                    if abs(final_balance - expected_final_balance) < 0.01:
                        print_test_result("Atualização automática de saldo (despesa)", True, 
                                        f"Saldo atualizado: R$ {balance_before_expense} → R$ {final_balance}")
                    else:
                        print_test_result("Atualização automática de saldo (despesa)", False, 
                                        f"Esperado: R$ {expected_final_balance}, Atual: R$ {final_balance}")
        else:
            print_test_result("Criação de transação (despesa)", False, 
                            f"Status: {expense_response.status_code}")
        
        # Test transaction listing
        transactions_response = requests.get(f"{BACKEND_URL}/transactions", headers=headers)
        
        if transactions_response.status_code == 200:
            transactions = transactions_response.json()
            if len(transactions) >= 2:
                print_test_result("Listagem de transações", True, 
                                f"Encontradas {len(transactions)} transação(ões)")
                
                # Check if transactions are sorted by date (most recent first)
                if len(transactions) >= 2:
                    first_date = datetime.fromisoformat(transactions[0].get("transaction_date").replace('Z', '+00:00'))
                    second_date = datetime.fromisoformat(transactions[1].get("transaction_date").replace('Z', '+00:00'))
                    
                    if first_date >= second_date:
                        print_test_result("Ordenação de transações por data", True, "Transações ordenadas corretamente")
                    else:
                        print_test_result("Ordenação de transações por data", False, "Transações não ordenadas")
            else:
                print_test_result("Listagem de transações", False, f"Poucas transações: {len(transactions)}")
        else:
            print_test_result("Listagem de transações", False, 
                            f"Status: {transactions_response.status_code}")
        
        return True
        
    except Exception as e:
        print_test_result("Gestão de transações", False, f"Exceção: {str(e)}")
        return False

def test_dashboard_summary():
    """Test dashboard summary calculations"""
    print("\n" + "="*60)
    print("TESTANDO DASHBOARD E RESUMOS")
    print("="*60)
    
    if not auth_token:
        print_test_result("Dashboard", False, "Token não disponível")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        response = requests.get(f"{BACKEND_URL}/dashboard/summary", headers=headers)
        
        if response.status_code == 200:
            summary = response.json()
            
            print_test_result("Endpoint de resumo do dashboard", True, "Endpoint respondeu com sucesso")
            
            # Check required fields
            required_fields = ["total_balance", "monthly_income", "monthly_expenses", "monthly_net", "accounts"]
            missing_fields = [field for field in required_fields if field not in summary]
            
            if not missing_fields:
                print_test_result("Campos obrigatórios do resumo", True, "Todos os campos presentes")
                
                # Validate data types and values
                total_balance = summary.get("total_balance")
                monthly_income = summary.get("monthly_income")
                monthly_expenses = summary.get("monthly_expenses")
                monthly_net = summary.get("monthly_net")
                accounts = summary.get("accounts", [])
                
                print(f"   Saldo Total: R$ {total_balance}")
                print(f"   Receitas do Mês: R$ {monthly_income}")
                print(f"   Despesas do Mês: R$ {monthly_expenses}")
                print(f"   Saldo Líquido do Mês: R$ {monthly_net}")
                print(f"   Número de Contas: {len(accounts)}")
                
                # Verify monthly net calculation
                expected_net = monthly_income - monthly_expenses
                if abs(monthly_net - expected_net) < 0.01:
                    print_test_result("Cálculo do saldo líquido mensal", True, 
                                    f"Cálculo correto: R$ {monthly_income} - R$ {monthly_expenses} = R$ {monthly_net}")
                else:
                    print_test_result("Cálculo do saldo líquido mensal", False, 
                                    f"Esperado: R$ {expected_net}, Atual: R$ {monthly_net}")
                
                # Check accounts summary
                if len(accounts) > 0:
                    print_test_result("Resumo de contas", True, f"Contas incluídas no resumo: {len(accounts)}")
                    
                    # Verify account fields
                    first_account = accounts[0]
                    account_fields = ["id", "name", "balance", "color"]
                    missing_account_fields = [field for field in account_fields if field not in first_account]
                    
                    if not missing_account_fields:
                        print_test_result("Campos das contas no resumo", True, "Todos os campos das contas presentes")
                    else:
                        print_test_result("Campos das contas no resumo", False, 
                                        f"Campos faltando: {missing_account_fields}")
                else:
                    print_test_result("Resumo de contas", False, "Nenhuma conta no resumo")
                
                # Verify total balance calculation
                if len(accounts) > 0:
                    calculated_total = sum(acc.get("balance", 0) for acc in accounts)
                    if abs(total_balance - calculated_total) < 0.01:
                        print_test_result("Cálculo do saldo total", True, 
                                        f"Saldo total correto: R$ {total_balance}")
                    else:
                        print_test_result("Cálculo do saldo total", False, 
                                        f"Esperado: R$ {calculated_total}, Atual: R$ {total_balance}")
                
            else:
                print_test_result("Campos obrigatórios do resumo", False, 
                                f"Campos faltando: {missing_fields}")
                return False
        else:
            print_test_result("Endpoint de resumo do dashboard", False, 
                            f"Status: {response.status_code}, Erro: {response.text}")
            return False
        
        return True
        
    except Exception as e:
        print_test_result("Dashboard", False, f"Exceção: {str(e)}")
        return False

def test_goals_system():
    """Test comprehensive Goals System APIs"""
    global goal_id
    
    print("\n" + "="*60)
    print("TESTANDO SISTEMA DE METAS FINANCEIRAS")
    print("="*60)
    
    if not auth_token:
        print_test_result("Sistema de Metas", False, "Token não disponível")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        # Test 1: Create a financial goal with all required fields
        goal_data = {
            "name": "Casa Própria",
            "description": "Economizar para entrada do apartamento",
            "target_amount": 50000.00,
            "current_amount": 0,
            "target_date": (datetime.now() + timedelta(days=365*2)).isoformat(),  # 2 years from now
            "category": "Casa Própria",
            "priority": "Alta",
            "auto_contribution": 1500.00
        }
        
        response = requests.post(f"{BACKEND_URL}/goals", json=goal_data, headers=headers)
        
        if response.status_code == 200:
            goal = response.json()
            goal_id = goal.get("id")
            
            print_test_result("Criação de meta financeira", True, 
                            f"Meta criada: {goal.get('name')}, Valor alvo: R$ {goal.get('target_amount')}")
            
            # Verify all fields are correctly stored
            expected_fields = ["id", "user_id", "name", "description", "target_amount", 
                             "current_amount", "target_date", "category", "priority", 
                             "auto_contribution", "is_active", "is_achieved", "created_at"]
            missing_fields = [field for field in expected_fields if field not in goal]
            
            if not missing_fields:
                print_test_result("Campos da meta", True, "Todos os campos obrigatórios presentes")
            else:
                print_test_result("Campos da meta", False, f"Campos faltando: {missing_fields}")
            
            # Verify default values
            if goal.get("is_active") == True and goal.get("is_achieved") == False:
                print_test_result("Valores padrão da meta", True, "is_active=True, is_achieved=False")
            else:
                print_test_result("Valores padrão da meta", False, "Valores padrão incorretos")
                
        else:
            print_test_result("Criação de meta financeira", False, 
                            f"Status: {response.status_code}, Erro: {response.text}")
            return False
        
        # Test 2: Create goal with different categories and priorities
        categories_to_test = ["Emergência", "Viagem", "Aposentadoria", "Outros"]
        priorities_to_test = ["Média", "Baixa"]
        
        for i, (cat, priority) in enumerate(zip(categories_to_test, priorities_to_test)):
            test_goal = {
                "name": f"Meta {cat}",
                "target_amount": 10000.00 + (i * 5000),
                "target_date": (datetime.now() + timedelta(days=365)).isoformat(),
                "category": cat,
                "priority": priority
            }
            
            cat_response = requests.post(f"{BACKEND_URL}/goals", json=test_goal, headers=headers)
            if cat_response.status_code == 200:
                print_test_result(f"Meta categoria {cat}", True, f"Categoria {cat} com prioridade {priority}")
            else:
                print_test_result(f"Meta categoria {cat}", False, f"Falha ao criar meta {cat}")
        
        # Test 3: List all user goals and verify proper filtering
        list_response = requests.get(f"{BACKEND_URL}/goals", headers=headers)
        
        if list_response.status_code == 200:
            goals = list_response.json()
            if len(goals) >= 1:
                print_test_result("Listagem de metas", True, 
                                f"Encontradas {len(goals)} meta(s)")
                
                # Verify our created goal is in the list
                found_goal = any(g.get("id") == goal_id for g in goals)
                if found_goal:
                    print_test_result("Meta criada na listagem", True, "Meta encontrada na lista")
                else:
                    print_test_result("Meta criada na listagem", False, "Meta não encontrada na lista")
                
                # Verify only active goals are returned
                active_goals = [g for g in goals if g.get("is_active") == True]
                if len(active_goals) == len(goals):
                    print_test_result("Filtro de metas ativas", True, "Apenas metas ativas retornadas")
                else:
                    print_test_result("Filtro de metas ativas", False, "Metas inativas incluídas")
            else:
                print_test_result("Listagem de metas", False, "Nenhuma meta encontrada")
        else:
            print_test_result("Listagem de metas", False, 
                            f"Status: {list_response.status_code}")
        
        # Test 4: Update existing goal
        if goal_id:
            update_data = {
                "name": "Casa Própria - Atualizada",
                "description": "Meta atualizada com novo valor",
                "target_amount": 60000.00,
                "current_amount": 5000.00,
                "target_date": (datetime.now() + timedelta(days=365*3)).isoformat(),
                "category": "Casa Própria",
                "priority": "Alta",
                "auto_contribution": 2000.00
            }
            
            update_response = requests.put(f"{BACKEND_URL}/goals/{goal_id}", json=update_data, headers=headers)
            
            if update_response.status_code == 200:
                updated_goal = update_response.json()
                print_test_result("Atualização de meta", True, 
                                f"Meta atualizada: {updated_goal.get('name')}")
                
                # Verify changes persisted
                if (updated_goal.get("target_amount") == 60000.00 and 
                    updated_goal.get("current_amount") == 5000.00):
                    print_test_result("Persistência de alterações", True, "Alterações salvas corretamente")
                else:
                    print_test_result("Persistência de alterações", False, "Alterações não persistiram")
            else:
                print_test_result("Atualização de meta", False, 
                                f"Status: {update_response.status_code}")
        
        # Test 5: Add contributions to goal and verify current_amount updates
        if goal_id:
            contribution_amount = 2500.00
            contribute_response = requests.post(f"{BACKEND_URL}/goals/{goal_id}/contribute", 
                                              json={"amount": contribution_amount}, headers=headers)
            
            if contribute_response.status_code == 200:
                contribution_result = contribute_response.json()
                print_test_result("Contribuição para meta", True, 
                                f"Contribuição de R$ {contribution_amount} adicionada")
                
                # Verify goal current_amount was updated
                updated_goal_response = requests.get(f"{BACKEND_URL}/goals", headers=headers)
                if updated_goal_response.status_code == 200:
                    updated_goals = updated_goal_response.json()
                    updated_goal = next((g for g in updated_goals if g.get("id") == goal_id), None)
                    
                    if updated_goal:
                        expected_amount = 5000.00 + contribution_amount  # Previous amount + contribution
                        actual_amount = updated_goal.get("current_amount")
                        
                        if abs(actual_amount - expected_amount) < 0.01:
                            print_test_result("Atualização do valor atual", True, 
                                            f"Valor atualizado: R$ {actual_amount}")
                        else:
                            print_test_result("Atualização do valor atual", False, 
                                            f"Esperado: R$ {expected_amount}, Atual: R$ {actual_amount}")
            else:
                print_test_result("Contribuição para meta", False, 
                                f"Status: {contribute_response.status_code}")
        
        # Test 6: Get goal contribution history
        if goal_id:
            contributions_response = requests.get(f"{BACKEND_URL}/goals/{goal_id}/contributions", headers=headers)
            
            if contributions_response.status_code == 200:
                contributions = contributions_response.json()
                if len(contributions) > 0:
                    print_test_result("Histórico de contribuições", True, 
                                    f"Encontradas {len(contributions)} contribuição(ões)")
                    
                    # Verify contribution fields
                    first_contribution = contributions[0]
                    contribution_fields = ["id", "user_id", "goal_id", "amount", "contribution_date"]
                    missing_contrib_fields = [field for field in contribution_fields if field not in first_contribution]
                    
                    if not missing_contrib_fields:
                        print_test_result("Campos da contribuição", True, "Todos os campos presentes")
                    else:
                        print_test_result("Campos da contribuição", False, 
                                        f"Campos faltando: {missing_contrib_fields}")
                else:
                    print_test_result("Histórico de contribuições", False, "Nenhuma contribuição encontrada")
            else:
                print_test_result("Histórico de contribuições", False, 
                                f"Status: {contributions_response.status_code}")
        
        # Test 7: Check goal achievement logic when current_amount >= target_amount
        if goal_id:
            # Add a large contribution to achieve the goal
            large_contribution = 55000.00  # Should exceed target of 60000 with previous 7500
            achieve_response = requests.post(f"{BACKEND_URL}/goals/{goal_id}/contribute", 
                                           json={"amount": large_contribution}, headers=headers)
            
            if achieve_response.status_code == 200:
                achieve_result = achieve_response.json()
                goal_achieved = achieve_result.get("goal_achieved", False)
                
                if goal_achieved:
                    print_test_result("Lógica de conquista de meta", True, "Meta marcada como conquistada")
                    
                    # Verify goal is marked as achieved
                    achieved_goal_response = requests.get(f"{BACKEND_URL}/goals", headers=headers)
                    if achieved_goal_response.status_code == 200:
                        achieved_goals = achieved_goal_response.json()
                        achieved_goal = next((g for g in achieved_goals if g.get("id") == goal_id), None)
                        
                        if achieved_goal and achieved_goal.get("is_achieved") == True:
                            print_test_result("Status de meta conquistada", True, "is_achieved=True")
                            
                            # Check if achieved_date is set
                            if achieved_goal.get("achieved_date"):
                                print_test_result("Data de conquista", True, "achieved_date definida")
                            else:
                                print_test_result("Data de conquista", False, "achieved_date não definida")
                        else:
                            print_test_result("Status de meta conquistada", False, "is_achieved não atualizado")
                else:
                    print_test_result("Lógica de conquista de meta", False, "Meta não marcada como conquistada")
        
        # Test 8: Test statistics endpoint and verify calculations
        stats_response = requests.get(f"{BACKEND_URL}/goals/statistics", headers=headers)
        
        if stats_response.status_code == 200:
            stats = stats_response.json()
            print_test_result("Endpoint de estatísticas", True, "Endpoint respondeu com sucesso")
            
            # Check required statistics fields
            required_stats_fields = ["total_goals", "achieved_goals", "active_goals", 
                                   "total_target_amount", "total_saved_amount", 
                                   "overall_progress", "category_statistics"]
            missing_stats_fields = [field for field in required_stats_fields if field not in stats]
            
            if not missing_stats_fields:
                print_test_result("Campos das estatísticas", True, "Todos os campos presentes")
                
                # Verify calculations
                total_goals = stats.get("total_goals")
                achieved_goals = stats.get("achieved_goals")
                active_goals = stats.get("active_goals")
                total_target = stats.get("total_target_amount")
                total_saved = stats.get("total_saved_amount")
                overall_progress = stats.get("overall_progress")
                
                print(f"   Total de Metas: {total_goals}")
                print(f"   Metas Conquistadas: {achieved_goals}")
                print(f"   Metas Ativas: {active_goals}")
                print(f"   Valor Total Alvo: R$ {total_target}")
                print(f"   Valor Total Economizado: R$ {total_saved}")
                print(f"   Progresso Geral: {overall_progress:.1f}%")
                
                # Verify active_goals calculation
                if active_goals == (total_goals - achieved_goals):
                    print_test_result("Cálculo de metas ativas", True, "Cálculo correto")
                else:
                    print_test_result("Cálculo de metas ativas", False, "Cálculo incorreto")
                
                # Verify overall progress calculation
                if total_target > 0:
                    expected_progress = (total_saved / total_target) * 100
                    if abs(overall_progress - expected_progress) < 0.1:
                        print_test_result("Cálculo do progresso geral", True, f"Progresso: {overall_progress:.1f}%")
                    else:
                        print_test_result("Cálculo do progresso geral", False, 
                                        f"Esperado: {expected_progress:.1f}%, Atual: {overall_progress:.1f}%")
                
                # Check category statistics
                category_stats = stats.get("category_statistics", {})
                if len(category_stats) > 0:
                    print_test_result("Estatísticas por categoria", True, 
                                    f"Estatísticas para {len(category_stats)} categoria(s)")
                    
                    # Verify category statistics structure
                    first_category = list(category_stats.keys())[0]
                    first_cat_stats = category_stats[first_category]
                    cat_fields = ["count", "target", "saved", "progress"]
                    missing_cat_fields = [field for field in cat_fields if field not in first_cat_stats]
                    
                    if not missing_cat_fields:
                        print_test_result("Campos das estatísticas por categoria", True, "Todos os campos presentes")
                    else:
                        print_test_result("Campos das estatísticas por categoria", False, 
                                        f"Campos faltando: {missing_cat_fields}")
                else:
                    print_test_result("Estatísticas por categoria", False, "Nenhuma estatística por categoria")
            else:
                print_test_result("Campos das estatísticas", False, 
                                f"Campos faltando: {missing_stats_fields}")
        else:
            print_test_result("Endpoint de estatísticas", False, 
                            f"Status: {stats_response.status_code}")
        
        # Test 9: Test soft delete functionality (goal marked inactive)
        if goal_id:
            delete_response = requests.delete(f"{BACKEND_URL}/goals/{goal_id}", headers=headers)
            
            if delete_response.status_code == 200:
                print_test_result("Exclusão de meta (soft delete)", True, "Meta excluída com sucesso")
                
                # Verify goal is no longer in active goals list
                after_delete_response = requests.get(f"{BACKEND_URL}/goals", headers=headers)
                if after_delete_response.status_code == 200:
                    remaining_goals = after_delete_response.json()
                    deleted_goal_found = any(g.get("id") == goal_id for g in remaining_goals)
                    
                    if not deleted_goal_found:
                        print_test_result("Meta removida da listagem", True, "Meta não aparece mais na lista ativa")
                    else:
                        print_test_result("Meta removida da listagem", False, "Meta ainda aparece na lista")
            else:
                print_test_result("Exclusão de meta (soft delete)", False, 
                                f"Status: {delete_response.status_code}")
        
        return True
        
    except Exception as e:
        print_test_result("Sistema de Metas", False, f"Exceção: {str(e)}")
        return False

def test_transaction_balance_logic_fix():
    """
    CRITICAL TEST: Test the corrected Transaction Balance Logic to verify the bug fix.
    
    Test Scenario:
    1. Get user account and note initial balance
    2. Create PENDING transaction (Despesa, R$ 100.00, status: "Pendente") → balance should NOT change
    3. Verify balance remains unchanged 
    4. Confirm the pending transaction → balance should decrease by R$ 100.00
    5. Create PAID transaction (Despesa, R$ 50.00, status: "Pago") → balance should decrease immediately by R$ 50.00
    
    Expected Results:
    - Step 2: Balance unchanged (no double deduction)
    - Step 4: Balance decreases by R$ 100.00 (single deduction on confirmation)  
    - Step 5: Balance decreases immediately by R$ 50.00 (single deduction)
    """
    print("\n" + "="*80)
    print("🔥 TESTE CRÍTICO: LÓGICA DE SALDO DE TRANSAÇÕES CORRIGIDA")
    print("="*80)
    print("Testando correção do bug de dupla dedução em transações pendentes")
    
    if not auth_token or not account_id:
        print_test_result("Teste de Lógica de Saldo", False, "Token ou conta não disponível")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        # Step 1: Get initial account balance
        accounts_response = requests.get(f"{BACKEND_URL}/accounts", headers=headers)
        if accounts_response.status_code != 200:
            print_test_result("Obter saldo inicial", False, "Não foi possível obter saldo inicial")
            return False
        
        accounts = accounts_response.json()
        initial_account = next((acc for acc in accounts if acc.get("id") == account_id), None)
        if not initial_account:
            print_test_result("Obter saldo inicial", False, "Conta não encontrada")
            return False
        
        initial_balance = initial_account.get("current_balance")
        print(f"   ✅ Saldo inicial da conta: R$ {initial_balance:.2f}")
        
        # Step 2: Create PENDING transaction (Despesa, R$ 100.00, status: "Pendente")
        pending_transaction = {
            "description": "Despesa Pendente - Teste Bug Fix",
            "value": 100.00,
            "type": "Despesa",
            "transaction_date": datetime.now().isoformat(),
            "account_id": account_id,
            "status": "Pendente"  # This is the key - PENDING status
        }
        
        pending_response = requests.post(f"{BACKEND_URL}/transactions", json=pending_transaction, headers=headers)
        
        if pending_response.status_code != 200:
            print_test_result("Criar transação pendente", False, 
                            f"Status: {pending_response.status_code}, Erro: {pending_response.text}")
            return False
        
        pending_trans = pending_response.json()
        pending_transaction_id = pending_trans.get("id")
        print_test_result("Criar transação pendente", True, 
                        f"Transação pendente criada: R$ {pending_trans.get('value'):.2f}")
        
        # Step 3: Verify balance remains unchanged after creating pending transaction
        after_pending_response = requests.get(f"{BACKEND_URL}/accounts", headers=headers)
        if after_pending_response.status_code != 200:
            print_test_result("Verificar saldo após pendente", False, "Erro ao obter saldo")
            return False
        
        after_pending_accounts = after_pending_response.json()
        after_pending_account = next((acc for acc in after_pending_accounts if acc.get("id") == account_id), None)
        balance_after_pending = after_pending_account.get("current_balance")
        
        # CRITICAL TEST: Balance should NOT change for pending transactions
        if abs(balance_after_pending - initial_balance) < 0.01:
            print_test_result("✅ CORREÇÃO DO BUG: Saldo não alterado para transação pendente", True, 
                            f"Saldo permaneceu: R$ {balance_after_pending:.2f} (correto!)")
        else:
            print_test_result("❌ BUG AINDA PRESENTE: Saldo alterado para transação pendente", False, 
                            f"Saldo inicial: R$ {initial_balance:.2f}, Após pendente: R$ {balance_after_pending:.2f}")
            return False
        
        # Step 4: Confirm the pending transaction → balance should decrease by R$ 100.00
        confirm_response = requests.patch(f"{BACKEND_URL}/transactions/{pending_transaction_id}/confirm-payment", 
                                        headers=headers)
        
        if confirm_response.status_code != 200:
            print_test_result("Confirmar transação pendente", False, 
                            f"Status: {confirm_response.status_code}, Erro: {confirm_response.text}")
            return False
        
        print_test_result("Confirmar transação pendente", True, "Transação confirmada com sucesso")
        
        # Verify balance decreases by R$ 100.00 after confirmation
        after_confirm_response = requests.get(f"{BACKEND_URL}/accounts", headers=headers)
        after_confirm_accounts = after_confirm_response.json()
        after_confirm_account = next((acc for acc in after_confirm_accounts if acc.get("id") == account_id), None)
        balance_after_confirm = after_confirm_account.get("current_balance")
        
        expected_balance_after_confirm = initial_balance - 100.00
        if abs(balance_after_confirm - expected_balance_after_confirm) < 0.01:
            print_test_result("✅ CORREÇÃO DO BUG: Saldo deduzido apenas na confirmação", True, 
                            f"Saldo após confirmação: R$ {balance_after_confirm:.2f} (dedução única de R$ 100.00)")
        else:
            print_test_result("❌ BUG: Dedução incorreta na confirmação", False, 
                            f"Esperado: R$ {expected_balance_after_confirm:.2f}, Atual: R$ {balance_after_confirm:.2f}")
            return False
        
        # Step 5: Create PAID transaction (Despesa, R$ 50.00, status: "Pago") → should decrease immediately
        paid_transaction = {
            "description": "Despesa Paga - Teste Bug Fix",
            "value": 50.00,
            "type": "Despesa",
            "transaction_date": datetime.now().isoformat(),
            "account_id": account_id,
            "status": "Pago"  # PAID status - should update balance immediately
        }
        
        paid_response = requests.post(f"{BACKEND_URL}/transactions", json=paid_transaction, headers=headers)
        
        if paid_response.status_code != 200:
            print_test_result("Criar transação paga", False, 
                            f"Status: {paid_response.status_code}, Erro: {paid_response.text}")
            return False
        
        paid_trans = paid_response.json()
        print_test_result("Criar transação paga", True, 
                        f"Transação paga criada: R$ {paid_trans.get('value'):.2f}")
        
        # Verify balance decreases immediately by R$ 50.00 for paid transaction
        after_paid_response = requests.get(f"{BACKEND_URL}/accounts", headers=headers)
        after_paid_accounts = after_paid_response.json()
        after_paid_account = next((acc for acc in after_paid_accounts if acc.get("id") == account_id), None)
        final_balance = after_paid_account.get("current_balance")
        
        expected_final_balance = balance_after_confirm - 50.00
        if abs(final_balance - expected_final_balance) < 0.01:
            print_test_result("✅ CORREÇÃO DO BUG: Transação paga deduzida imediatamente", True, 
                            f"Saldo final: R$ {final_balance:.2f} (dedução imediata de R$ 50.00)")
        else:
            print_test_result("❌ BUG: Dedução incorreta para transação paga", False, 
                            f"Esperado: R$ {expected_final_balance:.2f}, Atual: R$ {final_balance:.2f}")
            return False
        
        # Summary of the complete test
        print("\n" + "="*60)
        print("📊 RESUMO DO TESTE DE CORREÇÃO DO BUG")
        print("="*60)
        print(f"Saldo Inicial:                    R$ {initial_balance:.2f}")
        print(f"Após Transação Pendente:          R$ {balance_after_pending:.2f} (sem alteração ✅)")
        print(f"Após Confirmação da Pendente:     R$ {balance_after_confirm:.2f} (dedução única ✅)")
        print(f"Após Transação Paga:              R$ {final_balance:.2f} (dedução imediata ✅)")
        print("="*60)
        print("🎉 BUG CORRIGIDO COM SUCESSO!")
        print("   - Transações pendentes NÃO alteram saldo")
        print("   - Confirmação de pendentes deduz apenas uma vez")
        print("   - Transações pagas deduzem imediatamente")
        
        return True
        
    except Exception as e:
        print_test_result("Teste de Lógica de Saldo", False, f"Exceção: {str(e)}")
        return False

def run_all_tests():
    """Run all backend tests in sequence"""
    print("🇧🇷 INICIANDO TESTES DO BACKEND ORÇAZENFINANCEIRO")
    print("=" * 80)
    print(f"URL do Backend: {BACKEND_URL}")
    print("=" * 80)
    
    test_results = {}
    
    # Test sequence
    test_results["registration"] = test_user_registration()
    test_results["login"] = test_user_login()
    test_results["jwt_auth"] = test_jwt_authentication()
    test_results["categories"] = test_categories()
    test_results["accounts"] = test_account_management()
    test_results["transactions"] = test_transaction_management()
    test_results["dashboard"] = test_dashboard_summary()
    test_results["goals_system"] = test_goals_system()
    
    # Summary
    print("\n" + "="*80)
    print("RESUMO DOS TESTES")
    print("="*80)
    
    passed_tests = sum(1 for result in test_results.values() if result)
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{status} - {test_name.replace('_', ' ').title()}")
    
    print(f"\nResultado Final: {passed_tests}/{total_tests} testes passaram")
    
    if passed_tests == total_tests:
        print("🎉 TODOS OS TESTES PASSARAM! Backend funcionando corretamente.")
    else:
        print("⚠️  ALGUNS TESTES FALHARAM. Verifique os detalhes acima.")
    
    return test_results

def run_critical_balance_test():
    """Run only the critical balance logic test"""
    print("🔥 EXECUTANDO TESTE CRÍTICO DE CORREÇÃO DO BUG DE SALDO")
    print("=" * 80)
    print(f"URL do Backend: {BACKEND_URL}")
    print("=" * 80)
    
    # Setup required for the test
    if not test_user_login():
        print("❌ Falha no login - não é possível executar o teste")
        return False
    
    if not test_categories():
        print("❌ Falha ao carregar categorias - não é possível executar o teste")
        return False
        
    if not test_account_management():
        print("❌ Falha na gestão de contas - não é possível executar o teste")
        return False
    
    # Run the critical test
    result = test_transaction_balance_logic_fix()
    
    print("\n" + "="*80)
    print("RESULTADO DO TESTE CRÍTICO")
    print("="*80)
    
    if result:
        print("🎉 TESTE CRÍTICO PASSOU! Bug de saldo de transações foi corrigido.")
    else:
        print("❌ TESTE CRÍTICO FALHOU! Bug de saldo ainda presente.")
    
    return result

def test_categories_creation_detailed_debug():
    """
    DETAILED DEBUG: Test category creation process step by step
    """
    print("\n" + "="*80)
    print("🔍 DETAILED DEBUG: CATEGORY CREATION PROCESS")
    print("="*80)
    
    if not auth_token:
        print_test_result("Detailed Categories Debug", False, "Token não disponível")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        # Step 1: Count categories in the backend code
        print("\n📊 STEP 1: Analyzing backend code structure")
        
        # Let's manually count what should be created based on the backend code
        expected_categories = {
            # RECEITAS (13 categories)
            "Receita": [
                "Salário", "Freelance/PJ", "Pró-Labore", "Aluguel Recebido",
                "Dividendos/Juros (Investimentos)", "Vendas (Produtos/Serviços)", 
                "Restituição de IR", "13º Salário", "Férias", "Indenizações",
                "Presentes/Doações Recebidas", "Bônus", "Outras Receitas"
            ],
            
            # MAIN GROUPS (12 main expense groups)
            "Main_Groups": [
                "Moradia", "Transporte", "Alimentação", "Educação", "Saúde",
                "Lazer e Entretenimento", "Compras/Vestuário", "Serviços Pessoais",
                "Dívidas e Empréstimos", "Impostos e Taxas", "Investimentos",
                "Despesas com Pets"
            ],
            
            # SUBCATEGORIES by group
            "Moradia_subs": [
                "Aluguel", "Condomínio", "IPTU", "Água", "Luz", "Gás", 
                "Internet", "Telefone Fixo", "Manutenção e Reparos",
                "Financiamento Imobiliário", "Seguro Residencial"
            ],
            
            "Transporte_subs": [
                "Combustível (Gasolina)", "Combustível (Etanol)", "Combustível (GNV)",
                "Estacionamento", "Pedágio", "Transporte Público", "Uber/99/Táxi",
                "Manutenção do Veículo", "Seguro Auto", "IPVA", "Licenciamento",
                "Multas", "Lavagem de Carro", "Revisões"
            ],
            
            "Alimentacao_subs": [
                "Supermercado", "Feira", "Hortifrúti", "Açougue/Padaria",
                "Restaurantes", "Lanches", "Delivery", "Bares/Cafés",
                "Suplementos Alimentares"
            ],
            
            "Educacao_subs": [
                "Mensalidade Escolar", "Mensalidade Universitária", "Cursos Livres/Idiomas",
                "Material Escolar", "Livros", "Pós-graduação"
            ],
            
            "Saude_subs": [
                "Plano de Saúde", "Consultas Médicas", "Especialistas", "Exames",
                "Remédios", "Óculos/Lentes", "Odontologia", "Fisioterapia",
                "Terapias", "Vacinas"
            ],
            
            "Lazer_subs": [
                "Cinema", "Teatro", "Shows", "Eventos Esportivos",
                "Viagens (Passagens)", "Viagens (Hospedagem)", "Viagens (Passeios)",
                "Netflix", "Spotify", "Prime Video", "Globoplay", "Jogos",
                "Hobbies", "Festas/Eventos Sociais"
            ],
            
            "Compras_subs": [
                "Roupas", "Calçados", "Acessórios", "Eletrônicos", "Eletrodomésticos",
                "Móveis", "Utensílios Domésticos", "Presentes", "Artigos de Decoração"
            ],
            
            "Servicos_subs": [
                "Salão de Beleza", "Cabeleireiro", "Manicure", "Barbearia",
                "Academia", "Personal Trainer", "Estética", "Massagem", "Lavanderia"
            ],
            
            "Dividas_subs": [
                "Empréstimos Pessoais", "Financiamento de Veículo", 
                "Fatura do Cartão de Crédito", "Juros de Dívidas", "Cheque Especial"
            ],
            
            "Impostos_subs": [
                "Imposto de Renda", "Taxas Bancárias", "Contribuição Sindical",
                "Taxas de Condomínio Extras"
            ],
            
            "Investimentos_subs": [
                "Aplicações Financeiras", "Compra de Ações", "Fundos de Investimento",
                "Poupança Programada", "Custos de Corretagem"
            ],
            
            "Pets_subs": [
                "Ração", "Veterinário", "Acessórios para Pets", "Banho e Tosa"
            ]
        }
        
        # Calculate expected totals
        expected_receitas = len(expected_categories["Receita"])
        expected_main_groups = len(expected_categories["Main_Groups"])
        expected_subcategories = sum([
            len(expected_categories["Moradia_subs"]),
            len(expected_categories["Transporte_subs"]),
            len(expected_categories["Alimentacao_subs"]),
            len(expected_categories["Educacao_subs"]),
            len(expected_categories["Saude_subs"]),
            len(expected_categories["Lazer_subs"]),
            len(expected_categories["Compras_subs"]),
            len(expected_categories["Servicos_subs"]),
            len(expected_categories["Dividas_subs"]),
            len(expected_categories["Impostos_subs"]),
            len(expected_categories["Investimentos_subs"]),
            len(expected_categories["Pets_subs"])
        ])
        
        # Add other categories
        expected_other = 2  # "Doações" main group + "Outras Despesas"
        expected_doacoes_subs = 2  # "Caridade", "Dízimo"
        
        total_expected = expected_receitas + expected_main_groups + expected_subcategories + expected_other + expected_doacoes_subs
        
        print(f"   📊 Expected breakdown:")
        print(f"      - Receita categories: {expected_receitas}")
        print(f"      - Main expense groups: {expected_main_groups}")
        print(f"      - Subcategories: {expected_subcategories}")
        print(f"      - Other categories: {expected_other + expected_doacoes_subs}")
        print(f"      - TOTAL EXPECTED: {total_expected}")
        
        # Step 2: Get actual categories
        print("\n📊 STEP 2: Getting actual categories from database")
        response = requests.get(f"{BACKEND_URL}/categories", headers=headers)
        
        if response.status_code != 200:
            print_test_result("Get Categories", False, f"Status: {response.status_code}")
            return False
        
        categories = response.json()
        actual_total = len(categories)
        
        print(f"   📊 Actual total: {actual_total}")
        print(f"   📊 Gap: {total_expected - actual_total} categories missing")
        
        # Step 3: Detailed analysis of what's missing
        print("\n📊 STEP 3: Detailed missing category analysis")
        
        category_names = [cat.get("name") for cat in categories]
        
        # Check each expected group
        for group_name, expected_list in expected_categories.items():
            if group_name.endswith("_subs"):
                continue  # Skip subcategory lists for now
                
            missing_in_group = [cat for cat in expected_list if cat not in category_names]
            found_in_group = [cat for cat in expected_list if cat in category_names]
            
            if missing_in_group:
                print(f"   ❌ {group_name}: Missing {len(missing_in_group)}/{len(expected_list)}")
                print(f"      Missing: {', '.join(missing_in_group)}")
            else:
                print(f"   ✅ {group_name}: All {len(expected_list)} categories found")
        
        # Step 4: Check subcategories for each main group
        print("\n📊 STEP 4: Subcategory analysis by main group")
        
        parent_categories = [cat for cat in categories if cat.get("parent_category_id") is None]
        child_categories = [cat for cat in categories if cat.get("parent_category_id") is not None]
        
        subcategory_groups = {
            "Moradia": "Moradia_subs",
            "Transporte": "Transporte_subs", 
            "Alimentação": "Alimentacao_subs",
            "Educação": "Educacao_subs",
            "Saúde": "Saude_subs",
            "Lazer e Entretenimento": "Lazer_subs",
            "Compras/Vestuário": "Compras_subs",
            "Serviços Pessoais": "Servicos_subs",
            "Dívidas e Empréstimos": "Dividas_subs",
            "Impostos e Taxas": "Impostos_subs",
            "Investimentos": "Investimentos_subs",
            "Despesas com Pets": "Pets_subs"
        }
        
        for main_group, subs_key in subcategory_groups.items():
            parent_cat = next((cat for cat in parent_categories if cat.get("name") == main_group), None)
            
            if parent_cat:
                parent_id = parent_cat.get("id")
                actual_subs = [cat for cat in child_categories if cat.get("parent_category_id") == parent_id]
                actual_sub_names = [cat.get("name") for cat in actual_subs]
                expected_subs = expected_categories[subs_key]
                
                missing_subs = [sub for sub in expected_subs if sub not in actual_sub_names]
                
                if missing_subs:
                    print(f"   ❌ {main_group}: {len(actual_subs)}/{len(expected_subs)} subcategories")
                    print(f"      Missing: {', '.join(missing_subs)}")
                else:
                    print(f"   ✅ {main_group}: All {len(expected_subs)} subcategories found")
            else:
                print(f"   ❌ {main_group}: Main group not found (0/{len(expected_categories[subs_key])} subcategories)")
        
        # Step 5: Identify the exact point where creation stops
        print("\n📊 STEP 5: Identifying where category creation stops")
        
        # Based on the pattern, let's see which categories are the last ones created
        print("   🔍 Analyzing creation pattern...")
        
        # Check if the issue is with specific groups
        missing_main_groups = []
        for group in expected_categories["Main_Groups"]:
            if group not in category_names:
                missing_main_groups.append(group)
        
        if missing_main_groups:
            print(f"   ❌ Missing main groups: {', '.join(missing_main_groups)}")
            print("   🔍 This suggests the create_default_categories function is stopping")
            print("       before processing all main groups in the list.")
        
        # Final diagnosis
        print(f"\n🔍 FINAL DIAGNOSIS:")
        print(f"   Expected: {total_expected} categories")
        print(f"   Actual: {actual_total} categories") 
        print(f"   Success rate: {(actual_total/total_expected)*100:.1f}%")
        
        if actual_total < total_expected * 0.5:  # Less than 50% created
            print("   🚨 CRITICAL: Less than 50% of categories created")
            print("   🔍 Root cause: create_default_categories function is failing partway through")
            print("   💡 Likely causes:")
            print("      1. Database insertion error not being caught")
            print("      2. Parent-child relationship mapping failure")
            print("      3. Memory or timeout issues during bulk insertion")
            
            return False
        else:
            return True
            
    except Exception as e:
        print_test_result("Detailed Categories Debug", False, f"Exception: {str(e)}")
        return False

def test_categories_creation_debug():
    """
    COMPREHENSIVE CATEGORIES CREATION DEBUG TEST
    
    Debug why only 42 categories are being created instead of the expected 120+.
    
    Test Plan:
    1. Test with EXISTING user (teste.debug@email.com)
    2. Get current categories count
    3. Check if categories were created correctly for this user
    4. Test Categories Creation Logic
    5. Call the categories endpoint and count categories by type and parent relationships
    6. Verify parent/child relationships are being created properly
    7. Check if the create_default_categories function is working correctly
    8. Detailed Category Analysis - Count main groups and subcategories
    9. Identify which groups/subcategories are missing
    """
    print("\n" + "="*80)
    print("🔍 DEBUG: COMPREHENSIVE BRAZILIAN CATEGORIES SYSTEM")
    print("="*80)
    print("Debugging why only 42 categories are created instead of expected 120+")
    
    if not auth_token:
        print_test_result("Categories Debug", False, "Token não disponível")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        # Step 1: Get all categories for the user
        print("\n📊 STEP 1: Getting all categories for user teste.debug@email.com")
        response = requests.get(f"{BACKEND_URL}/categories", headers=headers)
        
        if response.status_code != 200:
            print_test_result("Get Categories", False, 
                            f"Status: {response.status_code}, Error: {response.text}")
            return False
        
        categories = response.json()
        total_categories = len(categories)
        
        print_test_result("Get Categories", True, f"Found {total_categories} categories")
        
        # Step 2: Analyze categories by type
        print("\n📊 STEP 2: Analyzing categories by type")
        receita_categories = [cat for cat in categories if cat.get("type") == "Receita"]
        despesa_categories = [cat for cat in categories if cat.get("type") == "Despesa"]
        
        print(f"   📈 Receita categories: {len(receita_categories)}")
        print(f"   📉 Despesa categories: {len(despesa_categories)}")
        
        # Step 3: Analyze parent/child relationships
        print("\n📊 STEP 3: Analyzing parent/child relationships")
        parent_categories = [cat for cat in categories if cat.get("parent_category_id") is None]
        child_categories = [cat for cat in categories if cat.get("parent_category_id") is not None]
        
        print(f"   👨‍👩‍👧‍👦 Parent categories: {len(parent_categories)}")
        print(f"   👶 Child categories: {len(child_categories)}")
        
        # Step 4: Expected main groups analysis
        print("\n📊 STEP 4: Expected main groups analysis")
        expected_main_groups = [
            "Moradia", "Transporte", "Alimentação", "Saúde", 
            "Lazer e Entretenimento", "Educação", "Compras/Vestuário", 
            "Serviços Pessoais", "Dívidas e Empréstimos", "Impostos e Taxas", 
            "Investimentos", "Despesas com Pets"
        ]
        
        found_main_groups = []
        missing_main_groups = []
        
        for group in expected_main_groups:
            found = any(cat.get("name") == group for cat in parent_categories)
            if found:
                found_main_groups.append(group)
            else:
                missing_main_groups.append(group)
        
        print(f"   ✅ Found main groups ({len(found_main_groups)}/12): {', '.join(found_main_groups)}")
        if missing_main_groups:
            print(f"   ❌ Missing main groups ({len(missing_main_groups)}/12): {', '.join(missing_main_groups)}")
        
        # Step 5: Detailed subcategory analysis for each found main group
        print("\n📊 STEP 5: Detailed subcategory analysis")
        
        subcategory_analysis = {}
        for main_group in found_main_groups:
            parent_cat = next((cat for cat in parent_categories if cat.get("name") == main_group), None)
            if parent_cat:
                parent_id = parent_cat.get("id")
                subcategories = [cat for cat in child_categories if cat.get("parent_category_id") == parent_id]
                subcategory_analysis[main_group] = {
                    "count": len(subcategories),
                    "names": [cat.get("name") for cat in subcategories]
                }
                print(f"   🏠 {main_group}: {len(subcategories)} subcategories")
                if subcategories:
                    print(f"      └─ {', '.join([cat.get('name') for cat in subcategories])}")
        
        # Step 6: Check for expected subcategories in key groups
        print("\n📊 STEP 6: Checking for expected subcategories in key groups")
        
        expected_subcategories = {
            "Transporte": ["Combustível (Gasolina)", "Uber/99/Táxi", "Transporte Público", "Estacionamento", "IPVA"],
            "Saúde": ["Plano de Saúde", "Consultas Médicas", "Remédios", "Odontologia"],
            "Lazer e Entretenimento": ["Cinema", "Netflix", "Spotify", "Viagens (Passagens)", "Viagens (Hospedagem)"],
            "Alimentação": ["Supermercado", "Restaurantes", "Delivery", "Feira", "Bares/Cafés"]
        }
        
        for group, expected_subs in expected_subcategories.items():
            if group in subcategory_analysis:
                found_subs = subcategory_analysis[group]["names"]
                missing_subs = [sub for sub in expected_subs if sub not in found_subs]
                if missing_subs:
                    print(f"   ❌ {group} missing subcategories: {', '.join(missing_subs)}")
                else:
                    print(f"   ✅ {group} has all expected subcategories")
            else:
                print(f"   ❌ {group} main group not found")
        
        # Step 7: Check for income categories
        print("\n📊 STEP 7: Analyzing income categories")
        expected_income_categories = [
            "Salário", "Freelance/PJ", "Pró-Labore", "Aluguel Recebido", 
            "Dividendos/Juros (Investimentos)", "13º Salário", "Férias", "Bônus"
        ]
        
        found_income = []
        missing_income = []
        
        income_names = [cat.get("name") for cat in receita_categories]
        for income_cat in expected_income_categories:
            if income_cat in income_names:
                found_income.append(income_cat)
            else:
                missing_income.append(income_cat)
        
        print(f"   ✅ Found income categories ({len(found_income)}/{len(expected_income_categories)}): {', '.join(found_income)}")
        if missing_income:
            print(f"   ❌ Missing income categories: {', '.join(missing_income)}")
        
        # Step 8: Summary and diagnosis
        print("\n📊 STEP 8: DIAGNOSIS SUMMARY")
        print("="*60)
        print(f"Total Categories Found: {total_categories}")
        print(f"Expected Categories: 120+")
        print(f"Gap: {120 - total_categories} categories missing")
        print()
        print(f"Main Groups Found: {len(found_main_groups)}/12")
        print(f"Income Categories Found: {len(found_income)}/{len(expected_income_categories)}")
        print(f"Parent Categories: {len(parent_categories)}")
        print(f"Child Categories: {len(child_categories)}")
        
        # Step 9: Identify the root cause
        print("\n🔍 STEP 9: ROOT CAUSE ANALYSIS")
        print("="*60)
        
        if len(found_main_groups) < 12:
            print(f"❌ ISSUE 1: Only {len(found_main_groups)}/12 main groups created")
            print(f"   Missing groups: {', '.join(missing_main_groups)}")
        
        if len(child_categories) < 80:  # Expected ~80+ subcategories
            print(f"❌ ISSUE 2: Only {len(child_categories)} subcategories created (expected 80+)")
        
        if len(receita_categories) < 13:  # Expected 13 income categories
            print(f"❌ ISSUE 3: Only {len(receita_categories)} income categories created (expected 13)")
        
        # Step 10: Check if create_default_categories function is working properly
        print("\n🔍 STEP 10: TESTING CATEGORY CREATION LOGIC")
        print("="*60)
        
        # Let's check if we can see the pattern in what's missing
        if total_categories == 42:
            print("🔍 PATTERN DETECTED: Exactly 42 categories suggests partial creation")
            print("   This indicates the create_default_categories function may be:")
            print("   1. Stopping early due to an error")
            print("   2. Not processing all categories in the default list")
            print("   3. Having issues with parent-child relationship creation")
        
        # Final assessment
        if total_categories < 100:
            print_test_result("Categories Creation Debug", False, 
                            f"Only {total_categories}/120+ categories created. Major gaps identified.")
            return False
        else:
            print_test_result("Categories Creation Debug", True, 
                            f"Categories creation working properly: {total_categories} categories found")
            return True
        
    except Exception as e:
        print_test_result("Categories Creation Debug", False, f"Exception: {str(e)}")
        return False

def run_categories_debug_test():
    """Run only the categories creation debug test"""
    print("🔍 EXECUTANDO DEBUG DE CRIAÇÃO DE CATEGORIAS")
    print("=" * 80)
    print(f"URL do Backend: {BACKEND_URL}")
    print("=" * 80)
    
    # Setup required for the test - login with existing user
    if not test_user_login():
        print("❌ Falha no login - não é possível executar o teste")
        return False
    
    # Run the detailed categories debug test
    result1 = test_categories_creation_detailed_debug()
    
    # Also run the original debug test for comparison
    result2 = test_categories_creation_debug()
    
    print("\n" + "="*80)
    print("RESULTADO DO DEBUG DE CATEGORIAS")
    print("="*80)
    
    if result1 and result2:
        print("🎉 CATEGORIAS FUNCIONANDO CORRETAMENTE!")
    else:
        print("❌ PROBLEMAS IDENTIFICADOS NA CRIAÇÃO DE CATEGORIAS!")
        print("   Verifique os detalhes acima para identificar as causas.")
    
    return result1 and result2

if __name__ == "__main__":
    # Run the categories creation debug test as requested
    run_categories_debug_test()