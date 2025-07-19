#!/usr/bin/env python3
"""
OrçaZenFinanceiro Backend API Testing Suite
Tests all backend endpoints with Brazilian test data
"""

import requests
import json
from datetime import datetime, timedelta
import uuid

# Configuration
BACKEND_URL = "https://c432aa88-8ae0-42ae-9224-4ead0f8df479.preview.emergentagent.com/api"

# Test data with Brazilian names and content
TEST_USER_DATA = {
    "name": "Maria Silva Santos",
    "email": "maria.silva@email.com.br",
    "password": "MinhaSenh@123"
}

TEST_USER_LOGIN = {
    "email": "maria.silva@email.com.br", 
    "password": "MinhaSenh@123"
}

# Global variables to store test data
auth_token = None
user_id = None
account_id = None
category_id = None

def print_test_result(test_name, success, details=""):
    """Print formatted test results"""
    status = "✅ PASSOU" if success else "❌ FALHOU"
    print(f"\n{status} - {test_name}")
    if details:
        print(f"   Detalhes: {details}")

def test_user_registration():
    """Test user registration endpoint"""
    global auth_token, user_id
    
    print("\n" + "="*60)
    print("TESTANDO REGISTRO DE USUÁRIO")
    print("="*60)
    
    try:
        response = requests.post(f"{BACKEND_URL}/auth/register", json=TEST_USER_DATA)
        
        if response.status_code == 200:
            data = response.json()
            auth_token = data.get("access_token")
            user_info = data.get("user", {})
            user_id = user_info.get("id")
            
            print_test_result("Registro de usuário", True, 
                            f"Token recebido, usuário: {user_info.get('name')}")
            
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

if __name__ == "__main__":
    run_all_tests()