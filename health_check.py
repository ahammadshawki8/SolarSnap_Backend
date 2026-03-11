#!/usr/bin/env python3
"""
Health check script for SolarSnap Backend
Can be used for monitoring and load balancer health checks
"""
import requests
import sys
import os
from datetime import datetime

def check_health(base_url=None):
    """Check application health"""
    if not base_url:
        base_url = os.getenv('BASE_URL', 'http://localhost:5000')
    
    print(f"🔍 Checking health of {base_url}")
    
    try:
        # Check main health endpoint
        response = requests.get(f"{base_url}/health", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Health check passed")
            print(f"   Status: {data.get('status')}")
            print(f"   Database: {data.get('database')}")
            print(f"   Environment: {data.get('environment')}")
            return True
        else:
            print(f"❌ Health check failed with status {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check failed: {e}")
        return False

def check_api_endpoints(base_url=None):
    """Check critical API endpoints"""
    if not base_url:
        base_url = os.getenv('BASE_URL', 'http://localhost:5000')
    
    endpoints = [
        '/',
        '/health',
        '/api/v1/auth/login'  # Should return 400/422 for missing data, not 500
    ]
    
    print(f"🔍 Checking API endpoints...")
    
    all_good = True
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code < 500:  # Any non-server error is acceptable
                print(f"   ✅ {endpoint} - {response.status_code}")
            else:
                print(f"   ❌ {endpoint} - {response.status_code}")
                all_good = False
        except Exception as e:
            print(f"   ❌ {endpoint} - Error: {e}")
            all_good = False
    
    return all_good

def main():
    """Main health check function"""
    print(f"🏥 SolarSnap Backend Health Check - {datetime.now()}")
    print("=" * 50)
    
    base_url = sys.argv[1] if len(sys.argv) > 1 else None
    
    # Basic health check
    health_ok = check_health(base_url)
    
    # API endpoints check
    api_ok = check_api_endpoints(base_url)
    
    print("=" * 50)
    
    if health_ok and api_ok:
        print("🎉 All checks passed!")
        sys.exit(0)
    else:
        print("💥 Some checks failed!")
        sys.exit(1)

if __name__ == '__main__':
    main()