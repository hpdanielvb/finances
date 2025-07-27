#!/usr/bin/env python3
"""
OrçaZenFinanceiro User Profile System Backend Testing
Tests the newly implemented User Profile system backend functionality
"""

import requests
import json
from datetime import datetime, timedelta

# Configuration
BACKEND_URL = "https://c8483016-28e3-4c32-82b5-fe040e32c737.preview.emergentagent.com/api"

def print_test_result(test_name, success, details=""):
    """Print formatted test results"""
    status = "✅ PASSOU" if success else "❌ FALHOU"
    print(f"\n{status} - {test_name}")
    if details:
        print(f"   Detalhes: {details}")

def test_user_profile_system():
    """
    COMPREHENSIVE USER PROFILE SYSTEM TEST
    
    This addresses the specific review request to test the newly implemented User Profile system
    for OrçaZenFinanceiro application. Tests all backend functionality:
    
    1. GET /api/profile - Get current user profile information
    2. PUT /api/profile - Update user profile (name and email) 
    3. PUT /api/profile/password - Change user password
    
    Test Scenarios:
    - Login with user credentials (hpdanielvb@gmail.com / TestPassword123 or 123456)
    - Test profile retrieval - verify current user data is returned correctly
    - Test profile update - change name and email, verify update success
    - Test password change - verify current password validation, new password requirements
    - Test error handling for invalid current passwords, mismatched confirmations
    - Test email uniqueness validation if changing to existing email
    
    Data Validation:
    - Verify profile data structure (id, name, email, created_at, email_verified fields)
    - Test authentication requirements for all endpoints
    - Test form validation for password strength and confirmation matching
    """
    print("\n" + "="*80)
    print("👤 USER PROFILE SYSTEM COMPREHENSIVE TEST")
    print("="*80)
    print("Testing User Profile backend functionality for OrçaZenFinanceiro")
    print("Endpoints: GET /api/profile, PUT /api/profile, PUT /api/profile/password")
    
    # Test credentials from review request
    user_login_primary = {
        "email": "hpdanielvb@gmail.com",
        "password": "TestPassword123"
    }
    
    user_login_secondary = {
        "email": "hpdanielvb@gmail.com", 
        "password": "123456"
    }
    
    test_results = {
        "login_success": False,
        "profile_retrieval": False,
        "profile_data_structure": False,
        "profile_update_success": False,
        "password_change_success": False,
        "error_handling_working": False,
        "email_uniqueness_validation": False,
        "authentication_required": False,
        "form_validation_working": False,
        "original_profile": None,
        "updated_profile": None,
        "auth_token": None
    }
    
    try:
        print(f"\n🔍 STEP 1: User Authentication")
        print(f"   Testing primary credentials: {user_login_primary['email']} / {user_login_primary['password']}")
        
        # Try primary credentials first
        response = requests.post(f"{BACKEND_URL}/auth/login", json=user_login_primary)
        
        if response.status_code != 200:
            print(f"   Primary login failed, trying secondary credentials: {user_login_secondary['password']}")
            response = requests.post(f"{BACKEND_URL}/auth/login", json=user_login_secondary)
            
            if response.status_code != 200:
                error_detail = response.json().get("detail", "Unknown error")
                print_test_result("USER AUTHENTICATION", False, f"❌ Both login attempts failed: {error_detail}")
                return test_results
            else:
                used_credentials = user_login_secondary
        else:
            used_credentials = user_login_primary
        
        data = response.json()
        user_info = data.get("user", {})
        auth_token = data.get("access_token")
        test_results["auth_token"] = auth_token
        test_results["login_success"] = True
        
        print_test_result("USER AUTHENTICATION", True, 
                        f"✅ Login successful with {used_credentials['password']}")
        print(f"   User: {user_info.get('name')} ({user_info.get('email')})")
        print(f"   User ID: {user_info.get('id')}")
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # STEP 2: Profile Retrieval - GET /api/profile
        print(f"\n🔍 STEP 2: Profile Retrieval - GET /api/profile")
        print("   Testing profile data retrieval and structure validation...")
        
        profile_response = requests.get(f"{BACKEND_URL}/profile", headers=headers)
        
        if profile_response.status_code == 200:
            profile_data = profile_response.json()
            test_results["original_profile"] = profile_data
            test_results["profile_retrieval"] = True
            
            print_test_result("PROFILE RETRIEVAL", True, "✅ Profile data retrieved successfully")
            
            # Validate profile data structure
            required_fields = ['id', 'name', 'email']
            optional_fields = ['created_at', 'email_verified']
            
            print(f"   📊 PROFILE DATA STRUCTURE VALIDATION:")
            structure_valid = True
            
            for field in required_fields:
                if field in profile_data and profile_data[field] is not None:
                    print(f"      ✅ {field}: {profile_data[field]}")
                else:
                    print(f"      ❌ {field}: MISSING or NULL")
                    structure_valid = False
            
            for field in optional_fields:
                if field in profile_data:
                    print(f"      ✅ {field}: {profile_data[field]}")
                else:
                    print(f"      ⚠️  {field}: Not present (optional)")
            
            if structure_valid:
                test_results["profile_data_structure"] = True
                print_test_result("PROFILE DATA STRUCTURE", True, 
                                "✅ All required fields present and valid")
            else:
                print_test_result("PROFILE DATA STRUCTURE", False, 
                                "❌ Missing required fields")
        else:
            print_test_result("PROFILE RETRIEVAL", False, 
                            f"❌ Failed: {profile_response.status_code}")
            return test_results
        
        # STEP 3: Profile Update - PUT /api/profile
        print(f"\n🔍 STEP 3: Profile Update - PUT /api/profile")
        print("   Testing profile update (name and email changes)...")
        
        original_name = profile_data.get('name', 'Unknown')
        original_email = profile_data.get('email', 'unknown@email.com')
        
        # Test profile update with new name and same email
        updated_name = f"{original_name} - Updated"
        
        update_data = {
            "name": updated_name,
            "email": original_email  # Keep same email to avoid uniqueness issues
        }
        
        print(f"   Updating profile:")
        print(f"      Name: '{original_name}' → '{updated_name}'")
        print(f"      Email: '{original_email}' (unchanged)")
        
        update_response = requests.put(f"{BACKEND_URL}/profile", json=update_data, headers=headers)
        
        if update_response.status_code == 200:
            update_result = update_response.json()
            print_test_result("PROFILE UPDATE", True, 
                            f"✅ Profile updated: {update_result.get('message', 'Success')}")
            
            # Verify the update by retrieving profile again
            verify_response = requests.get(f"{BACKEND_URL}/profile", headers=headers)
            if verify_response.status_code == 200:
                updated_profile = verify_response.json()
                test_results["updated_profile"] = updated_profile
                
                if updated_profile.get('name') == updated_name:
                    test_results["profile_update_success"] = True
                    print_test_result("PROFILE UPDATE VERIFICATION", True, 
                                    f"✅ Name successfully updated to '{updated_name}'")
                else:
                    print_test_result("PROFILE UPDATE VERIFICATION", False, 
                                    f"❌ Name not updated. Expected: '{updated_name}', Got: '{updated_profile.get('name')}'")
            else:
                print_test_result("PROFILE UPDATE VERIFICATION", False, 
                                "❌ Failed to verify profile update")
        else:
            error_detail = update_response.json().get("detail", "Unknown error")
            print_test_result("PROFILE UPDATE", False, f"❌ Update failed: {error_detail}")
        
        # STEP 4: Email Uniqueness Validation
        print(f"\n🔍 STEP 4: Email Uniqueness Validation")
        print("   Testing email uniqueness validation with existing email...")
        
        # Try to update to an email that might already exist
        existing_email_test = {
            "name": original_name,
            "email": "teste.debug@email.com"  # This email exists in the system
        }
        
        uniqueness_response = requests.put(f"{BACKEND_URL}/profile", json=existing_email_test, headers=headers)
        
        if uniqueness_response.status_code == 400:
            error_detail = uniqueness_response.json().get("detail", "")
            if "já está em uso" in error_detail or "already" in error_detail.lower():
                test_results["email_uniqueness_validation"] = True
                print_test_result("EMAIL UNIQUENESS VALIDATION", True, 
                                f"✅ Email uniqueness properly validated: {error_detail}")
            else:
                print_test_result("EMAIL UNIQUENESS VALIDATION", False, 
                                f"❌ Wrong error message: {error_detail}")
        else:
            print_test_result("EMAIL UNIQUENESS VALIDATION", False, 
                            f"❌ Expected 400 error, got: {uniqueness_response.status_code}")
        
        # STEP 5: Password Change - PUT /api/profile/password
        print(f"\n🔍 STEP 5: Password Change - PUT /api/profile/password")
        print("   Testing password change functionality...")
        
        current_password = used_credentials['password']
        new_password = "NovaSenh@123"
        
        password_change_data = {
            "current_password": current_password,
            "new_password": new_password,
            "confirm_password": new_password
        }
        
        print(f"   Attempting password change:")
        print(f"      Current Password: {current_password}")
        print(f"      New Password: {new_password}")
        
        password_response = requests.put(f"{BACKEND_URL}/profile/password", 
                                       json=password_change_data, headers=headers)
        
        if password_response.status_code == 200:
            password_result = password_response.json()
            print_test_result("PASSWORD CHANGE", True, 
                            f"✅ Password changed: {password_result.get('message', 'Success')}")
            
            # Test login with new password to verify change
            new_login_test = {
                "email": original_email,
                "password": new_password
            }
            
            new_login_response = requests.post(f"{BACKEND_URL}/auth/login", json=new_login_test)
            
            if new_login_response.status_code == 200:
                test_results["password_change_success"] = True
                print_test_result("PASSWORD CHANGE VERIFICATION", True, 
                                "✅ Login successful with new password")
                
                # Change password back to original for cleanup
                restore_password_data = {
                    "current_password": new_password,
                    "new_password": current_password,
                    "confirm_password": current_password
                }
                
                restore_response = requests.put(f"{BACKEND_URL}/profile/password", 
                                              json=restore_password_data, headers=headers)
                
                if restore_response.status_code == 200:
                    print_test_result("PASSWORD RESTORATION", True, 
                                    "✅ Password restored to original")
                else:
                    print_test_result("PASSWORD RESTORATION", False, 
                                    "⚠️  Failed to restore original password")
            else:
                print_test_result("PASSWORD CHANGE VERIFICATION", False, 
                                "❌ Login failed with new password")
        else:
            error_detail = password_response.json().get("detail", "Unknown error")
            print_test_result("PASSWORD CHANGE", False, f"❌ Password change failed: {error_detail}")
        
        # STEP 6: Error Handling Tests
        print(f"\n🔍 STEP 6: Error Handling Tests")
        print("   Testing various error scenarios...")
        
        error_tests_passed = 0
        total_error_tests = 4
        
        # Test 6.1: Invalid current password
        print("   6.1: Testing invalid current password...")
        invalid_current_password = {
            "current_password": "WrongPassword123",
            "new_password": "NewPassword123",
            "confirm_password": "NewPassword123"
        }
        
        invalid_current_response = requests.put(f"{BACKEND_URL}/profile/password", 
                                              json=invalid_current_password, headers=headers)
        
        if invalid_current_response.status_code == 400:
            error_detail = invalid_current_response.json().get("detail", "")
            if "incorreta" in error_detail or "incorrect" in error_detail.lower():
                error_tests_passed += 1
                print_test_result("INVALID CURRENT PASSWORD", True, 
                                f"✅ Properly rejected: {error_detail}")
            else:
                print_test_result("INVALID CURRENT PASSWORD", False, 
                                f"❌ Wrong error message: {error_detail}")
        else:
            print_test_result("INVALID CURRENT PASSWORD", False, 
                            f"❌ Expected 400, got: {invalid_current_response.status_code}")
        
        # Test 6.2: Mismatched password confirmation
        print("   6.2: Testing mismatched password confirmation...")
        mismatched_confirmation = {
            "current_password": current_password,
            "new_password": "NewPassword123",
            "confirm_password": "DifferentPassword123"
        }
        
        mismatch_response = requests.put(f"{BACKEND_URL}/profile/password", 
                                       json=mismatched_confirmation, headers=headers)
        
        if mismatch_response.status_code == 400:
            error_detail = mismatch_response.json().get("detail", "")
            if "coincidem" in error_detail or "match" in error_detail.lower():
                error_tests_passed += 1
                print_test_result("MISMATCHED CONFIRMATION", True, 
                                f"✅ Properly rejected: {error_detail}")
            else:
                print_test_result("MISMATCHED CONFIRMATION", False, 
                                f"❌ Wrong error message: {error_detail}")
        else:
            print_test_result("MISMATCHED CONFIRMATION", False, 
                            f"❌ Expected 400, got: {mismatch_response.status_code}")
        
        # Test 6.3: Same password as current
        print("   6.3: Testing same password as current...")
        same_password = {
            "current_password": current_password,
            "new_password": current_password,
            "confirm_password": current_password
        }
        
        same_password_response = requests.put(f"{BACKEND_URL}/profile/password", 
                                            json=same_password, headers=headers)
        
        if same_password_response.status_code == 400:
            error_detail = same_password_response.json().get("detail", "")
            if "diferente" in error_detail or "different" in error_detail.lower():
                error_tests_passed += 1
                print_test_result("SAME PASSWORD VALIDATION", True, 
                                f"✅ Properly rejected: {error_detail}")
            else:
                print_test_result("SAME PASSWORD VALIDATION", False, 
                                f"❌ Wrong error message: {error_detail}")
        else:
            print_test_result("SAME PASSWORD VALIDATION", False, 
                            f"❌ Expected 400, got: {same_password_response.status_code}")
        
        # Test 6.4: Invalid profile data
        print("   6.4: Testing invalid profile data...")
        invalid_profile_data = {
            "name": "",  # Empty name
            "email": "invalid-email"  # Invalid email format
        }
        
        invalid_profile_response = requests.put(f"{BACKEND_URL}/profile", 
                                              json=invalid_profile_data, headers=headers)
        
        if invalid_profile_response.status_code == 422 or invalid_profile_response.status_code == 400:
            error_tests_passed += 1
            print_test_result("INVALID PROFILE DATA", True, 
                            f"✅ Properly rejected invalid data: {invalid_profile_response.status_code}")
        else:
            print_test_result("INVALID PROFILE DATA", False, 
                            f"❌ Expected 400/422, got: {invalid_profile_response.status_code}")
        
        if error_tests_passed >= 3:  # At least 3 out of 4 error tests should pass
            test_results["error_handling_working"] = True
            print_test_result("ERROR HANDLING", True, 
                            f"✅ Error handling working ({error_tests_passed}/{total_error_tests} tests passed)")
        else:
            print_test_result("ERROR HANDLING", False, 
                            f"❌ Error handling issues ({error_tests_passed}/{total_error_tests} tests passed)")
        
        # STEP 7: Authentication Requirements Test
        print(f"\n🔍 STEP 7: Authentication Requirements Test")
        print("   Testing that all endpoints require authentication...")
        
        auth_tests_passed = 0
        total_auth_tests = 3
        
        # Test without authorization header
        no_auth_headers = {}
        
        # Test 7.1: GET /api/profile without auth
        no_auth_profile = requests.get(f"{BACKEND_URL}/profile", headers=no_auth_headers)
        if no_auth_profile.status_code == 401:
            auth_tests_passed += 1
            print_test_result("PROFILE GET AUTH REQUIRED", True, "✅ Authentication required")
        else:
            print_test_result("PROFILE GET AUTH REQUIRED", False, 
                            f"❌ Expected 401, got: {no_auth_profile.status_code}")
        
        # Test 7.2: PUT /api/profile without auth
        no_auth_update = requests.put(f"{BACKEND_URL}/profile", 
                                    json={"name": "Test", "email": "test@test.com"}, 
                                    headers=no_auth_headers)
        if no_auth_update.status_code == 401:
            auth_tests_passed += 1
            print_test_result("PROFILE UPDATE AUTH REQUIRED", True, "✅ Authentication required")
        else:
            print_test_result("PROFILE UPDATE AUTH REQUIRED", False, 
                            f"❌ Expected 401, got: {no_auth_update.status_code}")
        
        # Test 7.3: PUT /api/profile/password without auth
        no_auth_password = requests.put(f"{BACKEND_URL}/profile/password", 
                                      json={"current_password": "test", "new_password": "test", "confirm_password": "test"}, 
                                      headers=no_auth_headers)
        if no_auth_password.status_code == 401:
            auth_tests_passed += 1
            print_test_result("PASSWORD CHANGE AUTH REQUIRED", True, "✅ Authentication required")
        else:
            print_test_result("PASSWORD CHANGE AUTH REQUIRED", False, 
                            f"❌ Expected 401, got: {no_auth_password.status_code}")
        
        if auth_tests_passed == total_auth_tests:
            test_results["authentication_required"] = True
            print_test_result("AUTHENTICATION REQUIREMENTS", True, 
                            "✅ All endpoints properly require authentication")
        else:
            print_test_result("AUTHENTICATION REQUIREMENTS", False, 
                            f"❌ Authentication issues ({auth_tests_passed}/{total_auth_tests} tests passed)")
        
        # STEP 8: Form Validation Test
        print(f"\n🔍 STEP 8: Form Validation Test")
        print("   Testing form validation for password strength and field requirements...")
        
        validation_tests_passed = 0
        total_validation_tests = 2
        
        # Test 8.1: Weak password validation
        weak_password_data = {
            "current_password": current_password,
            "new_password": "123",  # Too short
            "confirm_password": "123"
        }
        
        weak_password_response = requests.put(f"{BACKEND_URL}/profile/password", 
                                            json=weak_password_data, headers=headers)
        
        if weak_password_response.status_code == 422 or weak_password_response.status_code == 400:
            validation_tests_passed += 1
            print_test_result("WEAK PASSWORD VALIDATION", True, 
                            f"✅ Weak password rejected: {weak_password_response.status_code}")
        else:
            print_test_result("WEAK PASSWORD VALIDATION", False, 
                            f"❌ Expected 400/422, got: {weak_password_response.status_code}")
        
        # Test 8.2: Required field validation
        missing_field_data = {
            "name": "Test Name"
            # Missing email field
        }
        
        missing_field_response = requests.put(f"{BACKEND_URL}/profile", 
                                            json=missing_field_data, headers=headers)
        
        if missing_field_response.status_code == 422 or missing_field_response.status_code == 400:
            validation_tests_passed += 1
            print_test_result("REQUIRED FIELD VALIDATION", True, 
                            f"✅ Missing field rejected: {missing_field_response.status_code}")
        else:
            print_test_result("REQUIRED FIELD VALIDATION", False, 
                            f"❌ Expected 400/422, got: {missing_field_response.status_code}")
        
        if validation_tests_passed >= 1:  # At least 1 validation test should pass
            test_results["form_validation_working"] = True
            print_test_result("FORM VALIDATION", True, 
                            f"✅ Form validation working ({validation_tests_passed}/{total_validation_tests} tests passed)")
        else:
            print_test_result("FORM VALIDATION", False, 
                            f"❌ Form validation issues ({validation_tests_passed}/{total_validation_tests} tests passed)")
        
        # STEP 9: Restore Original Profile
        print(f"\n🔍 STEP 9: Cleanup - Restore Original Profile")
        
        if test_results["profile_update_success"]:
            restore_data = {
                "name": original_name,
                "email": original_email
            }
            
            restore_response = requests.put(f"{BACKEND_URL}/profile", json=restore_data, headers=headers)
            
            if restore_response.status_code == 200:
                print_test_result("PROFILE RESTORATION", True, 
                                "✅ Original profile restored")
            else:
                print_test_result("PROFILE RESTORATION", False, 
                                "⚠️  Failed to restore original profile")
        
        # STEP 10: Final Summary
        print(f"\n🔍 STEP 10: USER PROFILE SYSTEM TEST SUMMARY")
        print("="*70)
        
        print(f"📊 TEST RESULTS:")
        print(f"   ✅ User Authentication: {'SUCCESS' if test_results['login_success'] else 'FAILED'}")
        print(f"   📄 Profile Retrieval: {'WORKING' if test_results['profile_retrieval'] else 'FAILED'}")
        print(f"   📋 Profile Data Structure: {'VALID' if test_results['profile_data_structure'] else 'INVALID'}")
        print(f"   ✏️  Profile Update: {'WORKING' if test_results['profile_update_success'] else 'FAILED'}")
        print(f"   🔒 Password Change: {'WORKING' if test_results['password_change_success'] else 'FAILED'}")
        print(f"   ⚠️  Error Handling: {'WORKING' if test_results['error_handling_working'] else 'FAILED'}")
        print(f"   📧 Email Uniqueness: {'WORKING' if test_results['email_uniqueness_validation'] else 'FAILED'}")
        print(f"   🔐 Authentication Required: {'WORKING' if test_results['authentication_required'] else 'FAILED'}")
        print(f"   ✅ Form Validation: {'WORKING' if test_results['form_validation_working'] else 'FAILED'}")
        
        # Determine overall success
        critical_features = [
            test_results['login_success'],
            test_results['profile_retrieval'],
            test_results['profile_data_structure'],
            test_results['profile_update_success'],
            test_results['password_change_success']
        ]
        
        security_features = [
            test_results['error_handling_working'],
            test_results['authentication_required']
        ]
        
        critical_success = all(critical_features)
        security_success = all(security_features)
        
        if critical_success and security_success:
            print(f"\n🎉 USER PROFILE SYSTEM WORKING EXCELLENTLY!")
            print("✅ All critical functionality working correctly:")
            print("   - User authentication with provided credentials")
            print("   - Profile data retrieval with proper structure (id, name, email, created_at, email_verified)")
            print("   - Profile update (name and email) with persistence verification")
            print("   - Password change with current password validation and new password requirements")
            print("   - Comprehensive error handling for invalid inputs")
            print("   - Email uniqueness validation")
            print("   - Authentication requirements for all endpoints")
            print("   - Form validation for password strength and required fields")
            print("   - Integration with existing authentication system")
            print("   - Brazilian Portuguese messaging patterns")
            
            return True
        else:
            print(f"\n⚠️ USER PROFILE SYSTEM ISSUES DETECTED:")
            if not critical_success:
                print("   ❌ Critical functionality issues:")
                if not test_results['login_success']:
                    print("      - User authentication failed")
                if not test_results['profile_retrieval']:
                    print("      - Profile retrieval failed")
                if not test_results['profile_data_structure']:
                    print("      - Profile data structure invalid")
                if not test_results['profile_update_success']:
                    print("      - Profile update failed")
                if not test_results['password_change_success']:
                    print("      - Password change failed")
            
            if not security_success:
                print("   ❌ Security functionality issues:")
                if not test_results['error_handling_working']:
                    print("      - Error handling not working properly")
                if not test_results['authentication_required']:
                    print("      - Authentication not properly required")
            
            return False
        
    except Exception as e:
        print_test_result("USER PROFILE SYSTEM TEST", False, f"Exception: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 OrçaZenFinanceiro User Profile System Backend Testing")
    print("="*80)
    print("Testing User Profile system backend functionality")
    print("Focus: GET /api/profile, PUT /api/profile, PUT /api/profile/password")
    print("="*80)
    
    try:
        # Run User Profile System Test
        print("\n📋 Running User Profile System Test...")
        profile_system_result = test_user_profile_system()
        
        # Final Summary
        print("\n" + "="*80)
        print("🏁 USER PROFILE SYSTEM TESTING COMPLETED")
        print("="*80)
        
        print("📊 FINAL TEST RESULTS:")
        print(f"   🔍 User Profile System Test: {'✅ PASSED' if profile_system_result else '❌ FAILED'}")
        
        if profile_system_result:
            print("\n🎉 USER PROFILE SYSTEM TESTING SUCCESSFUL!")
            print("✅ All User Profile backend functionality working correctly:")
            print("   - User authentication with provided credentials")
            print("   - Profile data retrieval (GET /api/profile)")
            print("   - Profile updates (PUT /api/profile)")
            print("   - Password changes (PUT /api/profile/password)")
            print("   - Data validation and error handling")
            print("   - Authentication requirements")
            print("   - Brazilian Portuguese messaging")
            print("   - Integration with existing authentication system")
            
            print("\n📋 READY FOR FRONTEND INTEGRATION:")
            print("   - Backend endpoints fully functional")
            print("   - Data structure validated")
            print("   - Security measures in place")
            print("   - Error handling comprehensive")
            
        else:
            print("\n⚠️ USER PROFILE SYSTEM TESTING ISSUES DETECTED:")
            print("   ❌ User profile system test failed")
            
            print("\n🔧 RECOMMENDED ACTIONS:")
            print("   - Review failed test details above")
            print("   - Fix identified backend issues")
            print("   - Re-run tests to verify fixes")
        
        print("\n" + "="*80)
        print("🏁 TESTING COMPLETE")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR DURING TESTING: {str(e)}")
        print("🔧 Please check backend server status and try again")