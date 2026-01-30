#!/usr/bin/env python3
"""
Backend API Testing for NotCluely Shared Profile Scheduler
Tests all endpoints including user registration, booking CRUD, conflicts, and timezone handling
"""

import requests
import sys
import json
from datetime import datetime, timezone, timedelta
import uuid

class NotCluelyAPITester:
    def __init__(self, base_url="https://profilesched.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_users = []
        self.test_bookings = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
        return success

    def test_api_health(self):
        """Test basic API connectivity"""
        try:
            response = requests.get(f"{self.api_url}/", timeout=10)
            success = response.status_code == 200 and "NotCluely API" in response.text
            return self.log_test("API Health Check", success, f"Status: {response.status_code}")
        except Exception as e:
            return self.log_test("API Health Check", False, str(e))

    def test_timezone_endpoint(self):
        """Test timezone listing endpoint"""
        try:
            response = requests.get(f"{self.api_url}/timezones", timeout=10)
            success = response.status_code == 200
            if success:
                data = response.json()
                success = "timezones" in data and len(data["timezones"]) > 0
            return self.log_test("Timezone Endpoint", success, f"Status: {response.status_code}")
        except Exception as e:
            return self.log_test("Timezone Endpoint", False, str(e))

    def test_user_registration_normal(self):
        """Test normal user registration"""
        try:
            fingerprint = f"test_fp_{uuid.uuid4().hex[:8]}"
            user_data = {
                "name": "Test User",
                "fingerprint": fingerprint,
                "timezone": "America/New_York"
            }
            
            response = requests.post(f"{self.api_url}/users/register", json=user_data, timeout=10)
            success = response.status_code == 200
            
            if success:
                user = response.json()
                success = (user["name"] == "Test User" and 
                          user["fingerprint"] == fingerprint and
                          user["is_admin"] == False)
                if success:
                    self.test_users.append(user)
            
            return self.log_test("Normal User Registration", success, f"Status: {response.status_code}")
        except Exception as e:
            return self.log_test("Normal User Registration", False, str(e))

    def test_user_registration_admin(self):
        """Test admin user registration (rutvik case-insensitive)"""
        try:
            fingerprint = f"admin_fp_{uuid.uuid4().hex[:8]}"
            user_data = {
                "name": "RUTVIK",  # Test case-insensitive
                "fingerprint": fingerprint,
                "timezone": "America/Los_Angeles"
            }
            
            response = requests.post(f"{self.api_url}/users/register", json=user_data, timeout=10)
            success = response.status_code == 200
            
            if success:
                user = response.json()
                success = (user["name"] == "RUTVIK" and 
                          user["fingerprint"] == fingerprint and
                          user["is_admin"] == True)
                if success:
                    self.test_users.append(user)
            
            return self.log_test("Admin User Registration (rutvik)", success, f"Status: {response.status_code}")
        except Exception as e:
            return self.log_test("Admin User Registration (rutvik)", False, str(e))

    def test_user_fingerprint_lookup(self):
        """Test user lookup by fingerprint"""
        if not self.test_users:
            return self.log_test("User Fingerprint Lookup", False, "No test users available")
        
        try:
            user = self.test_users[0]
            response = requests.get(f"{self.api_url}/users/by-fingerprint/{user['fingerprint']}", timeout=10)
            success = response.status_code == 200
            
            if success:
                fetched_user = response.json()
                success = fetched_user["id"] == user["id"]
            
            return self.log_test("User Fingerprint Lookup", success, f"Status: {response.status_code}")
        except Exception as e:
            return self.log_test("User Fingerprint Lookup", False, str(e))

    def test_get_all_users(self):
        """Test getting all users"""
        try:
            response = requests.get(f"{self.api_url}/users", timeout=10)
            success = response.status_code == 200
            
            if success:
                users = response.json()
                success = isinstance(users, list) and len(users) >= len(self.test_users)
            
            return self.log_test("Get All Users", success, f"Status: {response.status_code}")
        except Exception as e:
            return self.log_test("Get All Users", False, str(e))

    def test_create_booking_no_conflict(self):
        """Test creating a booking without conflicts"""
        if not self.test_users:
            return self.log_test("Create Booking (No Conflict)", False, "No test users available")
        
        try:
            user = self.test_users[0]
            
            # Create booking for tomorrow at 10 AM UTC
            tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
            start_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
            end_time = start_time + timedelta(hours=1)
            
            booking_data = {
                "title": "Test Meeting",
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "notes": "Test booking notes",
                "user_timezone": user["timezone"]
            }
            
            response = requests.post(
                f"{self.api_url}/bookings?user_id={user['id']}", 
                json=booking_data, 
                timeout=10
            )
            success = response.status_code == 200
            
            if success:
                booking = response.json()
                success = (booking["title"] == "Test Meeting" and 
                          booking["user_id"] == user["id"])
                if success:
                    self.test_bookings.append(booking)
            
            return self.log_test("Create Booking (No Conflict)", success, f"Status: {response.status_code}")
        except Exception as e:
            return self.log_test("Create Booking (No Conflict)", False, str(e))

    def test_create_conflicting_booking(self):
        """Test creating a conflicting booking"""
        if not self.test_users or len(self.test_users) < 2 or not self.test_bookings:
            return self.log_test("Create Conflicting Booking", False, "Insufficient test data")
        
        try:
            user = self.test_users[1]  # Different user
            existing_booking = self.test_bookings[0]
            
            # Create overlapping booking
            booking_data = {
                "title": "Conflicting Meeting",
                "start_time": existing_booking["start_time"],
                "end_time": existing_booking["end_time"],
                "notes": "This should conflict",
                "user_timezone": user["timezone"]
            }
            
            response = requests.post(
                f"{self.api_url}/bookings?user_id={user['id']}", 
                json=booking_data, 
                timeout=10
            )
            success = response.status_code == 200
            
            if success:
                booking = response.json()
                success = booking["title"] == "Conflicting Meeting"
                if success:
                    self.test_bookings.append(booking)
            
            return self.log_test("Create Conflicting Booking", success, f"Status: {response.status_code}")
        except Exception as e:
            return self.log_test("Create Conflicting Booking", False, str(e))

    def test_get_bookings(self):
        """Test getting all bookings"""
        try:
            response = requests.get(f"{self.api_url}/bookings", timeout=10)
            success = response.status_code == 200
            
            if success:
                bookings = response.json()
                success = isinstance(bookings, list) and len(bookings) >= len(self.test_bookings)
            
            return self.log_test("Get All Bookings", success, f"Status: {response.status_code}")
        except Exception as e:
            return self.log_test("Get All Bookings", False, str(e))

    def test_get_conflicts(self):
        """Test getting conflicts"""
        try:
            response = requests.get(f"{self.api_url}/conflicts", timeout=10)
            success = response.status_code == 200
            
            if success:
                conflicts = response.json()
                success = isinstance(conflicts, list)
                # Should have at least one conflict from our conflicting booking test
                if len(self.test_bookings) >= 2:
                    success = success and len(conflicts) > 0
            
            return self.log_test("Get Conflicts", success, f"Status: {response.status_code}")
        except Exception as e:
            return self.log_test("Get Conflicts", False, str(e))

    def test_get_user_conflicts(self):
        """Test getting user-specific conflicts"""
        if not self.test_users:
            return self.log_test("Get User Conflicts", False, "No test users available")
        
        try:
            user = self.test_users[0]
            response = requests.get(f"{self.api_url}/conflicts/user/{user['id']}", timeout=10)
            success = response.status_code == 200
            
            if success:
                conflicts = response.json()
                success = isinstance(conflicts, list)
            
            return self.log_test("Get User Conflicts", success, f"Status: {response.status_code}")
        except Exception as e:
            return self.log_test("Get User Conflicts", False, str(e))

    def test_update_user_timezone(self):
        """Test updating user timezone"""
        if not self.test_users:
            return self.log_test("Update User Timezone", False, "No test users available")
        
        try:
            user = self.test_users[0]
            new_timezone = "Europe/London"
            
            response = requests.put(
                f"{self.api_url}/users/{user['id']}/timezone?timezone={new_timezone}", 
                timeout=10
            )
            success = response.status_code == 200
            
            if success:
                result = response.json()
                success = result.get("success") == True
            
            return self.log_test("Update User Timezone", success, f"Status: {response.status_code}")
        except Exception as e:
            return self.log_test("Update User Timezone", False, str(e))

    def test_delete_booking_owner(self):
        """Test deleting booking by owner"""
        if not self.test_bookings or not self.test_users:
            return self.log_test("Delete Booking (Owner)", False, "No test data available")
        
        try:
            booking = self.test_bookings[0]
            user = self.test_users[0]
            
            response = requests.delete(
                f"{self.api_url}/bookings/{booking['id']}?user_id={user['id']}", 
                timeout=10
            )
            success = response.status_code == 200
            
            if success:
                result = response.json()
                success = result.get("success") == True
            
            return self.log_test("Delete Booking (Owner)", success, f"Status: {response.status_code}")
        except Exception as e:
            return self.log_test("Delete Booking (Owner)", False, str(e))

    def test_delete_booking_admin(self):
        """Test deleting booking by admin"""
        if len(self.test_bookings) < 2 or len(self.test_users) < 2:
            return self.log_test("Delete Booking (Admin)", False, "Insufficient test data")
        
        try:
            booking = self.test_bookings[1]  # Booking by second user
            admin_user = next((u for u in self.test_users if u.get("is_admin")), None)
            
            if not admin_user:
                return self.log_test("Delete Booking (Admin)", False, "No admin user available")
            
            response = requests.delete(
                f"{self.api_url}/bookings/{booking['id']}?user_id={admin_user['id']}", 
                timeout=10
            )
            success = response.status_code == 200
            
            if success:
                result = response.json()
                success = result.get("success") == True
            
            return self.log_test("Delete Booking (Admin)", success, f"Status: {response.status_code}")
        except Exception as e:
            return self.log_test("Delete Booking (Admin)", False, str(e))

    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting NotCluely Backend API Tests")
        print(f"📍 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Basic connectivity
        self.test_api_health()
        self.test_timezone_endpoint()
        
        # User management
        self.test_user_registration_normal()
        self.test_user_registration_admin()
        self.test_user_fingerprint_lookup()
        self.test_get_all_users()
        
        # Booking management
        self.test_create_booking_no_conflict()
        self.test_create_conflicting_booking()
        self.test_get_bookings()
        
        # Conflict management
        self.test_get_conflicts()
        self.test_get_user_conflicts()
        
        # Updates and deletions
        self.test_update_user_timezone()
        self.test_delete_booking_owner()
        self.test_delete_booking_admin()
        
        # Summary
        print("=" * 60)
        print(f"📊 Tests completed: {self.tests_passed}/{self.tests_run}")
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"📈 Success rate: {success_rate:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            print("⚠️  Some tests failed - check logs above")
            return 1

def main():
    tester = NotCluelyAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())