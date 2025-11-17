#!/usr/bin/env python3
"""
Zalo OA Finance Workflow - End-to-End Test Suite
Kiểm thử đầy đủ toàn bộ workflow từ Lead đến Hoàn thành
"""

import requests
import json
import time
import sys

# Configuration
BASE_URL = "http://localhost:5000/api"
TEST_RESULTS = {
    "passed": 0,
    "failed": 0,
    "errors": []
}

def print_header(text):
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

def print_test(name, passed, details=""):
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {name}")
    if details and not passed:
        print(f"    └─ {details}")
    
    if passed:
        TEST_RESULTS["passed"] += 1
    else:
        TEST_RESULTS["failed"] += 1
        TEST_RESULTS["errors"].append(f"{name}: {details}")

def test_health_check():
    """Test server is running"""
    try:
        response = requests.get(f"{BASE_URL.replace('/api', '/')}")
        return response.status_code == 200
    except:
        return False

def test_auth_login():
    """Test user authentication"""
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        data = response.json()
        
        if response.status_code == 200 and "token" in data:
            return True, data["token"]
        return False, None
    except Exception as e:
        return False, str(e)

def test_auth_invalid_login():
    """Test invalid login credentials"""
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json={
            "username": "admin",
            "password": "wrongpassword"
        })
        return response.status_code == 401
    except:
        return False

def test_get_current_user(token):
    """Test get current user info"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
        data = response.json()
        
        return (
            response.status_code == 200 and 
            "username" in data and 
            data["username"] == "admin"
        )
    except:
        return False

def test_create_lead(token):
    """Test creating a new lead"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        lead_data = {
            "name": "Nguyễn Văn Test",
            "phone": "0901234567",
            "email": "test@example.com",
            "product_interest": "vay_tieu_dung",
            "notes": "Lead từ E2E test"
        }
        
        response = requests.post(f"{BASE_URL}/leads", json=lead_data, headers=headers)
        data = response.json()
        
        if response.status_code == 201 and "id" in data:
            return True, data["id"]
        return False, None
    except Exception as e:
        return False, str(e)

def test_get_leads(token):
    """Test retrieving leads list"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/leads", headers=headers)
        data = response.json()
        
        return response.status_code == 200 and isinstance(data, list)
    except:
        return False

def test_update_lead(token, lead_id):
    """Test updating a lead"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        update_data = {
            "status": "dang_xu_ly",
            "assigned_to": "chuyen_vien_01",
            "notes": "Đã liên hệ khách hàng"
        }
        
        response = requests.put(f"{BASE_URL}/leads/{lead_id}", json=update_data, headers=headers)
        data = response.json()
        
        return response.status_code == 200 and data.get("status") == "dang_xu_ly"
    except:
        return False

def test_chatbot_response():
    """Test chatbot AI responses"""
    try:
        # Test greeting
        response = requests.post(f"{BASE_URL}/zalo/webhook", json={
            "event_name": "user_send_text",
            "sender": {"id": "test_user_001"},
            "message": {"text": "Xin chào"}
        })
        data = response.json()
        
        return (
            response.status_code == 200 and 
            "text" in data and 
            "intent" in data
        )
    except:
        return False

def test_chatbot_product_intent():
    """Test chatbot understands product inquiry"""
    try:
        response = requests.post(f"{BASE_URL}/zalo/webhook", json={
            "event_name": "user_send_text",
            "sender": {"id": "test_user_002"},
            "message": {"text": "Có những sản phẩm gì?"}
        })
        data = response.json()
        
        return (
            response.status_code == 200 and 
            data.get("intent") == "san_pham"
        )
    except:
        return False

def test_chatbot_registration_intent():
    """Test chatbot understands registration request"""
    try:
        response = requests.post(f"{BASE_URL}/zalo/webhook", json={
            "event_name": "user_send_text",
            "sender": {"id": "test_user_003"},
            "message": {"text": "Tôi muốn đăng ký tư vấn"}
        })
        data = response.json()
        
        return (
            response.status_code == 200 and 
            data.get("intent") == "dang_ky_tu_van"
        )
    except:
        return False

def test_send_message(token):
    """Test sending message through OA"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(f"{BASE_URL}/zalo/send-message", json={
            "recipient_id": "test_user_001",
            "message": "Cảm ơn bạn đã liên hệ!"
        }, headers=headers)
        data = response.json()
        
        return response.status_code == 200 and data.get("status") == "sent"
    except:
        return False

def test_get_conversations(token):
    """Test retrieving conversations"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/zalo/conversations", headers=headers)
        data = response.json()
        
        return response.status_code == 200 and isinstance(data, list)
    except:
        return False

def test_upload_document(token, lead_id):
    """Test uploading document"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        doc_data = {
            "type": "cccd",
            "lead_id": lead_id,
            "filename": "cccd_test.pdf",
            "file_size": 524288,
            "notes": "CCCD từ E2E test"
        }
        
        response = requests.post(f"{BASE_URL}/documents", json=doc_data, headers=headers)
        data = response.json()
        
        if response.status_code == 201 and "id" in data:
            return True, data["id"]
        return False, None
    except Exception as e:
        return False, str(e)

def test_process_ocr(token, doc_id):
    """Test OCR processing"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(f"{BASE_URL}/documents/{doc_id}/ocr", headers=headers)
        data = response.json()
        
        return (
            response.status_code == 200 and 
            data.get("status") == "verified" and
            "ocr_data" in data and
            "ho_ten" in data["ocr_data"]
        )
    except:
        return False

def test_get_documents(token):
    """Test retrieving documents"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/documents", headers=headers)
        data = response.json()
        
        return response.status_code == 200 and isinstance(data, list)
    except:
        return False

def test_notification_templates(token):
    """Test getting notification templates"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/notifications/templates", headers=headers)
        data = response.json()
        
        return (
            response.status_code == 200 and 
            "chao_mung" in data and
            "xac_nhan_yeu_cau" in data
        )
    except:
        return False

def test_send_notification(token):
    """Test sending notification"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(f"{BASE_URL}/notifications/send", json={
            "template": "chao_mung",
            "recipient_id": "test_user_001",
            "channel": "zalo_oa",
            "content": "Chào mừng bạn!"
        }, headers=headers)
        data = response.json()
        
        return response.status_code == 201 and data.get("status") == "sent"
    except:
        return False

def test_dashboard_analytics(token):
    """Test dashboard analytics"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/analytics/dashboard", headers=headers)
        data = response.json()
        
        return (
            response.status_code == 200 and
            "stats" in data and
            "total_leads" in data["stats"] and
            "lead_by_status" in data
        )
    except:
        return False

def test_export_report(token):
    """Test exporting reports"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/analytics/reports?type=summary", headers=headers)
        data = response.json()
        
        return (
            response.status_code == 200 and
            "report_type" in data and
            "data" in data
        )
    except:
        return False

def test_workflow_status(token, lead_id):
    """Test workflow status tracking"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/workflow/{lead_id}/status", headers=headers)
        data = response.json()
        
        return (
            response.status_code == 200 and
            "steps" in data and
            len(data["steps"]) == 6
        )
    except:
        return False

def test_advance_workflow(token, lead_id):
    """Test advancing workflow steps"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(f"{BASE_URL}/workflow/{lead_id}/advance", json={
            "next_step": "phan_loai"
        }, headers=headers)
        data = response.json()
        
        # Check if step was advanced
        phan_loai_step = next((s for s in data["steps"] if s["step"] == "phan_loai"), None)
        
        return (
            response.status_code == 200 and
            phan_loai_step is not None and
            phan_loai_step["status"] == "completed"
        )
    except:
        return False

def test_create_user(token):
    """Test creating new user (admin only)"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(f"{BASE_URL}/auth/register", json={
            "username": "test_cskh",
            "password": "123456",
            "name": "Test CSKH",
            "email": "cskh@test.com",
            "role": "cskh"
        }, headers=headers)
        data = response.json()
        
        return response.status_code == 200 and "user_id" in data
    except:
        return False

def test_get_users(token):
    """Test getting user list"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/users", headers=headers)
        data = response.json()
        
        return response.status_code == 200 and isinstance(data, list) and len(data) > 0
    except:
        return False

def test_get_roles(token):
    """Test getting roles list"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/roles", headers=headers)
        data = response.json()
        
        return (
            response.status_code == 200 and
            "quan_tri_vien" in data and
            "cskh" in data
        )
    except:
        return False

def test_broadcast_message(token):
    """Test sending broadcast message"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(f"{BASE_URL}/zalo/broadcast", json={
            "title": "Khuyến mãi tháng 11",
            "content": "Ưu đãi lãi suất 0% cho khoản vay đầu tiên",
            "target_audience": "all"
        }, headers=headers)
        data = response.json()
        
        return response.status_code == 201 and "id" in data
    except:
        return False

def run_all_tests():
    """Run complete E2E test suite"""
    
    print_header("ZALO OA FINANCE WORKFLOW - E2E TEST SUITE")
    print("Testing all features end-to-end...")
    
    # Test 1: Server Health
    print_header("1. SERVER HEALTH CHECK")
    health_ok = test_health_check()
    print_test("Server is running", health_ok, "Cannot connect to server")
    
    if not health_ok:
        print("\n❌ Server not running! Please start the server first.")
        print("   Run: python backend/app.py")
        sys.exit(1)
    
    # Test 2: Authentication
    print_header("2. AUTHENTICATION")
    
    login_ok, token = test_auth_login()
    print_test("Login with valid credentials", login_ok)
    
    if not login_ok or not token:
        print("\n❌ Cannot authenticate! Tests cannot continue.")
        sys.exit(1)
    
    invalid_login_ok = test_auth_invalid_login()
    print_test("Reject invalid credentials", invalid_login_ok)
    
    user_info_ok = test_get_current_user(token)
    print_test("Get current user info", user_info_ok)
    
    # Test 3: Lead Management
    print_header("3. LEAD MANAGEMENT")
    
    create_lead_ok, lead_id = test_create_lead(token)
    print_test("Create new lead", create_lead_ok)
    
    get_leads_ok = test_get_leads(token)
    print_test("Retrieve leads list", get_leads_ok)
    
    if lead_id:
        update_lead_ok = test_update_lead(token, lead_id)
        print_test("Update lead status", update_lead_ok)
    else:
        print_test("Update lead status", False, "No lead created")
    
    # Test 4: Chatbot AI
    print_header("4. CHATBOT AI ENGINE")
    
    chatbot_ok = test_chatbot_response()
    print_test("Chatbot responds to messages", chatbot_ok)
    
    product_intent_ok = test_chatbot_product_intent()
    print_test("Chatbot recognizes product intent", product_intent_ok)
    
    registration_intent_ok = test_chatbot_registration_intent()
    print_test("Chatbot recognizes registration intent", registration_intent_ok)
    
    # Test 5: Zalo OA Messaging
    print_header("5. ZALO OA MESSAGING")
    
    send_msg_ok = test_send_message(token)
    print_test("Send message to user", send_msg_ok)
    
    get_conv_ok = test_get_conversations(token)
    print_test("Retrieve conversations", get_conv_ok)
    
    broadcast_ok = test_broadcast_message(token)
    print_test("Send broadcast message", broadcast_ok)
    
    # Test 6: Document Management
    print_header("6. DOCUMENT MANAGEMENT & OCR")
    
    upload_doc_ok, doc_id = test_upload_document(token, lead_id or "test_lead")
    print_test("Upload document", upload_doc_ok)
    
    if doc_id:
        ocr_ok = test_process_ocr(token, doc_id)
        print_test("Process OCR and extract data", ocr_ok)
    else:
        print_test("Process OCR and extract data", False, "No document uploaded")
    
    get_docs_ok = test_get_documents(token)
    print_test("Retrieve documents list", get_docs_ok)
    
    # Test 7: Notifications
    print_header("7. NOTIFICATION SYSTEM")
    
    templates_ok = test_notification_templates(token)
    print_test("Get notification templates", templates_ok)
    
    send_notif_ok = test_send_notification(token)
    print_test("Send automated notification", send_notif_ok)
    
    # Test 8: Workflow Management
    print_header("8. WORKFLOW END-TO-END")
    
    if lead_id:
        workflow_status_ok = test_workflow_status(token, lead_id)
        print_test("Track workflow status", workflow_status_ok)
        
        advance_workflow_ok = test_advance_workflow(token, lead_id)
        print_test("Advance workflow steps", advance_workflow_ok)
    else:
        print_test("Track workflow status", False, "No lead created")
        print_test("Advance workflow steps", False, "No lead created")
    
    # Test 9: Analytics & Reporting
    print_header("9. ANALYTICS & REPORTING")
    
    analytics_ok = test_dashboard_analytics(token)
    print_test("Dashboard analytics", analytics_ok)
    
    report_ok = test_export_report(token)
    print_test("Export summary report", report_ok)
    
    # Test 10: User Management
    print_header("10. USER & ROLE MANAGEMENT")
    
    create_user_ok = test_create_user(token)
    print_test("Create new user", create_user_ok)
    
    get_users_ok = test_get_users(token)
    print_test("Get users list", get_users_ok)
    
    get_roles_ok = test_get_roles(token)
    print_test("Get roles and permissions", get_roles_ok)
    
    # Final Summary
    print_header("TEST SUMMARY")
    
    total = TEST_RESULTS["passed"] + TEST_RESULTS["failed"]
    pass_rate = (TEST_RESULTS["passed"] / total * 100) if total > 0 else 0
    
    print(f"Total Tests: {total}")
    print(f"Passed: {TEST_RESULTS['passed']} ✅")
    print(f"Failed: {TEST_RESULTS['failed']} ❌")
    print(f"Pass Rate: {pass_rate:.1f}%")
    
    if TEST_RESULTS["failed"] > 0:
        print("\nFailed Tests:")
        for error in TEST_RESULTS["errors"]:
            print(f"  • {error}")
    
    print("\n" + "=" * 60)
    
    if pass_rate >= 90:
        print("🎉 EXCELLENT! System is ready for production!")
    elif pass_rate >= 70:
        print("⚠️  GOOD! Some minor issues to fix.")
    else:
        print("❌ CRITICAL! Major issues need attention.")
    
    print("=" * 60)
    
    return TEST_RESULTS["failed"] == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
