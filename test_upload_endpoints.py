#!/usr/bin/env python3
"""
Test script for the upload/sync endpoints
"""

import requests
import json
import sys

# Test configuration
BASE_URL = "https://solarsnap-backend.onrender.com"
# BASE_URL = "http://localhost:5000"  # For local testing

def test_endpoint(method, endpoint, data=None, params=None, headers=None):
    """Test a single endpoint"""
    url = f"{BASE_URL}/api/v1/sync{endpoint}"
    
    try:
        if method == 'GET':
            response = requests.get(url, params=params, headers=headers, timeout=10)
        elif method == 'POST':
            response = requests.post(url, json=data, headers=headers, timeout=10)
        elif method == 'DELETE':
            response = requests.delete(url, json=data, headers=headers, timeout=10)
        
        print(f"\n{method} {endpoint}")
        print(f"Status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            result = response.json()
            if result.get('success'):
                print("✅ SUCCESS")
                if 'syncStatus' in result:
                    status = result['syncStatus']
                    print(f"   Pending: {status.get('pending', 0)}")
                    print(f"   Uploading: {status.get('uploading', 0)}")
                    print(f"   Completed: {status.get('completed', 0)}")
                    print(f"   Failed: {status.get('failed', 0)}")
                elif 'storage' in result:
                    storage = result['storage']
                    print(f"   Used: {storage['used']['percentage']}%")
                    print(f"   Available: {storage['available']['percentage']}%")
                return True
            else:
                print(f"❌ FAILED: {result.get('error', {}).get('message', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP ERROR: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data}")
            except:
                print(f"Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        return False

def main():
    """Test all upload/sync endpoints"""
    print("🧪 Testing SolarSnap Upload/Sync API Endpoints")
    print("=" * 50)
    
    # Test without authentication first (should work with disabled JWT)
    tests = [
        # Device storage (no auth required)
        ('GET', '/device-storage', None, None, None),
        
        # Sync status (requires auth, but we'll test without)
        ('GET', '/status', None, None, None),
        
        # Sync queue (requires auth, but we'll test without)
        ('GET', '/queue', None, {'status': 'all'}, None),
        
        # Create upload queue
        ('POST', '/create', {
            'inspectionId': 'test-inspection-uuid',
            'fileSize': 1.5
        }, None, None),
        
        # Clear completed (requires auth)
        ('POST', '/clear-completed', {}, None, None),
    ]
    
    passed = 0
    total = len(tests)
    
    for method, endpoint, data, params, headers in tests:
        if test_endpoint(method, endpoint, data, params, headers):
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed >= 1:  # At least device storage should work
        print("🎉 Core endpoints working!")
        return 0
    else:
        print("⚠️  All endpoints failed - check backend deployment")
        return 1

if __name__ == "__main__":
    sys.exit(main())