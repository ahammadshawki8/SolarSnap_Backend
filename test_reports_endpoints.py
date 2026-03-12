#!/usr/bin/env python3
"""
Test script for the new reports endpoints
"""

import requests
import json
import sys

# Test configuration
BASE_URL = "https://solarsnap-backend.onrender.com"
# BASE_URL = "http://localhost:5000"  # For local testing

def test_endpoint(method, endpoint, data=None, params=None):
    """Test a single endpoint"""
    url = f"{BASE_URL}/api/v1/reports{endpoint}"
    
    try:
        if method == 'GET':
            response = requests.get(url, params=params, timeout=10)
        elif method == 'POST':
            response = requests.post(url, json=data, timeout=10)
        elif method == 'DELETE':
            response = requests.delete(url, json=data, timeout=10)
        
        print(f"\n{method} {endpoint}")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ SUCCESS")
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
    """Test all new endpoints"""
    print("🧪 Testing SolarSnap Reports API Endpoints")
    print("=" * 50)
    
    # Test basic endpoints
    tests = [
        # Dashboard stats
        ('GET', '/dashboard-stats', None, {'siteId': 'NV-Solar-04'}),
        
        # Report generation
        ('POST', '/generate', {
            'reportType': 'site',
            'siteId': 'NV-Solar-04',
            'dateRange': {}
        }, None),
        
        # Export data
        ('POST', '/export-data', {
            'format': 'csv',
            'siteId': 'NV-Solar-04'
        }, None),
        
        # Export history
        ('POST', '/export-history', {
            'format': 'json',
            'severity': 'all'
        }, None),
        
        # Cloud sync
        ('POST', '/cloud-sync', {
            'siteId': 'NV-Solar-04',
            'syncType': 'incremental'
        }, None),
        
        # Temperature distribution
        ('GET', '/temperature-distribution', None, {'siteId': 'NV-Solar-04'}),
    ]
    
    passed = 0
    total = len(tests)
    
    for method, endpoint, data, params in tests:
        if test_endpoint(method, endpoint, data, params):
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All endpoints working correctly!")
        return 0
    else:
        print("⚠️  Some endpoints need attention")
        return 1

if __name__ == "__main__":
    sys.exit(main())