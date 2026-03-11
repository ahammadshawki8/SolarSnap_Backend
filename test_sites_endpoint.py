#!/usr/bin/env python3
"""
Test the sites endpoint to debug the 500 error
"""
import requests
import json

def test_sites_endpoint():
    """Test the sites API endpoint"""
    base_url = "https://solarsnap-backend.onrender.com"
    
    print("🔍 Testing SolarSnap Sites Endpoint")
    print("=" * 50)
    
    # Test health first
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        print(f"Health Check: {response.status_code}")
        if response.status_code == 200:
            health_data = response.json()
            print(f"  Database: {health_data.get('database')}")
            print(f"  Environment: {health_data.get('environment')}")
        print()
    except Exception as e:
        print(f"Health Check Failed: {e}")
        return
    
    # Test sites endpoint
    try:
        print("Testing /api/v1/sites endpoint...")
        response = requests.get(f"{base_url}/api/v1/sites", timeout=30)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Sites endpoint working!")
            print(f"Number of sites: {len(data.get('sites', []))}")
            
            # Show first site as example
            if data.get('sites'):
                first_site = data['sites'][0]
                print(f"First site: {first_site.get('siteName')} ({first_site.get('siteId')})")
                
        else:
            print("❌ Sites endpoint failed")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Sites endpoint test failed: {e}")
    
    print("=" * 50)

if __name__ == '__main__':
    test_sites_endpoint()