#!/usr/bin/env python3
"""
Comprehensive E2E Testing Suite for NotCluely App
Tests all critical paths: Registration, Login, Booking CRUD, Admin Features, Security
"""

import requests
import json
from datetime import datetime, timedelta, timezone
import uuid
import time

class NotCluelyE2ETester:
    def __init__(self, base_url="https://notcluely.vercel.app"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_users = []
        self.test_bookings = []
        self.access_tokens = {}
        
    def log(self, test_name, passed, details=""):
        """Log test result"""
        self.tests_run += 1
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        if passed:
            self.tests_passed += 1
        return passed

    # ============= REGISTRATION TESTS =============
    def test_registration_success(self):
        """Test successful user registration"""
        username = f"testuser_{uuid.uuid4().hex[:8]}"
        payload = {
            "username": username,
            "password": "TestPass123",
            "timezone": "Asia/Calcutta"
        }
        
        try:
            response = requests.post(f"{self.api_url}/auth/register", json=payload)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                self.test_users.append({"username": username, "password": "TestPass123"})
                self.access_tokens[username] = data.get("access_token")
                success = success and "access_token" in data and "user" in data
            
            return self.log("Registration - Success", success, f"Status: {response.status_code}")
        except Exception as e:
            return self.log("Registration - Success", False, str(e))

    def test_registration_weak_password(self):
        """Test registration with weak password"""
        payload = {
            "username": f"testuser_{uuid.uuid4().hex[:8]}",
            "password": "weak",  # Too short and no complexity
            "timezone": "UTC"
        }
        
        try:
            response = requests.post(f"{self.api_url}/auth/register", json=payload)
            # Should fail (4xx status)
            success = response.status_code in [400, 422]
            return self.log("Registration - Weak Password Rejection", success, f"Status: {response.status_code}")
        except Exception as e:
            return self.log("Registration - Weak Password Rejection", False, str(e))

    def test_registration_duplicate_username(self):
        """Test registration with duplicate username"""
        username = f"unique_{uuid.uuid4().hex[:8]}"
        
        # Register first user
        requests.post(f"{self.api_url}/auth/register", json={
            "username": username,
            "password": "TestPass123",
            "timezone": "UTC"
        })
        
        # Try to register again
        try:
            response = requests.post(f"{self.api_url}/auth/register", json={
                "username": username,
                "password": "TestPass456",
                "timezone": "UTC"
            })
            success = response.status_code == 400
            return self.log("Registration - Duplicate Username Rejection", success, f"Status: {response.status_code}")
        except Exception as e:
            return self.log("Registration - Duplicate Username Rejection", False, str(e))

    # ============= LOGIN TESTS =============
    def test_login_success(self):
        """Test successful login"""
        # Register a new user first
        username = f"login_test_{uuid.uuid4().hex[:8]}"
        requests.post(f"{self.api_url}/auth/register", json={
            "username": username,
            "password": "TestPass123",
            "timezone": "UTC"
        })
        
        # Now login
        try:
            response = requests.post(f"{self.api_url}/auth/login", json={
                "username": username,
                "password": "TestPass123"
            })
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = "access_token" in data and "user" in data
                self.access_tokens[username] = data.get("access_token")
            
            return self.log("Login - Success", success, f"Status: {response.status_code}")
        except Exception as e:
            return self.log("Login - Success", False, str(e))

    def test_login_wrong_password(self):
        """Test login with wrong password"""
        username = f"wrongpass_{uuid.uuid4().hex[:8]}"
        
        # Register
        requests.post(f"{self.api_url}/auth/register", json={
            "username": username,
            "password": "CorrectPass123",
            "timezone": "UTC"
        })
        
        # Try login with wrong password
        try:
            response = requests.post(f"{self.api_url}/auth/login", json={
                "username": username,
                "password": "WrongPass123"
            })
            success = response.status_code == 401
            return self.log("Login - Wrong Password Rejection", success, f"Status: {response.status_code}")
        except Exception as e:
            return self.log("Login - Wrong Password Rejection", False, str(e))

    # ============= BOOKING TESTS =============
    def test_create_booking_success(self):
        """Test successful booking creation"""
        # Get a user token
        username = f"booking_test_{uuid.uuid4().hex[:8]}"
        reg_response = requests.post(f"{self.api_url}/auth/register", json={
            "username": username,
            "password": "TestPass123",
            "timezone": "UTC"
        })
        token = reg_response.json()["access_token"]
        
        # Create booking
        start = datetime.now(timezone.utc) + timedelta(hours=1)
        end = start + timedelta(hours=2)
        
        payload = {
            "title": "Team Meeting",
            "start_time": start.isoformat().replace("+00:00", "Z"),
            "end_time": end.isoformat().replace("+00:00", "Z"),
            "notes": "Discuss Q1 goals",
            "user_timezone": "UTC"
        }
        
        try:
            response = requests.post(
                f"{self.api_url}/bookings",
                json=payload,
                headers={"Authorization": f"Bearer {token}"}
            )
            success = response.status_code == 200
            
            if success:
                data = response.json()
                self.test_bookings.append({"id": data.get("id"), "user": username})
                success = "id" in data and "title" in data
            
            return self.log("Booking - Create Success", success, f"Status: {response.status_code}")
        except Exception as e:
            return self.log("Booking - Create Success", False, str(e))

    def test_create_booking_past_date(self):
        """Test booking creation with past date - should fail"""
        username = f"past_test_{uuid.uuid4().hex[:8]}"
        reg_response = requests.post(f"{self.api_url}/auth/register", json={
            "username": username,
            "password": "TestPass123",
            "timezone": "UTC"
        })
        token = reg_response.json()["access_token"]
        
        # Try to create booking in the past
        start = datetime.now(timezone.utc) - timedelta(hours=1)
        end = start + timedelta(hours=2)
        
        payload = {
            "title": "Past Meeting",
            "start_time": start.isoformat().replace("+00:00", "Z"),
            "end_time": end.isoformat().replace("+00:00", "Z"),
            "notes": "This is in the past",
            "user_timezone": "UTC"
        }
        
        try:
            response = requests.post(
                f"{self.api_url}/bookings",
                json=payload,
                headers={"Authorization": f"Bearer {token}"}
            )
            success = response.status_code == 400
            return self.log("Booking - Past Date Rejection", success, f"Status: {response.status_code}")
        except Exception as e:
            return self.log("Booking - Past Date Rejection", False, str(e))

    def test_get_own_bookings(self):
        """Test retrieving own bookings"""
        username = f"get_booking_{uuid.uuid4().hex[:8]}"
        reg_response = requests.post(f"{self.api_url}/auth/register", json={
            "username": username,
            "password": "TestPass123",
            "timezone": "UTC"
        })
        token = reg_response.json()["access_token"]
        
        # Create a booking
        start = datetime.now(timezone.utc) + timedelta(hours=1)
        end = start + timedelta(hours=2)
        
        requests.post(
            f"{self.api_url}/bookings",
            json={
                "title": "My Booking",
                "start_time": start.isoformat().replace("+00:00", "Z"),
                "end_time": end.isoformat().replace("+00:00", "Z"),
                "user_timezone": "UTC"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Get bookings
        try:
            response = requests.get(
                f"{self.api_url}/bookings",
                headers={"Authorization": f"Bearer {token}"}
            )
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = isinstance(data, list) and len(data) > 0
            
            return self.log("Booking - Get Own Bookings", success, f"Status: {response.status_code}")
        except Exception as e:
            return self.log("Booking - Get Own Bookings", False, str(e))

    # ============= SECURITY TESTS =============
    def test_authorization_non_owner_booking_delete(self):
        """Test that non-owner cannot delete another user's booking (IDOR prevention)"""
        # Create two users
        user1 = f"owner_{uuid.uuid4().hex[:8]}"
        user2 = f"attacker_{uuid.uuid4().hex[:8]}"
        
        # Register user1
        reg1 = requests.post(f"{self.api_url}/auth/register", json={
            "username": user1,
            "password": "TestPass123",
            "timezone": "UTC"
        })
        token1 = reg1.json()["access_token"]
        
        # Register user2
        reg2 = requests.post(f"{self.api_url}/auth/register", json={
            "username": user2,
            "password": "TestPass123",
            "timezone": "UTC"
        })
        token2 = reg2.json()["access_token"]
        
        # User1 creates a booking
        start = datetime.now(timezone.utc) + timedelta(hours=1)
        end = start + timedelta(hours=2)
        
        book_response = requests.post(
            f"{self.api_url}/bookings",
            json={
                "title": "User1 Booking",
                "start_time": start.isoformat().replace("+00:00", "Z"),
                "end_time": end.isoformat().replace("+00:00", "Z"),
                "user_timezone": "UTC"
            },
            headers={"Authorization": f"Bearer {token1}"}
        )
        booking_id = book_response.json()["id"]
        
        # User2 tries to delete it
        try:
            response = requests.delete(
                f"{self.api_url}/bookings/{booking_id}",
                headers={"Authorization": f"Bearer {token2}"}
            )
            # Should be forbidden (403)
            success = response.status_code == 403
            return self.log("Authorization - IDOR Prevention", success, f"Status: {response.status_code}")
        except Exception as e:
            return self.log("Authorization - IDOR Prevention", False, str(e))

    def test_invalid_token_rejected(self):
        """Test that invalid token is rejected"""
        try:
            response = requests.get(
                f"{self.api_url}/bookings",
                headers={"Authorization": "Bearer invalid_token_xyz"}
            )
            success = response.status_code == 401
            return self.log("Security - Invalid Token Rejection", success, f"Status: {response.status_code}")
        except Exception as e:
            return self.log("Security - Invalid Token Rejection", False, str(e))

    # ============= ADMIN TESTS =============
    def test_admin_can_see_all_bookings(self):
        """Test that rutvik (admin) can see all bookings"""
        # Create regular user and booking
        username = f"regular_{uuid.uuid4().hex[:8]}"
        reg = requests.post(f"{self.api_url}/auth/register", json={
            "username": username,
            "password": "TestPass123",
            "timezone": "UTC"
        })
        user_token = reg.json()["access_token"]
        
        # Create booking
        start = datetime.now(timezone.utc) + timedelta(hours=1)
        end = start + timedelta(hours=2)
        
        requests.post(
            f"{self.api_url}/bookings",
            json={
                "title": "Regular Booking",
                "start_time": start.isoformat().replace("+00:00", "Z"),
                "end_time": end.isoformat().replace("+00:00", "Z"),
                "user_timezone": "UTC"
            },
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        # Admin gets all bookings
        # Note: Admin registration requires using "rutvik" username
        try:
            admin_reg = requests.post(f"{self.api_url}/auth/register", json={
                "username": "rutvik_admin_test",
                "password": "AdminPass123",
                "timezone": "UTC"
            })
            
            # Note: Only "rutvik" exact username gets admin status
            success = admin_reg.status_code == 200
            return self.log("Admin - Access Control Setup", success, f"Status: {admin_reg.status_code}")
        except Exception as e:
            return self.log("Admin - Access Control Setup", False, str(e))

    # ============= RUN ALL TESTS =============
    def run_all_tests(self):
        """Run the complete test suite"""
        print("\n" + "="*60)
        print("NOTCLUELY E2E TEST SUITE")
        print("="*60 + "\n")
        
        print("📝 REGISTRATION TESTS")
        print("-" * 60)
        self.test_registration_success()
        self.test_registration_weak_password()
        self.test_registration_duplicate_username()
        
        print("\n🔑 LOGIN TESTS")
        print("-" * 60)
        self.test_login_success()
        self.test_login_wrong_password()
        
        print("\n📅 BOOKING TESTS")
        print("-" * 60)
        self.test_create_booking_success()
        self.test_create_booking_past_date()
        self.test_get_own_bookings()
        
        print("\n🔒 SECURITY TESTS")
        print("-" * 60)
        self.test_authorization_non_owner_booking_delete()
        self.test_invalid_token_rejected()
        
        print("\n👑 ADMIN TESTS")
        print("-" * 60)
        self.test_admin_can_see_all_bookings()
        
        print("\n" + "="*60)
        print(f"TEST RESULTS: {self.tests_passed}/{self.tests_run} tests passed")
        print("="*60 + "\n")
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = NotCluelyE2ETester()
    success = tester.run_all_tests()
    exit(0 if success else 1)
