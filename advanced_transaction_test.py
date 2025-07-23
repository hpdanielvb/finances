#!/usr/bin/env python3
"""
Advanced Transaction Management System Testing Suite
Tests the newly implemented features:
1. Enhanced Brazilian Categories System (120+ categories)
2. Intelligent Category Suggestion System
3. Recent Descriptions Autocomplete
4. Advanced Transaction Filtering
5. Transaction Status Management
6. Transaction Statistics
"""

import requests
import json
from datetime import datetime, timedelta
import uuid

# Configuration
BACKEND_URL = "https://6742bccc-697e-4837-b503-d6ac88619844.preview.emergentagent.com/api"

# Test user credentials (existing user from previous tests)
TEST_USER_LOGIN = {
    "email": "teste.debug@email.com", 
    "password": "MinhaSenh@123"
}

# Global variables
auth_token = None
user_id = None
account_id = None
test_transactions = []

def print_test_result(test_name, success, details=""):
    """Print formatted test results"""
    status = "✅ PASSOU" if success else "❌ FALHOU"
    print(f"\n{status} - {test_name}")
    if details:
        print(f"   Detalhes: {details}")

def login_test_user():
    """Login with existing test user"""
    global auth_token, user_id
    
    print("\n" + "="*80)
    print("FAZENDO LOGIN COM USUÁRIO DE TESTE")
    print("="*80)
    
    try:
        response = requests.post(f"{BACKEND_URL}/auth/login", json=TEST_USER_LOGIN)
        
        if response.status_code == 200:
            data = response.json()
            auth_token = data.get("access_token")
            user_info = data.get("user", {})
            user_id = user_info.get("id")
            
            print_test_result("Login do usuário de teste", True, 
                            f"Logado como: {user_info.get('name')}")
            return True
        else:
            print_test_result("Login do usuário de teste", False, 
                            f"Status: {response.status_code}, Erro: {response.text}")
            return False
            
    except Exception as e:
        print_test_result("Login do usuário de teste", False, f"Exceção: {str(e)}")
        return False

def get_test_account():
    """Get an existing account for testing"""
    global account_id
    
    if not auth_token:
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        response = requests.get(f"{BACKEND_URL}/accounts", headers=headers)
        
        if response.status_code == 200:
            accounts = response.json()
            if len(accounts) > 0:
                account_id = accounts[0]["id"]
                print_test_result("Conta de teste obtida", True, 
                                f"Usando conta: {accounts[0]['name']}")
                return True
            else:
                print_test_result("Conta de teste obtida", False, "Nenhuma conta encontrada")
                return False
        else:
            print_test_result("Conta de teste obtida", False, 
                            f"Status: {response.status_code}")
            return False
            
    except Exception as e:
        print_test_result("Conta de teste obtida", False, f"Exceção: {str(e)}")
        return False

def test_enhanced_brazilian_categories():
    """Test the comprehensive Brazilian categories system (120+ categories)"""
    print("\n" + "="*80)
    print("TESTANDO SISTEMA ABRANGENTE DE CATEGORIAS BRASILEIRAS")
    print("="*80)
    
    if not auth_token:
        print_test_result("Categorias brasileiras", False, "Token não disponível")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        response = requests.get(f"{BACKEND_URL}/categories", headers=headers)
        
        if response.status_code == 200:
            categories = response.json()
            total_categories = len(categories)
            
            print_test_result("Total de categorias", True, 
                            f"Encontradas {total_categories} categorias")
            
            # Check for main category groups (12 main groups expected)
            main_groups = [
                "Moradia", "Transporte", "Alimentação", "Saúde", "Lazer e Entretenimento",
                "Educação", "Compras/Vestuário", "Serviços Pessoais", "Dívidas e Empréstimos",
                "Impostos e Taxas", "Investimentos", "Despesas com Pets"
            ]
            
            category_names = [cat.get("name") for cat in categories]
            found_main_groups = [group for group in main_groups if group in category_names]
            
            print_test_result("Grupos principais de categorias", 
                            len(found_main_groups) >= 8,  # At least 8 of 12 main groups
                            f"Encontrados {len(found_main_groups)}/12 grupos: {', '.join(found_main_groups)}")
            
            # Test specific subcategories for each main group
            subcategory_tests = {
                "Moradia": ["Aluguel", "Condomínio", "IPTU", "Água", "Luz", "Gás", "Internet"],
                "Transporte": ["Combustível (Gasolina)", "Uber/99/Táxi", "Transporte Público", "IPVA", "Seguro Auto"],
                "Alimentação": ["Supermercado", "Feira", "Hortifrúti", "Delivery", "Bares/Cafés"],
                "Saúde": ["Plano de Saúde", "Consultas Médicas", "Remédios", "Odontologia"],
                "Lazer e Entretenimento": ["Cinema", "Netflix", "Spotify", "Viagens (Passagens)", "Viagens (Hospedagem)"]
            }
            
            for main_category, expected_subcategories in subcategory_tests.items():
                found_subcategories = [sub for sub in expected_subcategories if sub in category_names]
                success_rate = len(found_subcategories) / len(expected_subcategories)
                
                print_test_result(f"Subcategorias de {main_category}", 
                                success_rate >= 0.6,  # At least 60% of expected subcategories
                                f"Encontradas {len(found_subcategories)}/{len(expected_subcategories)}: {', '.join(found_subcategories)}")
            
            # Test parent/child relationships
            parent_categories = [cat for cat in categories if cat.get("parent_category_id") is None and cat.get("type") == "Despesa"]
            child_categories = [cat for cat in categories if cat.get("parent_category_id") is not None]
            
            print_test_result("Relacionamentos pai/filho", 
                            len(parent_categories) > 0 and len(child_categories) > 0,
                            f"Categorias pai: {len(parent_categories)}, Categorias filhas: {len(child_categories)}")
            
            # Test income categories
            income_categories = [cat for cat in categories if cat.get("type") == "Receita"]
            expected_income_cats = ["Salário", "Freelance/PJ", "13º Salário", "Férias", "Bônus"]
            found_income_cats = [cat for cat in expected_income_cats if cat in category_names]
            
            print_test_result("Categorias de receita", 
                            len(found_income_cats) >= 3,
                            f"Encontradas {len(found_income_cats)}/{len(expected_income_cats)}: {', '.join(found_income_cats)}")
            
            # Overall assessment
            if total_categories >= 50:  # Expecting at least 50 categories for a comprehensive system
                print_test_result("Sistema abrangente de categorias", True, 
                                f"Sistema robusto com {total_categories} categorias")
                return True
            else:
                print_test_result("Sistema abrangente de categorias", False, 
                                f"Sistema básico com apenas {total_categories} categorias")
                return False
                
        else:
            print_test_result("Categorias brasileiras", False, 
                            f"Status: {response.status_code}, Erro: {response.text}")
            return False
            
    except Exception as e:
        print_test_result("Categorias brasileiras", False, f"Exceção: {str(e)}")
        return False

def test_intelligent_category_suggestion():
    """Test the intelligent category suggestion system"""
    print("\n" + "="*80)
    print("TESTANDO SISTEMA INTELIGENTE DE SUGESTÃO DE CATEGORIAS")
    print("="*80)
    
    if not auth_token:
        print_test_result("Sugestão inteligente", False, "Token não disponível")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Test cases with expected suggestions
    test_cases = [
        {
            "description": "Supermercado Pão de Açúcar",
            "type": "Despesa",
            "expected_category": "Supermercado",
            "expected_confidence": "high"
        },
        {
            "description": "Uber para aeroporto",
            "type": "Despesa", 
            "expected_category": "Uber/99/Táxi",
            "expected_confidence": "high"
        },
        {
            "description": "Consulta médico cardiologista",
            "type": "Despesa",
            "expected_category": "Consultas Médicas",
            "expected_confidence": "high"
        },
        {
            "description": "Netflix assinatura mensal",
            "type": "Despesa",
            "expected_category": "Netflix",
            "expected_confidence": "high"
        },
        {
            "description": "Gasolina posto Shell",
            "type": "Despesa",
            "expected_category": "Combustível (Gasolina)",
            "expected_confidence": "high"
        },
        {
            "description": "Salário Janeiro 2025",
            "type": "Receita",
            "expected_category": "Salário",
            "expected_confidence": "high"
        },
        {
            "description": "Pagamento freelance projeto",
            "type": "Receita",
            "expected_category": "Freelance/PJ",
            "expected_confidence": "high"
        },
        {
            "description": "Compra aleatória sem palavras-chave",
            "type": "Despesa",
            "expected_category": "Outras Despesas",
            "expected_confidence": "low"
        }
    ]
    
    successful_suggestions = 0
    total_tests = len(test_cases)
    
    try:
        for i, test_case in enumerate(test_cases, 1):
            request_data = {
                "description": test_case["description"],
                "type": test_case["type"]
            }
            
            response = requests.post(f"{BACKEND_URL}/transactions/suggest-category", 
                                   json=request_data, headers=headers)
            
            if response.status_code == 200:
                suggestion = response.json()
                suggested_category = suggestion.get("suggested_category")
                confidence = suggestion.get("confidence")
                category_id = suggestion.get("category_id")
                
                # Check if suggestion matches expected
                category_match = suggested_category == test_case["expected_category"]
                confidence_match = confidence == test_case["expected_confidence"]
                
                if category_match and confidence_match:
                    successful_suggestions += 1
                    print_test_result(f"Sugestão {i}: '{test_case['description']}'", True,
                                    f"Sugeriu '{suggested_category}' com confiança {confidence}")
                else:
                    print_test_result(f"Sugestão {i}: '{test_case['description']}'", False,
                                    f"Esperado: '{test_case['expected_category']}' ({test_case['expected_confidence']}), "
                                    f"Obtido: '{suggested_category}' ({confidence})")
                
                # Verify category_id is provided for valid suggestions
                if suggested_category not in ["Outras Despesas", "Outras Receitas"] and not category_id:
                    print_test_result(f"ID da categoria {i}", False, "category_id não fornecido para sugestão válida")
                
            else:
                print_test_result(f"Sugestão {i}: '{test_case['description']}'", False,
                                f"Status: {response.status_code}, Erro: {response.text}")
        
        # Overall success rate
        success_rate = successful_suggestions / total_tests
        print_test_result("Taxa de sucesso das sugestões", 
                        success_rate >= 0.7,  # At least 70% success rate
                        f"{successful_suggestions}/{total_tests} sugestões corretas ({success_rate:.1%})")
        
        return success_rate >= 0.7
        
    except Exception as e:
        print_test_result("Sugestão inteligente", False, f"Exceção: {str(e)}")
        return False

def test_recent_descriptions_autocomplete():
    """Test recent descriptions autocomplete functionality"""
    print("\n" + "="*80)
    print("TESTANDO AUTOCOMPLETAR DE DESCRIÇÕES RECENTES")
    print("="*80)
    
    if not auth_token or not account_id:
        print_test_result("Descrições recentes", False, "Token ou conta não disponível")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        # First, create some transactions with different descriptions
        test_descriptions = [
            "Supermercado Extra - Compras semanais",
            "Posto Shell - Gasolina",
            "Netflix - Assinatura mensal",
            "Uber - Corrida para trabalho",
            "Farmácia Drogasil - Medicamentos"
        ]
        
        created_transactions = 0
        for desc in test_descriptions:
            transaction_data = {
                "description": desc,
                "value": 50.00,
                "type": "Despesa",
                "transaction_date": datetime.now().isoformat(),
                "account_id": account_id,
                "status": "Pago"
            }
            
            response = requests.post(f"{BACKEND_URL}/transactions", 
                                   json=transaction_data, headers=headers)
            if response.status_code == 200:
                created_transactions += 1
        
        print_test_result("Criação de transações de teste", 
                        created_transactions >= 3,
                        f"Criadas {created_transactions}/{len(test_descriptions)} transações")
        
        # Now test the recent descriptions endpoint
        response = requests.get(f"{BACKEND_URL}/transactions/recent-descriptions", headers=headers)
        
        if response.status_code == 200:
            recent_descriptions = response.json()
            
            print_test_result("Endpoint de descrições recentes", True,
                            f"Retornou {len(recent_descriptions)} descrições")
            
            # Verify it returns a list of strings
            if isinstance(recent_descriptions, list) and len(recent_descriptions) > 0:
                all_strings = all(isinstance(desc, str) for desc in recent_descriptions)
                print_test_result("Formato das descrições", all_strings,
                                "Todas as descrições são strings" if all_strings else "Formato inválido")
                
                # Check if our test descriptions appear in the results
                found_descriptions = [desc for desc in test_descriptions 
                                    if any(test_desc in desc for test_desc in recent_descriptions)]
                
                print_test_result("Descrições de teste encontradas", 
                                len(found_descriptions) >= 2,
                                f"Encontradas {len(found_descriptions)} das {len(test_descriptions)} descrições de teste")
                
                # Verify uniqueness (no duplicates)
                unique_descriptions = len(set(recent_descriptions))
                total_descriptions = len(recent_descriptions)
                
                print_test_result("Unicidade das descrições", 
                                unique_descriptions == total_descriptions,
                                f"Únicas: {unique_descriptions}, Total: {total_descriptions}")
                
                return True
            else:
                print_test_result("Formato das descrições", False, "Lista vazia ou formato inválido")
                return False
                
        else:
            print_test_result("Endpoint de descrições recentes", False,
                            f"Status: {response.status_code}, Erro: {response.text}")
            return False
            
    except Exception as e:
        print_test_result("Descrições recentes", False, f"Exceção: {str(e)}")
        return False

def test_advanced_transaction_filtering():
    """Test comprehensive transaction filtering capabilities"""
    print("\n" + "="*80)
    print("TESTANDO FILTRAGEM AVANÇADA DE TRANSAÇÕES")
    print("="*80)
    
    if not auth_token or not account_id:
        print_test_result("Filtragem avançada", False, "Token ou conta não disponível")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        # Create test transactions with different characteristics for filtering
        base_date = datetime.now()
        test_transactions_data = [
            {
                "description": "Salário Janeiro",
                "value": 5000.00,
                "type": "Receita",
                "transaction_date": (base_date - timedelta(days=5)).isoformat(),
                "account_id": account_id,
                "status": "Pago"
            },
            {
                "description": "Supermercado Carrefour",
                "value": 150.00,
                "type": "Despesa",
                "transaction_date": (base_date - timedelta(days=3)).isoformat(),
                "account_id": account_id,
                "status": "Pago"
            },
            {
                "description": "Conta de luz pendente",
                "value": 120.00,
                "type": "Despesa",
                "transaction_date": (base_date + timedelta(days=2)).isoformat(),
                "account_id": account_id,
                "status": "Pendente"
            },
            {
                "description": "Freelance projeto X",
                "value": 800.00,
                "type": "Receita",
                "transaction_date": (base_date - timedelta(days=10)).isoformat(),
                "account_id": account_id,
                "status": "Pago"
            }
        ]
        
        # Create the test transactions
        created_count = 0
        for trans_data in test_transactions_data:
            response = requests.post(f"{BACKEND_URL}/transactions", 
                                   json=trans_data, headers=headers)
            if response.status_code == 200:
                created_count += 1
        
        print_test_result("Criação de transações para filtros", 
                        created_count >= 3,
                        f"Criadas {created_count}/{len(test_transactions_data)} transações")
        
        # Test 1: Date range filtering
        start_date = (base_date - timedelta(days=7)).strftime("%Y-%m-%d")
        end_date = (base_date - timedelta(days=1)).strftime("%Y-%m-%d")
        
        params = {
            "start_date": start_date,
            "end_date": end_date
        }
        
        response = requests.get(f"{BACKEND_URL}/transactions", params=params, headers=headers)
        
        if response.status_code == 200:
            filtered_transactions = response.json()
            print_test_result("Filtro por intervalo de datas", True,
                            f"Encontradas {len(filtered_transactions)} transações no período")
        else:
            print_test_result("Filtro por intervalo de datas", False,
                            f"Status: {response.status_code}")
        
        # Test 2: Search by description (case insensitive)
        params = {"search": "supermercado"}
        response = requests.get(f"{BACKEND_URL}/transactions", params=params, headers=headers)
        
        if response.status_code == 200:
            search_results = response.json()
            # Check if results contain the search term
            relevant_results = [t for t in search_results 
                              if "supermercado" in t.get("description", "").lower()]
            
            print_test_result("Busca por descrição (case insensitive)", 
                            len(relevant_results) > 0,
                            f"Encontradas {len(relevant_results)} transações com 'supermercado'")
        else:
            print_test_result("Busca por descrição", False,
                            f"Status: {response.status_code}")
        
        # Test 3: Filter by transaction type
        params = {"type_filter": "Receita"}
        response = requests.get(f"{BACKEND_URL}/transactions", params=params, headers=headers)
        
        if response.status_code == 200:
            income_transactions = response.json()
            all_income = all(t.get("type") == "Receita" for t in income_transactions)
            
            print_test_result("Filtro por tipo (Receita)", 
                            all_income and len(income_transactions) > 0,
                            f"Encontradas {len(income_transactions)} receitas")
        else:
            print_test_result("Filtro por tipo", False,
                            f"Status: {response.status_code}")
        
        # Test 4: Filter by status
        params = {"status": "Pendente"}
        response = requests.get(f"{BACKEND_URL}/transactions", params=params, headers=headers)
        
        if response.status_code == 200:
            pending_transactions = response.json()
            all_pending = all(t.get("status") == "Pendente" for t in pending_transactions)
            
            print_test_result("Filtro por status (Pendente)", 
                            all_pending and len(pending_transactions) > 0,
                            f"Encontradas {len(pending_transactions)} transações pendentes")
        else:
            print_test_result("Filtro por status", False,
                            f"Status: {response.status_code}")
        
        # Test 5: Value range filtering
        params = {
            "min_value": 100.00,
            "max_value": 1000.00
        }
        response = requests.get(f"{BACKEND_URL}/transactions", params=params, headers=headers)
        
        if response.status_code == 200:
            value_filtered = response.json()
            in_range = all(100.00 <= t.get("value", 0) <= 1000.00 for t in value_filtered)
            
            print_test_result("Filtro por faixa de valores", 
                            in_range and len(value_filtered) > 0,
                            f"Encontradas {len(value_filtered)} transações entre R$ 100-1000")
        else:
            print_test_result("Filtro por faixa de valores", False,
                            f"Status: {response.status_code}")
        
        # Test 6: Pagination
        params = {
            "limit": 2,
            "offset": 0
        }
        response = requests.get(f"{BACKEND_URL}/transactions", params=params, headers=headers)
        
        if response.status_code == 200:
            paginated_results = response.json()
            
            print_test_result("Paginação", 
                            len(paginated_results) <= 2,
                            f"Retornou {len(paginated_results)} transações (limite: 2)")
        else:
            print_test_result("Paginação", False,
                            f"Status: {response.status_code}")
        
        # Test 7: Combined filters
        params = {
            "type_filter": "Despesa",
            "status": "Pago",
            "min_value": 100.00
        }
        response = requests.get(f"{BACKEND_URL}/transactions", params=params, headers=headers)
        
        if response.status_code == 200:
            combined_results = response.json()
            valid_results = all(
                t.get("type") == "Despesa" and 
                t.get("status") == "Pago" and 
                t.get("value", 0) >= 100.00 
                for t in combined_results
            )
            
            print_test_result("Filtros combinados", 
                            valid_results,
                            f"Encontradas {len(combined_results)} despesas pagas >= R$ 100")
        else:
            print_test_result("Filtros combinados", False,
                            f"Status: {response.status_code}")
        
        return True
        
    except Exception as e:
        print_test_result("Filtragem avançada", False, f"Exceção: {str(e)}")
        return False

def test_transaction_status_management():
    """Test transaction status management (Pendente → Pago)"""
    print("\n" + "="*80)
    print("TESTANDO GESTÃO DE STATUS DE TRANSAÇÕES")
    print("="*80)
    
    if not auth_token or not account_id:
        print_test_result("Gestão de status", False, "Token ou conta não disponível")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        # Get initial account balance
        accounts_response = requests.get(f"{BACKEND_URL}/accounts", headers=headers)
        if accounts_response.status_code != 200:
            print_test_result("Gestão de status", False, "Não foi possível obter saldo inicial")
            return False
        
        accounts = accounts_response.json()
        account = next((acc for acc in accounts if acc.get("id") == account_id), None)
        if not account:
            print_test_result("Gestão de status", False, "Conta não encontrada")
            return False
        
        initial_balance = account.get("current_balance")
        print(f"   Saldo inicial da conta: R$ {initial_balance}")
        
        # Create a pending transaction
        pending_transaction = {
            "description": "Conta de internet - Vivo Fibra",
            "value": 89.90,
            "type": "Despesa",
            "transaction_date": datetime.now().isoformat(),
            "account_id": account_id,
            "status": "Pendente"
        }
        
        response = requests.post(f"{BACKEND_URL}/transactions", 
                               json=pending_transaction, headers=headers)
        
        if response.status_code == 200:
            transaction = response.json()
            transaction_id = transaction.get("id")
            
            print_test_result("Criação de transação pendente", True,
                            f"Transação pendente criada: {transaction.get('description')}")
            
            # Verify balance hasn't changed yet (pending transaction)
            updated_accounts_response = requests.get(f"{BACKEND_URL}/accounts", headers=headers)
            if updated_accounts_response.status_code == 200:
                updated_accounts = updated_accounts_response.json()
                updated_account = next((acc for acc in updated_accounts if acc.get("id") == account_id), None)
                
                if updated_account:
                    balance_after_pending = updated_account.get("current_balance")
                    
                    if abs(balance_after_pending - initial_balance) < 0.01:
                        print_test_result("Saldo não alterado (transação pendente)", True,
                                        f"Saldo mantido em R$ {balance_after_pending}")
                    else:
                        print_test_result("Saldo não alterado (transação pendente)", False,
                                        f"Saldo alterado: R$ {initial_balance} → R$ {balance_after_pending}")
            
            # Now confirm the payment
            confirm_response = requests.patch(f"{BACKEND_URL}/transactions/{transaction_id}/confirm-payment", 
                                            headers=headers)
            
            if confirm_response.status_code == 200:
                print_test_result("Confirmação de pagamento", True,
                                "Pagamento confirmado com sucesso")
                
                # Verify transaction status changed to "Pago"
                transactions_response = requests.get(f"{BACKEND_URL}/transactions", headers=headers)
                if transactions_response.status_code == 200:
                    transactions = transactions_response.json()
                    confirmed_transaction = next((t for t in transactions if t.get("id") == transaction_id), None)
                    
                    if confirmed_transaction and confirmed_transaction.get("status") == "Pago":
                        print_test_result("Status atualizado para Pago", True,
                                        "Status da transação atualizado corretamente")
                    else:
                        print_test_result("Status atualizado para Pago", False,
                                        "Status não foi atualizado")
                
                # Verify balance was updated after confirmation
                final_accounts_response = requests.get(f"{BACKEND_URL}/accounts", headers=headers)
                if final_accounts_response.status_code == 200:
                    final_accounts = final_accounts_response.json()
                    final_account = next((acc for acc in final_accounts if acc.get("id") == account_id), None)
                    
                    if final_account:
                        final_balance = final_account.get("current_balance")
                        expected_balance = initial_balance - pending_transaction["value"]
                        
                        if abs(final_balance - expected_balance) < 0.01:
                            print_test_result("Saldo atualizado após confirmação", True,
                                            f"Saldo atualizado: R$ {initial_balance} → R$ {final_balance}")
                        else:
                            print_test_result("Saldo atualizado após confirmação", False,
                                            f"Esperado: R$ {expected_balance}, Atual: R$ {final_balance}")
            else:
                print_test_result("Confirmação de pagamento", False,
                                f"Status: {confirm_response.status_code}")
                return False
            
            # Test confirming a non-existent or already paid transaction
            invalid_confirm_response = requests.patch(f"{BACKEND_URL}/transactions/{transaction_id}/confirm-payment", 
                                                    headers=headers)
            
            if invalid_confirm_response.status_code == 404:
                print_test_result("Confirmação de transação já paga", True,
                                "Rejeitou confirmação de transação já paga")
            else:
                print_test_result("Confirmação de transação já paga", False,
                                "Não rejeitou confirmação duplicada")
            
            return True
            
        else:
            print_test_result("Criação de transação pendente", False,
                            f"Status: {response.status_code}")
            return False
            
    except Exception as e:
        print_test_result("Gestão de status", False, f"Exceção: {str(e)}")
        return False

def test_transaction_statistics():
    """Test transaction statistics endpoint"""
    print("\n" + "="*80)
    print("TESTANDO ESTATÍSTICAS DE TRANSAÇÕES")
    print("="*80)
    
    if not auth_token:
        print_test_result("Estatísticas de transações", False, "Token não disponível")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        # Test basic statistics endpoint
        response = requests.get(f"{BACKEND_URL}/transactions/statistics", headers=headers)
        
        if response.status_code == 200:
            stats = response.json()
            
            print_test_result("Endpoint de estatísticas", True,
                            "Endpoint respondeu com sucesso")
            
            # Verify response structure
            if "statistics" in stats:
                statistics = stats["statistics"]
                
                print_test_result("Estrutura das estatísticas", True,
                                f"Retornou {len(statistics)} grupos de estatísticas")
                
                # Verify each statistic has required fields
                if len(statistics) > 0:
                    required_fields = ["type", "status", "count", "total_value"]
                    first_stat = statistics[0]
                    missing_fields = [field for field in required_fields if field not in first_stat]
                    
                    if not missing_fields:
                        print_test_result("Campos das estatísticas", True,
                                        "Todos os campos obrigatórios presentes")
                    else:
                        print_test_result("Campos das estatísticas", False,
                                        f"Campos faltando: {missing_fields}")
                    
                    # Display statistics summary
                    for stat in statistics:
                        type_name = stat.get("type")
                        status_name = stat.get("status")
                        count = stat.get("count")
                        total_value = stat.get("total_value")
                        
                        print(f"   {type_name} ({status_name}): {count} transações, R$ {total_value}")
                
                # Test with date range filter
                start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
                end_date = datetime.now().strftime("%Y-%m-%d")
                
                params = {
                    "start_date": start_date,
                    "end_date": end_date
                }
                
                filtered_response = requests.get(f"{BACKEND_URL}/transactions/statistics", 
                                               params=params, headers=headers)
                
                if filtered_response.status_code == 200:
                    filtered_stats = filtered_response.json()
                    print_test_result("Estatísticas com filtro de data", True,
                                    "Filtro por data funcionando")
                else:
                    print_test_result("Estatísticas com filtro de data", False,
                                    f"Status: {filtered_response.status_code}")
                
                return True
            else:
                print_test_result("Estrutura das estatísticas", False,
                                "Campo 'statistics' não encontrado")
                return False
                
        else:
            print_test_result("Endpoint de estatísticas", False,
                            f"Status: {response.status_code}, Erro: {response.text}")
            return False
            
    except Exception as e:
        print_test_result("Estatísticas de transações", False, f"Exceção: {str(e)}")
        return False

def run_advanced_transaction_tests():
    """Run all advanced transaction management tests"""
    print("🇧🇷 TESTANDO SISTEMA AVANÇADO DE GESTÃO DE TRANSAÇÕES")
    print("=" * 80)
    print(f"URL do Backend: {BACKEND_URL}")
    print("=" * 80)
    
    test_results = {}
    
    # Login first
    if not login_test_user():
        print("❌ FALHA NO LOGIN - Abortando testes")
        return {}
    
    # Get test account
    if not get_test_account():
        print("❌ FALHA AO OBTER CONTA DE TESTE - Abortando testes")
        return {}
    
    # Run all tests
    test_results["enhanced_categories"] = test_enhanced_brazilian_categories()
    test_results["intelligent_suggestions"] = test_intelligent_category_suggestion()
    test_results["recent_descriptions"] = test_recent_descriptions_autocomplete()
    test_results["advanced_filtering"] = test_advanced_transaction_filtering()
    test_results["status_management"] = test_transaction_status_management()
    test_results["transaction_statistics"] = test_transaction_statistics()
    
    # Summary
    print("\n" + "="*80)
    print("RESUMO DOS TESTES AVANÇADOS")
    print("="*80)
    
    passed_tests = sum(1 for result in test_results.values() if result)
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASSOU" if result else "❌ FALHOU"
        test_display_name = test_name.replace('_', ' ').title()
        print(f"{status} - {test_display_name}")
    
    print(f"\nResultado Final: {passed_tests}/{total_tests} testes passaram")
    
    if passed_tests == total_tests:
        print("🎉 TODOS OS TESTES AVANÇADOS PASSARAM! Sistema funcionando perfeitamente.")
    elif passed_tests >= total_tests * 0.8:
        print("✅ MAIORIA DOS TESTES PASSOU! Sistema funcionando bem com pequenos ajustes necessários.")
    else:
        print("⚠️  VÁRIOS TESTES FALHARAM. Sistema precisa de ajustes significativos.")
    
    return test_results

if __name__ == "__main__":
    run_advanced_transaction_tests()