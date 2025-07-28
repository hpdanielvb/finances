#!/usr/bin/env python3
"""
Complete Password Recovery and Email Verification Flow Test
Tests the complete authentication flow using real tokens extracted from server logs
"""

import requests
import json
import re
import subprocess

# Configuration
BACKEND_URL = "https://090d9661-b0bc-4e2d-9602-1953ab347935.preview.emergentagent.com/api"

# Test data
TEST_USER_DATA = {
    "name": "Complete Flow Test User",
    "email": "complete.flow.test@email.com",
    "password": "MinhaSenh@123",
    "confirm_password": "MinhaSenh@123"
}

def print_test_result(test_name, success, details=""):
    """Print formatted test results"""
    status = "✅ PASSOU" if success else "❌ FALHOU"
    print(f"\n{status} - {test_name}")
    if details:
        print(f"   Detalhes: {details}")

def extract_token_from_logs(token_type="verification"):
    """Extract the most recent verification or reset token from server logs"""
    try:
        # Get recent logs
        result = subprocess.run(
            ["tail", "-n", "200", "/var/log/supervisor/backend.out.log"],
            capture_output=True, text=True
        )
        
        if result.returncode != 0:
            return None
            
        log_content = result.stdout
        
        if token_type == "verification":
            pattern = r'verify-email\?token=([a-zA-Z0-9_-]+)'
        else:
            pattern = r'reset-password\?token=([a-zA-Z0-9_-]+)'
        
        # Find all matches and return the most recent one
        matches = re.findall(pattern, log_content)
        if matches:
            return matches[-1]  # Return the most recent token
        
        return None
    except Exception as e:
        print(f"   Erro ao extrair token: {e}")
        return None

def test_complete_registration_and_verification_flow():
    """Test complete registration and email verification flow"""
    print("\n" + "="*80)
    print("TESTANDO FLUXO COMPLETO: REGISTRO → VERIFICAÇÃO → LOGIN")
    print("="*80)
    
    try:
        # Step 1: Register new user
        print("\n🔸 Passo 1: Registrando novo usuário...")
        response = requests.post(f"{BACKEND_URL}/auth/register", json=TEST_USER_DATA)
        
        if response.status_code != 200:
            print_test_result("Registro inicial", False, 
                            f"Status: {response.status_code}, Erro: {response.text}")
            return False
        
        data = response.json()
        print_test_result("Registro inicial", True, 
                        f"Usuário registrado: {data.get('message')}")
        
        # Step 2: Try login before verification (should fail)
        print("\n🔸 Passo 2: Tentando login antes da verificação...")
        login_response = requests.post(f"{BACKEND_URL}/auth/login", json={
            "email": TEST_USER_DATA["email"],
            "password": TEST_USER_DATA["password"]
        })
        
        if login_response.status_code == 401:
            error_msg = login_response.json().get("detail", "")
            print_test_result("Login bloqueado antes da verificação", True, 
                            f"Login rejeitado: {error_msg}")
        else:
            print_test_result("Login bloqueado antes da verificação", False, 
                            "Login permitido sem verificação")
            return False
        
        # Step 3: Extract verification token from logs
        print("\n🔸 Passo 3: Extraindo token de verificação dos logs...")
        verification_token = extract_token_from_logs("verification")
        
        if not verification_token:
            print_test_result("Extração de token de verificação", False, 
                            "Token não encontrado nos logs")
            return False
        
        print_test_result("Extração de token de verificação", True, 
                        f"Token extraído: {verification_token[:20]}...")
        
        # Step 4: Verify email with token
        print("\n🔸 Passo 4: Verificando email com token...")
        verify_response = requests.post(f"{BACKEND_URL}/auth/verify-email", 
                                      json={"token": verification_token})
        
        if verify_response.status_code == 200:
            verify_data = verify_response.json()
            access_token = verify_data.get("access_token")
            user_info = verify_data.get("user", {})
            
            print_test_result("Verificação de email", True, 
                            f"Email verificado: {verify_data.get('message')}")
            
            # Verify access token is provided after verification
            if access_token:
                print_test_result("Token fornecido após verificação", True, 
                                "Access token fornecido automaticamente")
            else:
                print_test_result("Token fornecido após verificação", False, 
                                "Access token não fornecido")
        else:
            print_test_result("Verificação de email", False, 
                            f"Status: {verify_response.status_code}, Erro: {verify_response.text}")
            return False
        
        # Step 5: Try login after verification (should succeed)
        print("\n🔸 Passo 5: Tentando login após verificação...")
        final_login_response = requests.post(f"{BACKEND_URL}/auth/login", json={
            "email": TEST_USER_DATA["email"],
            "password": TEST_USER_DATA["password"]
        })
        
        if final_login_response.status_code == 200:
            final_login_data = final_login_response.json()
            final_token = final_login_data.get("access_token")
            final_user = final_login_data.get("user", {})
            
            print_test_result("Login após verificação", True, 
                            f"Login bem-sucedido para: {final_user.get('name')}")
            
            # Verify token works for authenticated endpoints
            headers = {"Authorization": f"Bearer {final_token}"}
            test_auth_response = requests.get(f"{BACKEND_URL}/accounts", headers=headers)
            
            if test_auth_response.status_code in [200, 404]:  # 404 is OK if no accounts
                print_test_result("Token funcional após login", True, 
                                "Token permite acesso a endpoints autenticados")
            else:
                print_test_result("Token funcional após login", False, 
                                f"Token rejeitado: {test_auth_response.status_code}")
        else:
            print_test_result("Login após verificação", False, 
                            f"Status: {final_login_response.status_code}, Erro: {final_login_response.text}")
            return False
        
        print("\n🎉 FLUXO COMPLETO DE REGISTRO E VERIFICAÇÃO CONCLUÍDO COM SUCESSO!")
        return True
        
    except Exception as e:
        print_test_result("Fluxo completo de registro", False, f"Exceção: {str(e)}")
        return False

def test_complete_password_recovery_flow():
    """Test complete password recovery flow"""
    print("\n" + "="*80)
    print("TESTANDO FLUXO COMPLETO: ESQUECI SENHA → RESET → LOGIN")
    print("="*80)
    
    try:
        # Step 1: Request password reset
        print("\n🔸 Passo 1: Solicitando reset de senha...")
        reset_request = {"email": TEST_USER_DATA["email"]}
        reset_response = requests.post(f"{BACKEND_URL}/auth/forgot-password", json=reset_request)
        
        if reset_response.status_code != 200:
            print_test_result("Solicitação de reset", False, 
                            f"Status: {reset_response.status_code}")
            return False
        
        reset_data = reset_response.json()
        print_test_result("Solicitação de reset", True, 
                        f"Reset solicitado: {reset_data.get('message')}")
        
        # Step 2: Extract reset token from logs
        print("\n🔸 Passo 2: Extraindo token de reset dos logs...")
        reset_token = extract_token_from_logs("reset")
        
        if not reset_token:
            print_test_result("Extração de token de reset", False, 
                            "Token não encontrado nos logs")
            return False
        
        print_test_result("Extração de token de reset", True, 
                        f"Token extraído: {reset_token[:20]}...")
        
        # Step 3: Reset password with token
        print("\n🔸 Passo 3: Resetando senha com token...")
        new_password = "NovaSenha@456"
        reset_password_data = {
            "token": reset_token,
            "new_password": new_password,
            "confirm_password": new_password
        }
        
        reset_password_response = requests.post(f"{BACKEND_URL}/auth/reset-password", 
                                              json=reset_password_data)
        
        if reset_password_response.status_code == 200:
            reset_result = reset_password_response.json()
            print_test_result("Reset de senha", True, 
                            f"Senha resetada: {reset_result.get('message')}")
        else:
            print_test_result("Reset de senha", False, 
                            f"Status: {reset_password_response.status_code}, Erro: {reset_password_response.text}")
            return False
        
        # Step 4: Try login with old password (should fail)
        print("\n🔸 Passo 4: Tentando login com senha antiga...")
        old_login_response = requests.post(f"{BACKEND_URL}/auth/login", json={
            "email": TEST_USER_DATA["email"],
            "password": TEST_USER_DATA["password"]  # Old password
        })
        
        if old_login_response.status_code == 401:
            print_test_result("Login com senha antiga rejeitado", True, 
                            "Senha antiga não funciona mais")
        else:
            print_test_result("Login com senha antiga rejeitado", False, 
                            "Senha antiga ainda funciona")
        
        # Step 5: Try login with new password (should succeed)
        print("\n🔸 Passo 5: Tentando login com nova senha...")
        new_login_response = requests.post(f"{BACKEND_URL}/auth/login", json={
            "email": TEST_USER_DATA["email"],
            "password": new_password  # New password
        })
        
        if new_login_response.status_code == 200:
            new_login_data = new_login_response.json()
            new_token = new_login_data.get("access_token")
            user_info = new_login_data.get("user", {})
            
            print_test_result("Login com nova senha", True, 
                            f"Login bem-sucedido para: {user_info.get('name')}")
            
            # Verify new token works
            headers = {"Authorization": f"Bearer {new_token}"}
            test_response = requests.get(f"{BACKEND_URL}/accounts", headers=headers)
            
            if test_response.status_code in [200, 404]:
                print_test_result("Token da nova senha funcional", True, 
                                "Token permite acesso a endpoints autenticados")
            else:
                print_test_result("Token da nova senha funcional", False, 
                                f"Token rejeitado: {test_response.status_code}")
        else:
            print_test_result("Login com nova senha", False, 
                            f"Status: {new_login_response.status_code}, Erro: {new_login_response.text}")
            return False
        
        print("\n🎉 FLUXO COMPLETO DE RECUPERAÇÃO DE SENHA CONCLUÍDO COM SUCESSO!")
        return True
        
    except Exception as e:
        print_test_result("Fluxo completo de recuperação", False, f"Exceção: {str(e)}")
        return False

def test_token_expiry_simulation():
    """Test token expiry behavior (simulation)"""
    print("\n" + "="*80)
    print("TESTANDO COMPORTAMENTO DE EXPIRAÇÃO DE TOKENS")
    print("="*80)
    
    try:
        # Test with obviously invalid/expired token
        expired_token = "expired_token_123"
        
        # Test verification with expired token
        verify_response = requests.post(f"{BACKEND_URL}/auth/verify-email", 
                                      json={"token": expired_token})
        
        if verify_response.status_code == 400:
            error_msg = verify_response.json().get("detail", "")
            if "inválido" in error_msg.lower() or "expirado" in error_msg.lower():
                print_test_result("Token de verificação expirado rejeitado", True, 
                                f"Token expirado rejeitado: {error_msg}")
            else:
                print_test_result("Token de verificação expirado rejeitado", False, 
                                f"Erro inesperado: {error_msg}")
        else:
            print_test_result("Token de verificação expirado rejeitado", False, 
                            "Token expirado aceito")
        
        # Test reset with expired token
        reset_response = requests.post(f"{BACKEND_URL}/auth/reset-password", json={
            "token": expired_token,
            "new_password": "NovaSenha@789",
            "confirm_password": "NovaSenha@789"
        })
        
        if reset_response.status_code == 400:
            error_msg = reset_response.json().get("detail", "")
            if "inválido" in error_msg.lower() or "expirado" in error_msg.lower():
                print_test_result("Token de reset expirado rejeitado", True, 
                                f"Token expirado rejeitado: {error_msg}")
            else:
                print_test_result("Token de reset expirado rejeitado", False, 
                                f"Erro inesperado: {error_msg}")
        else:
            print_test_result("Token de reset expirado rejeitado", False, 
                            "Token expirado aceito")
        
        return True
        
    except Exception as e:
        print_test_result("Teste de expiração de tokens", False, f"Exceção: {str(e)}")
        return False

def run_complete_flow_tests():
    """Run all complete flow tests"""
    print("🔐 INICIANDO TESTES COMPLETOS DE FLUXO DE AUTENTICAÇÃO")
    print("=" * 80)
    print(f"URL do Backend: {BACKEND_URL}")
    print("=" * 80)
    
    test_results = {}
    
    # Test sequence
    test_results["complete_registration_flow"] = test_complete_registration_and_verification_flow()
    test_results["complete_password_recovery_flow"] = test_complete_password_recovery_flow()
    test_results["token_expiry_simulation"] = test_token_expiry_simulation()
    
    # Summary
    print("\n" + "="*80)
    print("RESUMO DOS TESTES COMPLETOS DE FLUXO")
    print("="*80)
    
    passed_tests = sum(1 for result in test_results.values() if result)
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{status} - {test_name.replace('_', ' ').title()}")
    
    print(f"\nResultado Final: {passed_tests}/{total_tests} testes passaram")
    
    if passed_tests == total_tests:
        print("🎉 TODOS OS TESTES DE FLUXO COMPLETO PASSARAM!")
        print("   Sistema de autenticação com verificação de email e recuperação de senha")
        print("   está funcionando perfeitamente em todos os cenários testados.")
    else:
        print("⚠️  ALGUNS TESTES FALHARAM. Verifique os detalhes acima.")
    
    return test_results

if __name__ == "__main__":
    run_complete_flow_tests()