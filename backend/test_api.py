#!/usr/bin/env python3
"""
Simple script to test the AInki API and see error logs
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_endpoints():
    print("🧪 Testing AInki API Endpoints")
    print("=" * 50)
    
    # Test health endpoint
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        print(f"✅ Health check: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
    
    print()
    
    # Test debug routes
    try:
        response = requests.get(f"{BASE_URL}/api/debug/routes")
        print(f"✅ Available routes: {response.status_code}")
        routes = response.json()["routes"]
        for route in routes:
            print(f"   {route['methods']} {route['path']}")
    except Exception as e:
        print(f"❌ Routes check failed: {e}")
    
    print()
    
    # Test debug logging
    try:
        response = requests.get(f"{BASE_URL}/api/debug/log")
        print(f"✅ Debug log test: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"❌ Debug log test failed: {e}")
    
    print()
    
    # Test registration (this should show errors in logs)
    try:
        test_user = {
            "username": "testuser",
            "password": "testpass",
            "gmail": "test@example.com"
        }
        response = requests.post(f"{BASE_URL}/api/auth/register", json=test_user)
        print(f"✅ Registration test: {response.status_code}")
        if response.status_code != 200:
            print(f"   Error: {response.json()}")
        else:
            print(f"   Success: {response.json()}")
    except Exception as e:
        print(f"❌ Registration test failed: {e}")

if __name__ == "__main__":
    test_endpoints()
