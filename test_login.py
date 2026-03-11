#!/usr/bin/env python3
"""
Test login endpoint to see exact error
"""
import requests
import json
import sys

def test_login(base_url="https://your-app.onrender.com"):
    """Test login endpoint"""
    print(f"🧪 Testing login endpoint: {base_url}")
    
    # Test data
    login_data = {
        "email": "inspector1@solartech.com",
        "password": "password123",
        "companyId": "SOLARTECH-001"
    }
    
    try:
        # Test login
        response = requests.post(
            f"{base_url}/api/v1/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Login successful!")
        else:
            print("❌ Login failed")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        test_login(sys.argv[1])
    else:
        print("Usage: python test_login.py https://your-app.onrender.com")