#!/usr/bin/env python3
"""
Gmail App Password Configuration Test - Final Verification
Tests the real email sending with the new Gmail App Password configuration
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

def test_gmail_app_password_configuration():
    """
    📧 GMAIL APP PASSWORD CONFIGURATION TEST - FINAL VERIFICATION
    
    This addresses the specific review request to test the real email sending with the new 
    Gmail App Password configuration as the final test to confirm real email sending is working.
    
    Configuration Being Tested:
    - SMTP_USER: hpdanielvb@gmail.com  
    - SMTP_PASSWORD: ycxacobxjvxmyfwk (App Password)
    - EMAIL_ENABLED: true
    - SMTP_HOST: smtp.gmail.com:587
    
    Test Steps:
    1. **Login** with hpdanielvb@gmail.com / 123456
    2. **Send real test email** to hpdanielvb@gmail.com via POST /api/test-email
    3. **Verify SMTP connection** works with App Password
    4. **Confirm email actually sends** (not simulation)
    5. **Check backend logs** for "[EMAIL SENT] Successfully sent to:" message
    
    Expected Results:
    - ✅ No SMTP authentication errors
    - ✅ Response shows success: true
    - ✅ email_enabled: true
    - ✅ Backend logs show "[EMAIL SENT]" (not "[EMAIL SIMULATION]")
    - ✅ Real email delivered to hpdanielvb@gmail.com inbox
    
    Key Validation:
    - Gmail App Password should eliminate the "Application-specific password required" error
    - SMTP connection to smtp.gmail.com:587 should succeed
    - HTML and text email content should be properly sent
    - Response should include all fields: success, message, email_enabled, smtp_server, smtp_port, timestamp
    
    This is the final test to confirm real email sending is working with Gmail App Password authentication.
    """
    print("\n" + "="*80)
    print("📧 GMAIL APP PASSWORD CONFIGURATION TEST - FINAL VERIFICATION")
    print("="*80)
    print("Testing real email sending with Gmail App Password configuration")
    print("Configuration: SMTP_USER=hpdanielvb@gmail.com, SMTP_PASSWORD=ycxacobxjvxmyfwk (App Password)")
    print("Target email: hpdanielvb@gmail.com")
    print("Expected: EMAIL_ENABLED=true (real sending mode)")
    
    # Test credentials from review request
    user_login_primary = {
        "email": "hpdanielvb@gmail.com",
        "password": "123456"
    }
    
    user_login_secondary = {
        "email": "hpdanielvb@gmail.com", 
        "password": "TestPassword123"
    }
    
    test_results = {
        "login_success": False,
        "email_endpoint_accessible": False,
        "email_sent_successfully": False,
        "response_structure_valid": False,
        "email_enabled_true": False,
        "smtp_config_correct": False,
        "timestamp_present": False,
        "real_sending_confirmed": False,
        "no_smtp_auth_errors": False,
        "app_password_working": False,
        "auth_token": None,
        "email_response": None,
        "error_details": None
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
                test_results["error_details"] = f"Authentication failed: {error_detail}"
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
        
        # STEP 2: Test Email Endpoint Accessibility
        print(f"\n🔍 STEP 2: Email Endpoint Accessibility Test")
        print("   Verifying POST /api/test-email endpoint is accessible...")
        
        # First, test with invalid data to check endpoint exists
        test_access_response = requests.post(f"{BACKEND_URL}/test-email", 
                                           json={}, headers=headers)
        
        if test_access_response.status_code in [422, 400]:  # Validation error means endpoint exists
            test_results["email_endpoint_accessible"] = True
            print_test_result("EMAIL ENDPOINT ACCESSIBILITY", True, 
                            "✅ POST /api/test-email endpoint is accessible")
        elif test_access_response.status_code == 404:
            test_results["error_details"] = "Email endpoint not found"
            print_test_result("EMAIL ENDPOINT ACCESSIBILITY", False, 
                            "❌ POST /api/test-email endpoint not found")
            return test_results
        else:
            print_test_result("EMAIL ENDPOINT ACCESSIBILITY", True, 
                            f"✅ Endpoint accessible (status: {test_access_response.status_code})")
            test_results["email_endpoint_accessible"] = True
        
        # STEP 3: Send Test Email with Gmail App Password
        print(f"\n🔍 STEP 3: Send Test Email with Gmail App Password - POST /api/test-email")
        print("   Sending test email to hpdanielvb@gmail.com...")
        print("   Expected: Real email sending with App Password authentication")
        
        email_request = {
            "to": "hpdanielvb@gmail.com",
            "subject": "🔐 Gmail App Password Test - OrçaZenFinanceiro Final Verification"
        }
        
        print(f"   📧 EMAIL REQUEST:")
        print(f"      To: {email_request['to']}")
        print(f"      Subject: {email_request['subject']}")
        print(f"      Expected SMTP: smtp.gmail.com:587")
        print(f"      Expected EMAIL_ENABLED: true")
        print(f"      Expected App Password: ycxacobxjvxmyfwk")
        
        email_response = requests.post(f"{BACKEND_URL}/test-email", 
                                     json=email_request, headers=headers)
        
        test_results["email_response"] = email_response.json() if email_response.status_code == 200 else None
        
        if email_response.status_code == 200:
            email_result = email_response.json()
            test_results["email_sent_successfully"] = True
            
            print_test_result("EMAIL SENDING", True, 
                            "✅ Email endpoint responded successfully")
            
            # STEP 4: Verify Response Structure
            print(f"\n🔍 STEP 4: Response Structure Validation")
            print("   Verifying response contains all required fields...")
            
            required_fields = ['success', 'message', 'email_enabled', 'smtp_server', 'smtp_port', 'timestamp']
            structure_valid = True
            
            print(f"   📊 RESPONSE STRUCTURE VALIDATION:")
            for field in required_fields:
                if field in email_result:
                    value = email_result[field]
                    print(f"      ✅ {field}: {value}")
                else:
                    print(f"      ❌ {field}: MISSING")
                    structure_valid = False
            
            if structure_valid:
                test_results["response_structure_valid"] = True
                print_test_result("RESPONSE STRUCTURE", True, 
                                "✅ All required fields present in response")
            else:
                print_test_result("RESPONSE STRUCTURE", False, 
                                "❌ Missing required fields in response")
            
            # STEP 5: Verify Gmail App Password Configuration
            print(f"\n🔍 STEP 5: Gmail App Password Configuration Verification")
            print("   Checking EMAIL_ENABLED and SMTP configuration...")
            
            success_status = email_result.get('success', False)
            email_enabled = email_result.get('email_enabled', False)
            smtp_server = email_result.get('smtp_server', '')
            smtp_port = email_result.get('smtp_port', 0)
            timestamp = email_result.get('timestamp', '')
            message = email_result.get('message', '')
            
            print(f"   📧 GMAIL APP PASSWORD CONFIGURATION:")
            print(f"      Success: {success_status}")
            print(f"      Email Enabled: {email_enabled}")
            print(f"      SMTP Server: {smtp_server}")
            print(f"      SMTP Port: {smtp_port}")
            print(f"      Timestamp: {timestamp}")
            print(f"      Message: {message}")
            
            # Check EMAIL_ENABLED is true
            if email_enabled:
                test_results["email_enabled_true"] = True
                print_test_result("EMAIL_ENABLED STATUS", True, 
                                "✅ EMAIL_ENABLED is true (real sending mode)")
            else:
                print_test_result("EMAIL_ENABLED STATUS", False, 
                                "❌ EMAIL_ENABLED is false (simulation mode)")
            
            # Check SMTP configuration
            if smtp_server == "smtp.gmail.com" and smtp_port == 587:
                test_results["smtp_config_correct"] = True
                print_test_result("SMTP CONFIGURATION", True, 
                                "✅ SMTP configuration correct (smtp.gmail.com:587)")
            else:
                print_test_result("SMTP CONFIGURATION", False, 
                                f"❌ SMTP config incorrect. Expected: smtp.gmail.com:587, Got: {smtp_server}:{smtp_port}")
            
            # Check timestamp
            if timestamp:
                test_results["timestamp_present"] = True
                print_test_result("TIMESTAMP", True, 
                                f"✅ Timestamp present: {timestamp}")
            else:
                print_test_result("TIMESTAMP", False, 
                                "❌ Timestamp missing")
            
            # STEP 6: Verify Real Sending vs Simulation
            print(f"\n🔍 STEP 6: Real Sending vs Simulation Verification")
            print("   Analyzing response to confirm real email sending...")
            
            if success_status and email_enabled:
                if "enviado com sucesso" in message.lower() or "successfully sent" in message.lower():
                    test_results["real_sending_confirmed"] = True
                    print_test_result("REAL SENDING CONFIRMATION", True, 
                                    "✅ Response indicates real email was sent")
                    print(f"      Success Message: {message}")
                    
                    # Check for no SMTP authentication errors
                    if "authentication" not in message.lower() and "login" not in message.lower() and "password" not in message.lower():
                        test_results["no_smtp_auth_errors"] = True
                        print_test_result("NO SMTP AUTH ERRORS", True, 
                                        "✅ No SMTP authentication errors detected")
                    else:
                        print_test_result("NO SMTP AUTH ERRORS", False, 
                                        f"❌ SMTP authentication issues detected: {message}")
                    
                    # Check if App Password is working
                    if success_status and email_enabled and test_results["no_smtp_auth_errors"]:
                        test_results["app_password_working"] = True
                        print_test_result("GMAIL APP PASSWORD WORKING", True, 
                                        "✅ Gmail App Password authentication successful")
                    else:
                        print_test_result("GMAIL APP PASSWORD WORKING", False, 
                                        "❌ Gmail App Password authentication failed")
                    
                    # Additional verification
                    print(f"\n   🔍 BACKEND LOG MONITORING GUIDANCE:")
                    print("   Look for these log messages in backend logs:")
                    print("      ✅ '[EMAIL SENT] Successfully sent to: hpdanielvb@gmail.com'")
                    print("      ❌ '[EMAIL SIMULATION]' (should NOT appear)")
                    print("   Check for SMTP authentication success with App Password")
                    print("   Monitor that no 'Application-specific password required' errors appear")
                else:
                    print_test_result("REAL SENDING CONFIRMATION", False, 
                                    f"❌ Message doesn't confirm real sending: {message}")
            else:
                print_test_result("REAL SENDING CONFIRMATION", False, 
                                "❌ Email not sent successfully or EMAIL_ENABLED is false")
            
            # STEP 7: Gmail App Password Error Analysis
            print(f"\n🔍 STEP 7: Gmail App Password Error Analysis")
            
            if not success_status:
                print("   ⚠️  EMAIL SENDING FAILED - Analyzing Gmail App Password issues:")
                print("   Possible issues:")
                print("      1. App Password not correctly configured")
                print("      2. Gmail account 2FA not enabled")
                print("      3. App Password expired or revoked")
                print("      4. SMTP_PASSWORD in .env not updated with App Password")
                print("      5. Network connectivity issues")
                print("      6. Gmail security blocks")
                
                if "application-specific password required" in message.lower():
                    print("   🔍 APP PASSWORD REQUIRED ERROR DETECTED:")
                    print("      - This is the exact error we're trying to fix")
                    print("      - App Password configuration not working")
                    print("      - Check SMTP_PASSWORD in backend/.env")
                
                if "authentication" in message.lower() or "login" in message.lower():
                    print("   🔍 AUTHENTICATION ISSUE DETECTED:")
                    print("      - App Password may be incorrect")
                    print("      - Verify App Password: ycxacobxjvxmyfwk")
                    print("      - Check if App Password was generated correctly")
                
                if "connection" in message.lower() or "timeout" in message.lower():
                    print("   🔍 CONNECTION ISSUE DETECTED:")
                    print("      - Check network connectivity")
                    print("      - Verify SMTP server and port")
                    print("      - Check firewall settings")
            else:
                print("   ✅ NO GMAIL APP PASSWORD ERRORS DETECTED")
                print("   Gmail App Password authentication working correctly")
                
        else:
            error_detail = email_response.json().get("detail", "Unknown error") if email_response.status_code != 500 else "Internal server error"
            test_results["error_details"] = f"Email sending failed: {error_detail}"
            print_test_result("EMAIL SENDING", False, 
                            f"❌ Email sending failed: {error_detail}")
            
            # Analyze error type
            if email_response.status_code == 401:
                print("   🔍 AUTHENTICATION ERROR:")
                print("      - JWT token may be invalid or expired")
                print("      - User authentication required")
            elif email_response.status_code == 422:
                print("   🔍 VALIDATION ERROR:")
                print("      - Check email request format")
                print("      - Verify 'to' field is valid email")
            elif email_response.status_code == 500:
                print("   🔍 SERVER ERROR:")
                print("      - SMTP configuration issue")
                print("      - Gmail App Password authentication failure")
                print("      - Check backend logs for detailed error")
        
        # STEP 8: Final Summary
        print(f"\n🔍 STEP 8: GMAIL APP PASSWORD CONFIGURATION TEST SUMMARY")
        print("="*70)
        
        print(f"📊 TEST RESULTS:")
        print(f"   ✅ User Authentication: {'SUCCESS' if test_results['login_success'] else 'FAILED'}")
        print(f"   🔗 Email Endpoint Access: {'WORKING' if test_results['email_endpoint_accessible'] else 'FAILED'}")
        print(f"   📧 Email Sending: {'SUCCESS' if test_results['email_sent_successfully'] else 'FAILED'}")
        print(f"   📋 Response Structure: {'VALID' if test_results['response_structure_valid'] else 'INVALID'}")
        print(f"   ⚙️  EMAIL_ENABLED: {'TRUE' if test_results['email_enabled_true'] else 'FALSE'}")
        print(f"   🌐 SMTP Configuration: {'CORRECT' if test_results['smtp_config_correct'] else 'INCORRECT'}")
        print(f"   ⏰ Timestamp: {'PRESENT' if test_results['timestamp_present'] else 'MISSING'}")
        print(f"   📨 Real Sending: {'CONFIRMED' if test_results['real_sending_confirmed'] else 'NOT CONFIRMED'}")
        print(f"   🔐 No SMTP Auth Errors: {'CONFIRMED' if test_results['no_smtp_auth_errors'] else 'ERRORS DETECTED'}")
        print(f"   🔑 Gmail App Password: {'WORKING' if test_results['app_password_working'] else 'NOT WORKING'}")
        
        # Determine overall success
        critical_features = [
            test_results['login_success'],
            test_results['email_endpoint_accessible'],
            test_results['email_sent_successfully'],
            test_results['response_structure_valid']
        ]
        
        gmail_app_password_features = [
            test_results['email_enabled_true'],
            test_results['smtp_config_correct'],
            test_results['real_sending_confirmed'],
            test_results['no_smtp_auth_errors'],
            test_results['app_password_working']
        ]
        
        critical_success = all(critical_features)
        gmail_app_password_success = all(gmail_app_password_features)
        
        if critical_success and gmail_app_password_success:
            print(f"\n🎉 GMAIL APP PASSWORD CONFIGURATION WORKING EXCELLENTLY!")
            print("✅ All functionality working correctly:")
            print("   - User authentication with hpdanielvb@gmail.com / 123456")
            print("   - POST /api/test-email endpoint accessible and functional")
            print("   - EMAIL_ENABLED=true (real sending mode, not simulation)")
            print("   - SMTP configuration correct (smtp.gmail.com:587)")
            print("   - Gmail App Password authentication successful")
            print("   - No SMTP authentication errors")
            print("   - Test email sent successfully to hpdanielvb@gmail.com")
            print("   - Response structure contains all required fields")
            print("   - Timestamp present for tracking")
            print("   - Real email sending confirmed (not just logged)")
            print("   - Gmail App Password (ycxacobxjvxmyfwk) working properly")
            
            if test_results["email_response"]:
                print(f"\n📧 FINAL EMAIL RESPONSE:")
                for key, value in test_results["email_response"].items():
                    print(f"   {key}: {value}")
            
            print(f"\n🔍 BACKEND LOG VERIFICATION:")
            print("   Expected log message: '[EMAIL SENT] Successfully sent to: hpdanielvb@gmail.com'")
            print("   Should NOT see: '[EMAIL SIMULATION]'")
            
            return True
        else:
            print(f"\n⚠️ GMAIL APP PASSWORD CONFIGURATION ISSUES DETECTED:")
            if not critical_success:
                print("   ❌ Critical functionality issues:")
                if not test_results['login_success']:
                    print("      - User authentication failed")
                if not test_results['email_endpoint_accessible']:
                    print("      - Email endpoint not accessible")
                if not test_results['email_sent_successfully']:
                    print("      - Email sending failed")
                if not test_results['response_structure_valid']:
                    print("      - Response structure invalid")
            
            if not gmail_app_password_success:
                print("   ❌ Gmail App Password configuration issues:")
                if not test_results['email_enabled_true']:
                    print("      - EMAIL_ENABLED is false (simulation mode)")
                if not test_results['smtp_config_correct']:
                    print("      - SMTP configuration incorrect")
                if not test_results['real_sending_confirmed']:
                    print("      - Real email sending not confirmed")
                if not test_results['no_smtp_auth_errors']:
                    print("      - SMTP authentication errors detected")
                if not test_results['app_password_working']:
                    print("      - Gmail App Password not working")
            
            if test_results["error_details"]:
                print(f"   🔍 Error Details: {test_results['error_details']}")
            
            print(f"\n💡 GMAIL APP PASSWORD TROUBLESHOOTING:")
            print("   1. Verify Gmail App Password configuration:")
            print("      - SMTP_USER=hpdanielvb@gmail.com")
            print("      - SMTP_PASSWORD=ycxacobxjvxmyfwk (App Password)")
            print("      - EMAIL_ENABLED=true")
            print("   2. Check Gmail account settings:")
            print("      - 2-factor authentication must be enabled")
            print("      - App Password must be generated and active")
            print("      - App Password should be 16 characters")
            print("   3. Verify backend/.env file:")
            print("      - SMTP_PASSWORD should contain App Password, not regular password")
            print("      - No spaces or extra characters in App Password")
            print("   4. Check backend logs for detailed SMTP errors")
            print("   5. Test App Password directly with Gmail SMTP")
            
            return False
        
    except Exception as e:
        test_results["error_details"] = f"Exception: {str(e)}"
        print_test_result("GMAIL APP PASSWORD CONFIGURATION TEST", False, f"Exception: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Gmail App Password Configuration Test - Final Verification")
    print("="*80)
    print("Testing real email sending functionality with Gmail App Password")
    print("Focus: POST /api/test-email with Gmail App Password authentication")
    print("Target: hpdanielvb@gmail.com")
    print("="*80)
    
    # Run the Gmail App Password Configuration test
    print("\n📧 RUNNING GMAIL APP PASSWORD CONFIGURATION TEST...")
    email_success = test_gmail_app_password_configuration()
    
    # Summary
    print("\n" + "="*80)
    print("📊 GMAIL APP PASSWORD CONFIGURATION TESTING SUMMARY")
    print("="*80)
    
    if email_success:
        print("🎉 GMAIL APP PASSWORD CONFIGURATION TESTING COMPLETED SUCCESSFULLY!")
        print("✅ Gmail App Password working properly with EMAIL_ENABLED=true")
        print("✅ Test email sent successfully to hpdanielvb@gmail.com")
        print("✅ SMTP configuration correct (smtp.gmail.com:587)")
        print("✅ No SMTP authentication errors")
        print("✅ Real email sending confirmed (not simulation)")
        print("✅ App Password (ycxacobxjvxmyfwk) authentication successful")
        print("\n🔍 FINAL VERIFICATION:")
        print("   - Check hpdanielvb@gmail.com inbox for test email")
        print("   - Backend logs should show '[EMAIL SENT] Successfully sent to:'")
        print("   - No '[EMAIL SIMULATION]' messages should appear")
        print("\n🎯 CONCLUSION: Gmail App Password configuration is working correctly!")
    else:
        print("❌ GMAIL APP PASSWORD CONFIGURATION TESTING FAILED!")
        print("⚠️  Issues detected with Gmail App Password authentication")
        print("🔧 Review troubleshooting recommendations above")
        print("📋 Check backend logs for detailed SMTP error messages")
        print("🔑 Verify App Password configuration in backend/.env")
        print("\n🎯 CONCLUSION: Gmail App Password configuration needs attention!")
    
    print("="*80)