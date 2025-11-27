import subprocess
import time
import requests
import json
from pathlib import Path

def test_scrape_functionality():
    print("🧪 Testing LinkedIn scraping integration...")
    
    # Check what folders exist
    backend_dir = Path(".")
    folders = [d.name for d in backend_dir.iterdir() if d.is_dir() and "Pradeep" in d.name]
    print(f"📂 Pradeep folders found: {folders}")
    
    # Check if final_summary.json exists in any of these folders
    for folder_name in folders:
        summary_file = backend_dir / folder_name / "final_summary.json"
        if summary_file.exists():
            print(f"✅ Found final_summary.json in: {folder_name}")
            
            # Try to load and display a snippet
            try:
                with open(summary_file, 'r', encoding='utf-8') as f:
                    summary = json.load(f)
                    
                print(f"📄 Summary preview:")
                if 'personal_info' in summary:
                    print(f"   Name: {summary['personal_info'].get('name', 'N/A')}")
                    print(f"   Headline: {summary['personal_info'].get('headline', 'N/A')}")
                    print(f"   Location: {summary['personal_info'].get('location', 'N/A')}")
                
                print(f"🎯 This file should be returned by the API!")
                return folder_name, summary
                
            except Exception as e:
                print(f"❌ Error reading summary: {e}")
        else:
            print(f"❌ No final_summary.json in: {folder_name}")
    
    return None, None

if __name__ == "__main__":
    test_scrape_functionality()