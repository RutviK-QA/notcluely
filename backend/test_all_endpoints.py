"""
Comprehensive API tests for NotCluely backend.
Tests all endpoints with proper error handling and logging.
"""

import requests
import json
from datetime import datetime, timezone, timedelta
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
BASE_URL = "http://localhost:8000/api"
# For Render: BASE_URL = "https://notcluely-backend.onrender.com/api"

# Test credentials
TEST_USER_1 = {
    "username": "testuser1",
    "password": "TestPass@123"
}

TEST_USER_2 = {
    "username": "testuser2", 
    "password": "TestPass@456"
}

ADMIN_USER = {
    "username": "rutvik",
    "password": "Qa@12345678"
}

class APITester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.tokens = {}
        self.bookings = {}
        
    def log_response(self, endpoint, method, status_code, data):
        """Log API response"""
        logger.info(f"{method} {endpoint} - Status: {status_code}")
        if status_code >= 400:
            logger.error(f"Response: {json.dumps(data, indent=2)}")
        else:
            logger.debug(f"Response: {json.dumps(data, indent=2)[:200]}...")
    
    def test_registration(self):
        """Test user registration"""
        logger.info("\n" + "="*60)
        logger.info("TESTING: User Registration")
        logger.info("="*60)
        
        for user in [TEST_USER_1, TEST_USER_2]:
            try:
                endpoint = f"{self.base_url}/auth/register"
                payload = {
                    "username": user["username"],
                    "password": user["password"],
                    "timezone": "Asia/Calcutta"
                }
                
                logger.info(f"\nRegistering user: {user['username']}")
                response = requests.post(endpoint, json=payload)
                data = response.json()
                self.log_response(endpoint, "POST", response.status_code, data)
                
                if response.status_code == 200:
                    logger.info(f"✓ Registration successful for {user['username']}")
                    self.tokens[user['username']] = data.get('access_token')
                    logger.debug(f"Token: {data.get('access_token')[:20]}...")
                else:
                    logger.error(f"✗ Registration failed: {data.get('detail')}")
                    
            except Exception as e:
                logger.error(f"✗ Exception during registration: {type(e).__name__}: {str(e)}")
    
    def test_login(self):
        """Test user login"""
        logger.info("\n" + "="*60)
        logger.info("TESTING: User Login")
        logger.info("="*60)
        
        for user in [TEST_USER_1, TEST_USER_2, ADMIN_USER]:
            try:
                endpoint = f"{self.base_url}/auth/login"
                payload = {
                    "username": user["username"],
                    "password": user["password"]
                }
                
                logger.info(f"\nLogging in user: {user['username']}")
                response = requests.post(endpoint, json=payload)
                data = response.json()
                self.log_response(endpoint, "POST", response.status_code, data)
                
                if response.status_code == 200:
                    logger.info(f"✓ Login successful for {user['username']}")
                    self.tokens[user['username']] = data.get('access_token')
                    logger.debug(f"Token: {data.get('access_token')[:20]}...")
                else:
                    logger.error(f"✗ Login failed: {data.get('detail')}")
                    
            except Exception as e:
                logger.error(f"✗ Exception during login: {type(e).__name__}: {str(e)}")
    
    def test_get_me(self):
        """Test get current user info"""
        logger.info("\n" + "="*60)
        logger.info("TESTING: Get Current User Info")
        logger.info("="*60)
        
        for username, token in self.tokens.items():
            try:
                endpoint = f"{self.base_url}/auth/me"
                headers = {"Authorization": f"Bearer {token}"}
                
                logger.info(f"\nFetching user info for: {username}")
                response = requests.get(endpoint, headers=headers)
                data = response.json()
                self.log_response(endpoint, "GET", response.status_code, data)
                
                if response.status_code == 200:
                    logger.info(f"✓ Get me successful for {username}")
                else:
                    logger.error(f"✗ Get me failed: {data.get('detail')}")
                    
            except Exception as e:
                logger.error(f"✗ Exception during get me: {type(e).__name__}: {str(e)}")
    
    def test_create_bookings(self):
        """Test creating bookings"""
        logger.info("\n" + "="*60)
        logger.info("TESTING: Create Bookings")
        logger.info("="*60)
        
        # Create bookings for test users
        users_to_book = [TEST_USER_1, TEST_USER_2]
        
        for i, user in enumerate(users_to_book):
            try:
                if user['username'] not in self.tokens:
                    logger.warning(f"No token for {user['username']}, skipping...")
                    continue
                
                endpoint = f"{self.base_url}/bookings"
                token = self.tokens[user['username']]
                headers = {"Authorization": f"Bearer {token}"}
                
                # Create booking starting tomorrow
                now = datetime.now(timezone.utc)
                start_time = now + timedelta(days=1, hours=i*2)  # Stagger bookings
                end_time = start_time + timedelta(hours=1)
                
                payload = {
                    "title": f"Meeting {i+1} by {user['username']}",
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "notes": f"Test booking {i+1}",
                    "user_timezone": "Asia/Calcutta"
                }
                
                logger.info(f"\nCreating booking for {user['username']}")
                logger.debug(f"Start: {start_time.isoformat()}, End: {end_time.isoformat()}")
                response = requests.post(endpoint, json=payload, headers=headers)
                data = response.json()
                self.log_response(endpoint, "POST", response.status_code, data)
                
                if response.status_code == 200:
                    logger.info(f"✓ Booking created successfully")
                    self.bookings[user['username']] = data.get('id')
                    logger.debug(f"Booking ID: {data.get('id')}")
                else:
                    logger.error(f"✗ Booking creation failed: {data.get('detail')}")
                    
            except Exception as e:
                logger.error(f"✗ Exception during create booking: {type(e).__name__}: {str(e)}", exc_info=True)
    
    def test_get_bookings(self):
        """Test fetching bookings"""
        logger.info("\n" + "="*60)
        logger.info("TESTING: Get Bookings")
        logger.info("="*60)
        
        for username, token in self.tokens.items():
            try:
                endpoint = f"{self.base_url}/bookings"
                headers = {"Authorization": f"Bearer {token}"}
                
                logger.info(f"\nFetching bookings for: {username}")
                response = requests.get(endpoint, headers=headers)
                data = response.json()
                self.log_response(endpoint, "GET", response.status_code, data)
                
                if response.status_code == 200:
                    logger.info(f"✓ Retrieved {len(data)} bookings")
                else:
                    logger.error(f"✗ Get bookings failed: {data.get('detail')}")
                    
            except Exception as e:
                logger.error(f"✗ Exception during get bookings: {type(e).__name__}: {str(e)}")
    
    def test_get_conflicts(self):
        """Test fetching conflicts"""
        logger.info("\n" + "="*60)
        logger.info("TESTING: Get Conflicts")
        logger.info("="*60)
        
        for username, token in self.tokens.items():
            try:
                endpoint = f"{self.base_url}/conflicts"
                headers = {"Authorization": f"Bearer {token}"}
                
                logger.info(f"\nFetching conflicts for: {username}")
                response = requests.get(endpoint, headers=headers)
                data = response.json()
                self.log_response(endpoint, "GET", response.status_code, data)
                
                if response.status_code == 200:
                    logger.info(f"✓ Retrieved {len(data)} conflicts")
                else:
                    logger.error(f"✗ Get conflicts failed: {data.get('detail')}")
                    
            except Exception as e:
                logger.error(f"✗ Exception during get conflicts: {type(e).__name__}: {str(e)}")
    
    def test_get_timezones(self):
        """Test fetching timezones"""
        logger.info("\n" + "="*60)
        logger.info("TESTING: Get Timezones")
        logger.info("="*60)
        
        try:
            endpoint = f"{self.base_url}/timezones"
            
            logger.info("\nFetching available timezones...")
            response = requests.get(endpoint)
            data = response.json()
            self.log_response(endpoint, "GET", response.status_code, {})
            
            if response.status_code == 200:
                logger.info(f"✓ Retrieved {len(data)} timezones")
            else:
                logger.error(f"✗ Get timezones failed")
                
        except Exception as e:
            logger.error(f"✗ Exception during get timezones: {type(e).__name__}: {str(e)}")
    
    def test_delete_bookings(self):
        """Test deleting bookings"""
        logger.info("\n" + "="*60)
        logger.info("TESTING: Delete Bookings")
        logger.info("="*60)
        
        for username, booking_id in self.bookings.items():
            try:
                if username not in self.tokens:
                    logger.warning(f"No token for {username}, skipping...")
                    continue
                
                endpoint = f"{self.base_url}/bookings/{booking_id}"
                token = self.tokens[username]
                headers = {"Authorization": f"Bearer {token}"}
                
                logger.info(f"\nDeleting booking {booking_id} for: {username}")
                response = requests.delete(endpoint, headers=headers)
                data = response.json()
                self.log_response(endpoint, "DELETE", response.status_code, data)
                
                if response.status_code == 200:
                    logger.info(f"✓ Booking deleted successfully")
                else:
                    logger.error(f"✗ Delete booking failed: {data.get('detail')}")
                    
            except Exception as e:
                logger.error(f"✗ Exception during delete booking: {type(e).__name__}: {str(e)}")
    
    def run_all_tests(self):
        """Run all API tests"""
        logger.info("\n\n" + "="*60)
        logger.info("NOTCLUELY API COMPREHENSIVE TEST SUITE")
        logger.info("="*60)
        
        self.test_registration()
        self.test_login()
        self.test_get_me()
        self.test_get_timezones()
        self.test_create_bookings()
        self.test_get_bookings()
        self.test_get_conflicts()
        self.test_delete_bookings()
        
        logger.info("\n\n" + "="*60)
        logger.info("TEST SUITE COMPLETE")
        logger.info("="*60 + "\n")

if __name__ == "__main__":
    tester = APITester(BASE_URL)
    tester.run_all_tests()
