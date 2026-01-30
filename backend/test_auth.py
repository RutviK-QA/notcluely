#!/usr/bin/env python
"""Quick auth test for NotCluely backend"""

import sys
import json
sys.path.insert(0, '.')

from server import (
    app, get_password_hash, verify_password, create_access_token,
    get_db, init_db
)

def test_auth():
    """Test authentication functions"""
    print("\n=== TESTING AUTHENTICATION ===\n")
    
    # Test 1: Password hashing
    print("✓ Test 1: Password hashing")
    password = "TestPassword123!"
    hashed = get_password_hash(password)
    assert verify_password(password, hashed), "Password verification failed"
    print(f"  - Password hashed: {hashed[:20]}...")
    print(f"  - Verification passed: {verify_password(password, hashed)}")
    
    # Test 2: JWT token creation
    print("\n✓ Test 2: JWT token creation")
    token = create_access_token({"sub": "test-user-id"})
    print(f"  - Token: {token[:50]}...")
    assert token, "Token not created"
    
    # Test 3: Database initialization
    print("\n✓ Test 3: Database initialization")
    init_db()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    expected_tables = ['users', 'bookings', 'conflicts']
    for table in expected_tables:
        assert table in tables, f"Table {table} not created"
        print(f"  - Table '{table}' exists ✓")
    
    print("\n=== ALL TESTS PASSED ===\n")
    print("Backend is ready for deployment!")
    print("\nNEXT STEPS:")
    print("1. Push to GitHub: git push")
    print("2. Deploy to Render.com (backend)")
    print("3. Deploy to Vercel (frontend)")
    print("4. Update REACT_APP_BACKEND_URL in frontend/.env.production")

if __name__ == '__main__':
    test_auth()
