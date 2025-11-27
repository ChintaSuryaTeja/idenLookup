from fastapi import FastAPI
from fastapi.testclient import TestClient
import sys
import os

# Add the current directory to sys.path to import api
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from api import app
    
    # Create a test client
    client = TestClient(app)
    
    print("🧪 Testing /scrape-status endpoint...")
    
    # Test with the actual name we expect from the dashboard
    test_name = "Pradeep Rajgopal"  # This is what comes from dashboard
    
    response = client.get(f"/scrape-status/{test_name}")
    
    print(f"📡 Request: GET /scrape-status/{test_name}")
    print(f"📊 Status Code: {response.status_code}")
    print(f"📄 Response: {response.json()}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get("status") == "completed" and "summary" in data:
            print("✅ SUCCESS: API found the completed scraping results!")
            summary = data["summary"]
            print(f"🎯 Name: {summary.get('personal_info', {}).get('name')}")
            print(f"🎯 Headline: {summary.get('personal_info', {}).get('headline')}")
        elif data.get("status") == "not_found":
            print("❌ ISSUE: API could not find matching folder")
        else:
            print(f"⚠️ Unexpected status: {data.get('status')}")
    else:
        print(f"❌ API Error: {response.status_code}")
        
except Exception as e:
    print(f"❌ Error importing or testing: {e}")
    import traceback
    traceback.print_exc()