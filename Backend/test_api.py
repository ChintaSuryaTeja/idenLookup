#!/usr/bin/env python3
import requests
import json
from pathlib import Path

def test_scrape_status():
    # Test the scrape-status endpoint
    print("🧪 Testing /scrape-status endpoint...")
    
    # Check what folders exist
    backend_dir = Path(__file__).parent
    print(f"📁 Backend directory: {backend_dir}")
    
    folders = [d.name for d in backend_dir.iterdir() if d.is_dir() and "Pradeep" in d.name]
    print(f"📂 Pradeep folders found: {folders}")
    
    # Test the API
    try:
        response = requests.get("http://localhost:8000/scrape-status/Pradeep%20Rajgopal")
        print(f"🌐 API Response status: {response.status_code}")
        print(f"📄 API Response:")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"❌ API Error: {e}")

if __name__ == "__main__":
    test_scrape_status()