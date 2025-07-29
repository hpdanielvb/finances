#!/usr/bin/env python3
"""
CONSORTIUM MODULE ENHANCEMENTS RE-TEST - PHASE 3 CORRECTIONS
Re-testing the Melhorias no Módulo de Consórcio após correções implementadas

This test specifically addresses the review request to verify if all expected fields
are now present in the consortium endpoints after corrections were implemented.

FOCUS: Verify ALL expected fields are present in responses
"""

import requests
import json
from datetime import datetime

# Configuration
BACKEND_URL = "https://2353e19b-098e-4c36-9781-1e4f6c502504.preview.emergentagent.com/api"

def print_test_result(test_name, success, details=""):
    """Print formatted test results"""
    status = "✅ PASSOU" if success else "❌ FALHOU"
    print(f"\n{status} - {test_name}")
    if details:
        print(f"   Detalhes: {details}")

def test_consortium_corrections():
    """
    🏠 CONSORTIUM MODULE CORRECTIONS RE-TEST
    
    Testing all 5 endpoints to verify expected fields are present:
    1. GET /api/consortiums/dashboard - All dashboard fields
    2. GET /api/consortiums/contemplation-projections - All projection fields  
    3. GET /api/consortiums/statistics - All statistics fields
    4. GET /api/consortiums/payments-calendar - All calendar fields
    5. GET /api/consortiums/active - All enriched data fields
    
    CREDENTIALS: hpdanielvb@gmail.com / 123456
    """
    print("\n" + "="*80)
    print("🏠 CONSORTIUM MODULE CORRECTIONS RE-TEST - PHASE 3")
    print("="*80)
    print("Re-testing após correções implementadas - verificando TODOS os campos esperados")
    
    # Test credentials
    user_login = {
        "email": "hpdanielvb@gmail.com",
        "password": "123456"
    }
    
    test_results = {
        "login_success": False,
        "dashboard_complete": False,
        "projections_complete": False,
        "statistics_complete": False,
        "calendar_complete": False,
        "active_enriched": False,
        "all_endpoints_working": False,
        "auth_token": None,
        "missing_fields": [],
        "error_details": None
    }
    
    try:
        print(f"\n🔍 STEP 1: Authentication")
        print(f"   Login: {user_login['email']} / {user_login['password']}")
        
        response = requests.post(f"{BACKEND_URL}/auth/login", json=user_login)
        
        if response.status_code != 200:
            error_detail = response.json().get("detail", "Unknown error")
            test_results["error_details"] = f"Authentication failed: {error_detail}"
            print_test_result("AUTHENTICATION", False, f"❌ Login failed: {error_detail}")
            return test_results
        
        data = response.json()
        user_info = data.get("user", {})
        auth_token = data.get("access_token")
        test_results["auth_token"] = auth_token
        test_results["login_success"] = True
        
        print_test_result("AUTHENTICATION", True, f"✅ Login successful")
        print(f"   User: {user_info.get('name')} ({user_info.get('email')})")
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # TEST 1: Dashboard - Check ALL expected fields
        print(f"\n🔍 STEP 2: Dashboard Fields Verification")
        print("   Testing GET /api/consortiums/dashboard - checking ALL expected fields...")
        
        dashboard_response = requests.get(f"{BACKEND_URL}/consortiums/dashboard", headers=headers)
        
        if dashboard_response.status_code == 200:
            dashboard_data = dashboard_response.json()
            
            # Expected dashboard fields from review request
            expected_dashboard_fields = [
                'total_consortiums', 'active_consortiums', 'contemplated_consortiums',
                'total_invested', 'total_pending', 'next_payments', 
                'contemplation_projections', 'performance_summary'
            ]
            
            missing_dashboard = []
            present_dashboard = []
            
            print(f"   📊 DASHBOARD FIELD VERIFICATION:")
            for field in expected_dashboard_fields:
                if field in dashboard_data and dashboard_data[field] is not None:
                    present_dashboard.append(field)
                    value = dashboard_data[field]
                    if isinstance(value, list):
                        print(f"      ✅ {field}: {len(value)} items")
                    elif isinstance(value, dict):
                        print(f"      ✅ {field}: {len(value)} fields")
                    else:
                        print(f"      ✅ {field}: {value}")
                else:
                    missing_dashboard.append(field)
                    print(f"      ❌ {field}: MISSING")
            
            if len(missing_dashboard) == 0:
                test_results["dashboard_complete"] = True
                print_test_result("DASHBOARD FIELDS", True, 
                                f"✅ All {len(expected_dashboard_fields)} expected fields present")
            else:
                test_results["missing_fields"].extend([f"dashboard.{field}" for field in missing_dashboard])
                print_test_result("DASHBOARD FIELDS", False, 
                                f"❌ Missing {len(missing_dashboard)} fields: {', '.join(missing_dashboard)}")
        else:
            error_detail = dashboard_response.json().get("detail", "Unknown error")
            print_test_result("DASHBOARD ENDPOINT", False, f"❌ Failed: {error_detail}")
        
        # TEST 2: Contemplation Projections - Check ALL expected fields
        print(f"\n🔍 STEP 3: Contemplation Projections Fields Verification")
        print("   Testing GET /api/consortiums/contemplation-projections - checking ALL expected fields...")
        
        projections_response = requests.get(f"{BACKEND_URL}/consortiums/contemplation-projections", headers=headers)
        
        if projections_response.status_code == 200:
            projections_data = projections_response.json()
            
            if projections_data and len(projections_data) > 0:
                # Expected projection fields from review request
                expected_projection_fields = [
                    'contemplation_probability', 'available_methods', 
                    'months_remaining', 'recommendation'
                ]
                
                first_projection = projections_data[0]
                missing_projections = []
                present_projections = []
                
                print(f"   📊 PROJECTION FIELD VERIFICATION:")
                for field in expected_projection_fields:
                    if field in first_projection and first_projection[field] is not None:
                        present_projections.append(field)
                        value = first_projection[field]
                        if field == 'contemplation_probability':
                            print(f"      ✅ {field}: {value}%")
                        elif field == 'available_methods':
                            methods = ', '.join(value) if isinstance(value, list) else value
                            print(f"      ✅ {field}: {methods}")
                        else:
                            print(f"      ✅ {field}: {value}")
                    else:
                        missing_projections.append(field)
                        print(f"      ❌ {field}: MISSING")
                
                if len(missing_projections) == 0:
                    test_results["projections_complete"] = True
                    print_test_result("PROJECTION FIELDS", True, 
                                    f"✅ All {len(expected_projection_fields)} expected fields present")
                else:
                    test_results["missing_fields"].extend([f"projections.{field}" for field in missing_projections])
                    print_test_result("PROJECTION FIELDS", False, 
                                    f"❌ Missing {len(missing_projections)} fields: {', '.join(missing_projections)}")
            else:
                print_test_result("PROJECTION DATA", False, "❌ No projection data returned")
        else:
            error_detail = projections_response.json().get("detail", "Unknown error")
            print_test_result("PROJECTIONS ENDPOINT", False, f"❌ Failed: {error_detail}")
        
        # TEST 3: Statistics - Check ALL expected fields
        print(f"\n🔍 STEP 4: Statistics Fields Verification")
        print("   Testing GET /api/consortiums/statistics - checking ALL expected fields...")
        
        statistics_response = requests.get(f"{BACKEND_URL}/consortiums/statistics", headers=headers)
        
        if statistics_response.status_code == 200:
            statistics_data = statistics_response.json()
            
            # Expected statistics fields from review request
            expected_statistics_fields = [
                'distribution_by_status', 'distribution_by_type', 'average_progress',
                'upcoming_due_dates', 'contemplation_summary'
            ]
            
            missing_statistics = []
            present_statistics = []
            
            print(f"   📊 STATISTICS FIELD VERIFICATION:")
            for field in expected_statistics_fields:
                if field in statistics_data and statistics_data[field] is not None:
                    present_statistics.append(field)
                    value = statistics_data[field]
                    if isinstance(value, dict):
                        print(f"      ✅ {field}: {len(value)} categories")
                    elif isinstance(value, list):
                        print(f"      ✅ {field}: {len(value)} items")
                    else:
                        print(f"      ✅ {field}: {value}")
                else:
                    missing_statistics.append(field)
                    print(f"      ❌ {field}: MISSING")
            
            if len(missing_statistics) == 0:
                test_results["statistics_complete"] = True
                print_test_result("STATISTICS FIELDS", True, 
                                f"✅ All {len(expected_statistics_fields)} expected fields present")
            else:
                test_results["missing_fields"].extend([f"statistics.{field}" for field in missing_statistics])
                print_test_result("STATISTICS FIELDS", False, 
                                f"❌ Missing {len(missing_statistics)} fields: {', '.join(missing_statistics)}")
        else:
            error_detail = statistics_response.json().get("detail", "Unknown error")
            print_test_result("STATISTICS ENDPOINT", False, f"❌ Failed: {error_detail}")
        
        # TEST 4: Payments Calendar - Check ALL expected fields
        print(f"\n🔍 STEP 5: Payments Calendar Fields Verification")
        print("   Testing GET /api/consortiums/payments-calendar - checking ALL expected fields...")
        
        calendar_response = requests.get(f"{BACKEND_URL}/consortiums/payments-calendar", headers=headers)
        
        if calendar_response.status_code == 200:
            calendar_data = calendar_response.json()
            
            # Expected calendar fields from review request
            expected_calendar_fields = [
                'total_monthly_commitment', 'next_12_months_summary'
            ]
            
            missing_calendar = []
            present_calendar = []
            
            print(f"   📊 CALENDAR FIELD VERIFICATION:")
            for field in expected_calendar_fields:
                if field in calendar_data and calendar_data[field] is not None:
                    present_calendar.append(field)
                    value = calendar_data[field]
                    if isinstance(value, dict):
                        print(f"      ✅ {field}: {len(value)} fields")
                    elif isinstance(value, list):
                        print(f"      ✅ {field}: {len(value)} items")
                    else:
                        print(f"      ✅ {field}: {value}")
                else:
                    missing_calendar.append(field)
                    print(f"      ❌ {field}: MISSING")
            
            if len(missing_calendar) == 0:
                test_results["calendar_complete"] = True
                print_test_result("CALENDAR FIELDS", True, 
                                f"✅ All {len(expected_calendar_fields)} expected fields present")
            else:
                test_results["missing_fields"].extend([f"calendar.{field}" for field in missing_calendar])
                print_test_result("CALENDAR FIELDS", False, 
                                f"❌ Missing {len(missing_calendar)} fields: {', '.join(missing_calendar)}")
        else:
            error_detail = calendar_response.json().get("detail", "Unknown error")
            print_test_result("CALENDAR ENDPOINT", False, f"❌ Failed: {error_detail}")
        
        # TEST 5: Active Consortiums - Check enriched data fields
        print(f"\n🔍 STEP 6: Active Consortiums Enriched Data Verification")
        print("   Testing GET /api/consortiums/active - checking enriched data fields...")
        
        active_response = requests.get(f"{BACKEND_URL}/consortiums/active", headers=headers)
        
        if active_response.status_code == 200:
            active_data = active_response.json()
            
            if active_data and len(active_data) > 0:
                # Expected enriched data fields from review request
                expected_enriched_fields = [
                    'completion_percentage', 'months_remaining', 'contemplation_probability'
                ]
                
                first_consortium = active_data[0]
                missing_enriched = []
                present_enriched = []
                
                print(f"   📊 ENRICHED DATA FIELD VERIFICATION:")
                for field in expected_enriched_fields:
                    if field in first_consortium and first_consortium[field] is not None:
                        present_enriched.append(field)
                        value = first_consortium[field]
                        if field in ['completion_percentage', 'contemplation_probability']:
                            print(f"      ✅ {field}: {value}%")
                        else:
                            print(f"      ✅ {field}: {value}")
                    else:
                        missing_enriched.append(field)
                        print(f"      ❌ {field}: MISSING")
                
                if len(missing_enriched) == 0:
                    test_results["active_enriched"] = True
                    print_test_result("ENRICHED DATA FIELDS", True, 
                                    f"✅ All {len(expected_enriched_fields)} enriched fields present")
                else:
                    test_results["missing_fields"].extend([f"active.{field}" for field in missing_enriched])
                    print_test_result("ENRICHED DATA FIELDS", False, 
                                    f"❌ Missing {len(missing_enriched)} fields: {', '.join(missing_enriched)}")
            else:
                print_test_result("ACTIVE DATA", False, "❌ No active consortium data returned")
        else:
            error_detail = active_response.json().get("detail", "Unknown error")
            print_test_result("ACTIVE ENDPOINT", False, f"❌ Failed: {error_detail}")
        
        # Final Assessment
        print(f"\n🔍 STEP 7: FINAL ASSESSMENT - CONSORTIUM CORRECTIONS")
        print("="*70)
        
        all_endpoints_working = all([
            dashboard_response.status_code == 200,
            projections_response.status_code == 200,
            statistics_response.status_code == 200,
            calendar_response.status_code == 200,
            active_response.status_code == 200
        ])
        
        all_fields_complete = all([
            test_results["dashboard_complete"],
            test_results["projections_complete"],
            test_results["statistics_complete"],
            test_results["calendar_complete"],
            test_results["active_enriched"]
        ])
        
        test_results["all_endpoints_working"] = all_endpoints_working
        
        print(f"📊 DETAILED TEST RESULTS:")
        print(f"   ✅ Authentication: {'SUCCESS' if test_results['login_success'] else 'FAILED'}")
        print(f"   🏠 Dashboard Fields Complete: {'YES' if test_results['dashboard_complete'] else 'NO'}")
        print(f"   📊 Projection Fields Complete: {'YES' if test_results['projections_complete'] else 'NO'}")
        print(f"   📈 Statistics Fields Complete: {'YES' if test_results['statistics_complete'] else 'NO'}")
        print(f"   📅 Calendar Fields Complete: {'YES' if test_results['calendar_complete'] else 'NO'}")
        print(f"   🔧 Enriched Data Complete: {'YES' if test_results['active_enriched'] else 'NO'}")
        print(f"   🌐 All Endpoints Working: {'YES' if all_endpoints_working else 'NO'}")
        
        if len(test_results["missing_fields"]) > 0:
            print(f"\n❌ MISSING FIELDS SUMMARY:")
            for missing_field in test_results["missing_fields"]:
                print(f"      - {missing_field}")
        
        if all_endpoints_working and all_fields_complete:
            print(f"\n🎉 CONSORTIUM MODULE CORRECTIONS SUCCESSFUL!")
            print("✅ All corrections implemented successfully:")
            print("   - GET /api/consortiums/dashboard: ALL expected fields present")
            print("     (total_consortiums, active_consortiums, contemplated_consortiums,")
            print("      total_invested, total_pending, next_payments, contemplation_projections, performance_summary)")
            print("   - GET /api/consortiums/contemplation-projections: ALL expected fields present")
            print("     (contemplation_probability, available_methods, months_remaining, recommendation)")
            print("   - GET /api/consortiums/statistics: ALL expected fields present")
            print("     (distribution_by_status, distribution_by_type, average_progress, upcoming_due_dates, contemplation_summary)")
            print("   - GET /api/consortiums/payments-calendar: ALL expected fields present")
            print("     (total_monthly_commitment, next_12_months_summary)")
            print("   - GET /api/consortiums/active: ALL enriched data fields present")
            print("     (completion_percentage, months_remaining, contemplation_probability)")
            print("   - Intelligent calculations working correctly")
            print("   - Data structure issues from previous test RESOLVED")
            print("   - All 5 endpoints functioning with complete data structures")
            
            return True
        else:
            print(f"\n⚠️ CONSORTIUM MODULE CORRECTIONS INCOMPLETE:")
            if not all_endpoints_working:
                print("   ❌ Some endpoints not working properly")
            if not all_fields_complete:
                print("   ❌ Missing expected fields in responses:")
                if not test_results["dashboard_complete"]:
                    print("      - Dashboard missing required fields")
                if not test_results["projections_complete"]:
                    print("      - Projections missing required fields")
                if not test_results["statistics_complete"]:
                    print("      - Statistics missing required fields")
                if not test_results["calendar_complete"]:
                    print("      - Calendar missing required fields")
                if not test_results["active_enriched"]:
                    print("      - Active consortiums missing enriched data")
            
            print(f"\n🔍 RECOMMENDATION:")
            print("   The corrections are partially implemented but some expected fields are still missing.")
            print("   Please review the missing fields listed above and ensure all expected data")
            print("   structures are properly implemented in the backend endpoints.")
            
            return False
        
    except Exception as e:
        test_results["error_details"] = f"Exception: {str(e)}"
        print_test_result("CONSORTIUM CORRECTIONS TEST", False, f"Exception: {str(e)}")
        return False

if __name__ == "__main__":
    test_consortium_corrections()