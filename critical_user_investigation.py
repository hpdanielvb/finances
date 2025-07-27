#!/usr/bin/env python3
"""
CRITICAL USER DATA INVESTIGATION
Investigating the discrepancies reported by the user for teste.debug@email.com:
1. Categories Issue - Only 8 vs Expected 129
2. Balance Calculation Issue - Negative Total Balance
3. Real user data verification
"""

import requests
import json
from datetime import datetime, timedelta

# Configuration
BACKEND_URL = "https://c8483016-28e3-4c32-82b5-fe040e32c737.preview.emergentagent.com/api"

# Existing user credentials
EXISTING_USER_LOGIN = {
    "email": "teste.debug@email.com", 
    "password": "MinhaSenh@123"
}

# Global variables
auth_token = None
user_id = None

def print_investigation_result(test_name, details=""):
    """Print formatted investigation results"""
    print(f"\n🔍 {test_name}")
    if details:
        print(f"   {details}")

def login_existing_user():
    """Login as the existing user teste.debug@email.com"""
    global auth_token, user_id
    
    print("\n" + "="*80)
    print("🔐 LOGGING IN AS EXISTING USER: teste.debug@email.com")
    print("="*80)
    
    try:
        response = requests.post(f"{BACKEND_URL}/auth/login", json=EXISTING_USER_LOGIN)
        
        if response.status_code == 200:
            data = response.json()
            auth_token = data.get("access_token")
            user_info = data.get("user", {})
            user_id = user_info.get("id")
            
            print_investigation_result("✅ LOGIN SUCCESSFUL", 
                                     f"User: {user_info.get('name')}, ID: {user_id}")
            return True
        else:
            print_investigation_result("❌ LOGIN FAILED", 
                                     f"Status: {response.status_code}, Error: {response.text}")
            return False
            
    except Exception as e:
        print_investigation_result("❌ LOGIN EXCEPTION", f"Error: {str(e)}")
        return False

def investigate_categories_issue():
    """Investigate the categories issue - User reports only 8 vs expected 129"""
    print("\n" + "="*80)
    print("🔍 CRITICAL INVESTIGATION: CATEGORIES ISSUE")
    print("User reports: Only 8 categories visible")
    print("Expected: 129 categories")
    print("="*80)
    
    if not auth_token:
        print_investigation_result("❌ CATEGORIES INVESTIGATION", "No auth token available")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        response = requests.get(f"{BACKEND_URL}/categories", headers=headers)
        
        if response.status_code == 200:
            categories = response.json()
            total_count = len(categories)
            
            print_investigation_result("📊 TOTAL CATEGORIES FOUND", f"{total_count} categories")
            
            # Analyze categories by type
            income_cats = [cat for cat in categories if cat.get("type") == "Receita"]
            expense_cats = [cat for cat in categories if cat.get("type") == "Despesa"]
            
            print_investigation_result("📊 CATEGORIES BY TYPE", 
                                     f"Receitas: {len(income_cats)}, Despesas: {len(expense_cats)}")
            
            # Analyze parent vs child categories
            parent_cats = [cat for cat in categories if cat.get("parent_category_id") is None]
            child_cats = [cat for cat in categories if cat.get("parent_category_id") is not None]
            
            print_investigation_result("📊 CATEGORIES BY STRUCTURE", 
                                     f"Parents: {len(parent_cats)}, Subcategories: {len(child_cats)}")
            
            # Show first 20 categories for analysis
            print_investigation_result("📋 FIRST 20 CATEGORIES", "")
            for i, cat in enumerate(categories[:20]):
                parent_info = f" (child of {cat.get('parent_category_id')})" if cat.get('parent_category_id') else " (parent)"
                print(f"   {i+1:2d}. {cat.get('name')} [{cat.get('type')}]{parent_info}")
            
            if total_count > 20:
                print(f"   ... and {total_count - 20} more categories")
            
            # Check for specific expected categories
            expected_categories = [
                "Salário", "Moradia", "Transporte", "Alimentação", "Saúde",
                "Netflix", "Spotify", "Uber/99/Táxi", "Consultas Médicas"
            ]
            
            category_names = [cat.get("name") for cat in categories]
            found_expected = [cat for cat in expected_categories if cat in category_names]
            missing_expected = [cat for cat in expected_categories if cat not in category_names]
            
            print_investigation_result("🎯 EXPECTED CATEGORIES CHECK", 
                                     f"Found: {found_expected}")
            if missing_expected:
                print_investigation_result("❌ MISSING EXPECTED CATEGORIES", 
                                         f"Missing: {missing_expected}")
            
            # CRITICAL FINDING
            if total_count <= 10:
                print_investigation_result("🚨 CRITICAL ISSUE CONFIRMED", 
                                         f"User report ACCURATE: Only {total_count} categories found vs expected 129")
                return False
            elif total_count < 100:
                print_investigation_result("⚠️ PARTIAL ISSUE CONFIRMED", 
                                         f"Incomplete categories: {total_count}/129 found")
                return False
            else:
                print_investigation_result("✅ CATEGORIES SEEM OK", 
                                         f"Found {total_count} categories - user report may be frontend issue")
                return True
                
        else:
            print_investigation_result("❌ CATEGORIES API ERROR", 
                                     f"Status: {response.status_code}, Error: {response.text}")
            return False
            
    except Exception as e:
        print_investigation_result("❌ CATEGORIES INVESTIGATION EXCEPTION", f"Error: {str(e)}")
        return False

def investigate_balance_issue():
    """Investigate the balance calculation issue - User reports negative total balance"""
    print("\n" + "="*80)
    print("🔍 CRITICAL INVESTIGATION: BALANCE CALCULATION ISSUE")
    print("User reports: 'Saldo Total Consolidado' appears negative from start")
    print("Expected: Should start with initial account balance and subtract expenses")
    print("="*80)
    
    if not auth_token:
        print_investigation_result("❌ BALANCE INVESTIGATION", "No auth token available")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        # Get all accounts
        accounts_response = requests.get(f"{BACKEND_URL}/accounts", headers=headers)
        
        if accounts_response.status_code == 200:
            accounts = accounts_response.json()
            
            print_investigation_result("📊 ACCOUNTS FOUND", f"{len(accounts)} accounts")
            
            total_initial_balance = 0
            total_current_balance = 0
            
            for i, account in enumerate(accounts):
                initial = account.get("initial_balance", 0)
                current = account.get("current_balance", 0)
                total_initial_balance += initial
                total_current_balance += current
                
                print_investigation_result(f"💳 ACCOUNT {i+1}: {account.get('name')}", 
                                         f"Initial: R$ {initial:.2f}, Current: R$ {current:.2f}")
            
            print_investigation_result("💰 TOTAL BALANCES", 
                                     f"Initial: R$ {total_initial_balance:.2f}, Current: R$ {total_current_balance:.2f}")
            
            # Check dashboard summary
            dashboard_response = requests.get(f"{BACKEND_URL}/dashboard/summary", headers=headers)
            
            if dashboard_response.status_code == 200:
                dashboard = dashboard_response.json()
                dashboard_total = dashboard.get("total_balance", 0)
                monthly_income = dashboard.get("monthly_income", 0)
                monthly_expenses = dashboard.get("monthly_expenses", 0)
                monthly_net = dashboard.get("monthly_net", 0)
                
                print_investigation_result("📊 DASHBOARD SUMMARY", 
                                         f"Total Balance: R$ {dashboard_total:.2f}")
                print_investigation_result("📊 MONTHLY SUMMARY", 
                                         f"Income: R$ {monthly_income:.2f}, Expenses: R$ {monthly_expenses:.2f}, Net: R$ {monthly_net:.2f}")
                
                # Check if dashboard total matches account totals
                if abs(dashboard_total - total_current_balance) < 0.01:
                    print_investigation_result("✅ BALANCE CONSISTENCY", 
                                             "Dashboard total matches account totals")
                else:
                    print_investigation_result("❌ BALANCE INCONSISTENCY", 
                                             f"Dashboard: R$ {dashboard_total:.2f} vs Accounts: R$ {total_current_balance:.2f}")
                
                # CRITICAL FINDING
                if dashboard_total < 0:
                    print_investigation_result("🚨 CRITICAL ISSUE CONFIRMED", 
                                             f"User report ACCURATE: Total balance is negative (R$ {dashboard_total:.2f})")
                    return False
                elif total_current_balance < total_initial_balance:
                    print_investigation_result("⚠️ BALANCE DECREASED", 
                                             f"Current balance lower than initial (expenses > income)")
                    return True
                else:
                    print_investigation_result("✅ BALANCE SEEMS OK", 
                                             f"Positive balance: R$ {dashboard_total:.2f}")
                    return True
            else:
                print_investigation_result("❌ DASHBOARD API ERROR", 
                                         f"Status: {dashboard_response.status_code}")
                return False
                
        else:
            print_investigation_result("❌ ACCOUNTS API ERROR", 
                                     f"Status: {accounts_response.status_code}, Error: {accounts_response.text}")
            return False
            
    except Exception as e:
        print_investigation_result("❌ BALANCE INVESTIGATION EXCEPTION", f"Error: {str(e)}")
        return False

def investigate_transactions():
    """Investigate transactions to understand balance calculations"""
    print("\n" + "="*80)
    print("🔍 INVESTIGATING TRANSACTIONS FOR BALANCE VERIFICATION")
    print("="*80)
    
    if not auth_token:
        print_investigation_result("❌ TRANSACTIONS INVESTIGATION", "No auth token available")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        # Get all transactions
        transactions_response = requests.get(f"{BACKEND_URL}/transactions?limit=100", headers=headers)
        
        if transactions_response.status_code == 200:
            transactions = transactions_response.json()
            
            print_investigation_result("📊 TRANSACTIONS FOUND", f"{len(transactions)} transactions")
            
            # Analyze transactions
            income_transactions = [t for t in transactions if t.get("type") == "Receita"]
            expense_transactions = [t for t in transactions if t.get("type") == "Despesa"]
            paid_transactions = [t for t in transactions if t.get("status") == "Pago"]
            pending_transactions = [t for t in transactions if t.get("status") == "Pendente"]
            
            total_income = sum(t.get("value", 0) for t in income_transactions if t.get("status") == "Pago")
            total_expenses = sum(t.get("value", 0) for t in expense_transactions if t.get("status") == "Pago")
            
            print_investigation_result("📊 TRANSACTION ANALYSIS", 
                                     f"Income: {len(income_transactions)}, Expenses: {len(expense_transactions)}")
            print_investigation_result("📊 TRANSACTION STATUS", 
                                     f"Paid: {len(paid_transactions)}, Pending: {len(pending_transactions)}")
            print_investigation_result("💰 TRANSACTION TOTALS", 
                                     f"Total Income: R$ {total_income:.2f}, Total Expenses: R$ {total_expenses:.2f}")
            
            # Show recent transactions
            print_investigation_result("📋 RECENT TRANSACTIONS", "")
            for i, trans in enumerate(transactions[:10]):
                date_str = trans.get("transaction_date", "")[:10]  # Just the date part
                print(f"   {i+1:2d}. {date_str} | {trans.get('type'):8s} | R$ {trans.get('value'):8.2f} | {trans.get('status'):8s} | {trans.get('description')}")
            
            if len(transactions) > 10:
                print(f"   ... and {len(transactions) - 10} more transactions")
            
            return True
            
        else:
            print_investigation_result("❌ TRANSACTIONS API ERROR", 
                                     f"Status: {transactions_response.status_code}, Error: {transactions_response.text}")
            return False
            
    except Exception as e:
        print_investigation_result("❌ TRANSACTIONS INVESTIGATION EXCEPTION", f"Error: {str(e)}")
        return False

def run_critical_investigation():
    """Run the complete critical investigation"""
    print("🚨 CRITICAL USER DATA INVESTIGATION")
    print("=" * 80)
    print("Investigating discrepancies reported by user for teste.debug@email.com")
    print("=" * 80)
    
    # Step 1: Login
    if not login_existing_user():
        print("\n❌ INVESTIGATION FAILED: Cannot login as existing user")
        return
    
    # Step 2: Investigate categories issue
    categories_ok = investigate_categories_issue()
    
    # Step 3: Investigate balance issue
    balance_ok = investigate_balance_issue()
    
    # Step 4: Investigate transactions
    investigate_transactions()
    
    # Final summary
    print("\n" + "="*80)
    print("📊 CRITICAL INVESTIGATION SUMMARY")
    print("="*80)
    
    if not categories_ok:
        print("🚨 CATEGORIES ISSUE: CONFIRMED - User report is accurate")
        print("   - User sees limited categories (likely < 20)")
        print("   - Expected 129 categories not available")
        print("   - Root cause: Category creation function not working properly for this user")
    else:
        print("✅ CATEGORIES ISSUE: NOT CONFIRMED - Categories seem adequate")
        print("   - May be a frontend display issue")
    
    if not balance_ok:
        print("🚨 BALANCE ISSUE: CONFIRMED - User report is accurate")
        print("   - Total balance appears negative or incorrect")
        print("   - Balance calculation logic has issues")
    else:
        print("✅ BALANCE ISSUE: NOT CONFIRMED - Balance calculations seem correct")
        print("   - May be a frontend display issue")
    
    print("\n🔍 RECOMMENDED ACTIONS:")
    if not categories_ok:
        print("   1. Fix category creation for existing users")
        print("   2. Run category migration for teste.debug@email.com")
    if not balance_ok:
        print("   3. Review balance calculation logic")
        print("   4. Check transaction status handling")
    
    print("   5. Test frontend category loading")
    print("   6. Test frontend balance display")

if __name__ == "__main__":
    run_critical_investigation()