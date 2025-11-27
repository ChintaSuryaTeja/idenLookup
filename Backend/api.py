import os
import json
import shutil
import subprocess
import sys
import glob
import logging
from pathlib import Path
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

TEMP_INPUT = "uploaded_input.jpg"
OUTPUT_JSON = "top_matches.json"


class ProfileRequest(BaseModel):
    profile_url: str


@app.post("/match")
async def match(file: UploadFile = File(...)):
    with open(TEMP_INPUT, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    process = subprocess.Popen(
        [sys.executable, "final_facial_embedding.py", TEMP_INPUT],
        stdout=sys.stdout,
        stderr=sys.stderr
    )
    process.wait()

    if not os.path.exists(OUTPUT_JSON):
        return {"success": False, "results": []}

    with open(OUTPUT_JSON, "r") as f:
        raw = json.load(f)

    formatted = []
    for r in raw:
        similarity_percent = int(r["similarity"] * 100)
        formatted.append({
            "name": r["name"],
            "platform": "LinkedIn",
            "confidence": similarity_percent,
            "status": "verified" if similarity_percent >= 50 else "pending",
            "profile": r["profile"]
        })

    return {"success": True, "results": formatted}


@app.post("/scrape-profile")
async def scrape_profile(req: ProfileRequest):
    """Start LinkedIn scraping process and return immediately."""
    try:
        # Log the exact URL being processed
        logger.info(f"🔗 Received LinkedIn URL: {req.profile_url}")
        logger.info(f"🔗 URL type: {type(req.profile_url)}")
        
        # Validate it's a LinkedIn profile URL
        if not req.profile_url or "linkedin.com/in/" not in req.profile_url:
            return {
                "success": False,
                "error": f"Invalid LinkedIn profile URL: {req.profile_url}"
            }
        
        # Start the scraping process in the background (detached)
        logger.info(f"🚀 Starting LinkedIn scrape for: {req.profile_url}")
        
        # Use subprocess.Popen exactly like when running manually
        process = subprocess.Popen(
            [sys.executable, "final_scrape_summary.py", req.profile_url],
            cwd="."
        )
        
        logger.info(f"✅ Scraping process started with PID: {process.pid} for URL: {req.profile_url}")
        
        return {
            "success": True,
            "profile_url": req.profile_url,
            "message": f"LinkedIn scraping started for {req.profile_url}. This will take 2-4 minutes. Check the Backend folder for results.",
            "process_id": process.pid,
            "expected_duration": "2-4 minutes"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to start scraping process: {str(e)}"
        }


@app.get("/scrape-status/{profile_name}")
async def get_scrape_status(profile_name: str):
    """Check if scraping results are available for a profile."""
    try:
        # Look for folders matching the profile name pattern
        current_dir = Path(__file__).parent  # Use the directory where api.py is located
        logger.info(f"🔍 Searching in directory: {current_dir}")
        logger.info(f"🔍 Looking for profile: {profile_name}")
        
        # Clean profile name for folder matching (remove spaces, etc.)
        clean_name = profile_name.replace(" ", "_")
        
        # Try a comprehensive search approach
        matching_folders = []
        
        # Get all directories that look like profile folders (contain timestamps)
        all_profile_folders = list(current_dir.glob("*_*_*"))
        
        # Filter folders that contain any part of the profile name
        name_parts = profile_name.lower().replace("_", " ").split()
        
        for folder in all_profile_folders:
            folder_name_lower = folder.name.lower()
            # Check if folder contains all significant name parts
            matches = 0
            for part in name_parts:
                if len(part) > 2 and (part in folder_name_lower or part.replace("rajgopal", "rajagopal") in folder_name_lower or part.replace("rajagopal", "rajgopal") in folder_name_lower):
                    matches += 1
            
            # If at least half the name parts match, consider it a match
            if matches >= len(name_parts) // 2 and matches > 0:
                matching_folders.append(folder)
        
        logger.info(f"🔍 Found {len(matching_folders)} matching folders: {[f.name for f in matching_folders]}")
        
        if not matching_folders:
            # List all directories for debugging
            all_dirs = [d.name for d in current_dir.iterdir() if d.is_dir()]
            return {
                "success": False,
                "status": "not_found", 
                "message": f"No scraping results found for {profile_name}",
                "name_parts_searched": name_parts,
                "available_directories": all_dirs,
                "search_directory": str(current_dir)
            }
            
        # Use the most recent folder
        latest_folder = max(matching_folders, key=lambda p: p.stat().st_mtime)
        
        summary_file = latest_folder / "final_summary.json"
        activity_file = latest_folder / "activity_posts.json"
        
        if not summary_file.exists():
            return {
                "success": False,
                "status": "in_progress",
                "message": f"Scraping in progress for {profile_name}. Results folder exists but summary not ready yet."
            }
            
        # Load results (only final_summary.json)
        with open(summary_file, "r", encoding="utf-8") as f:
            summary = json.load(f)
        
        return {
            "success": True,
            "status": "completed",
            "profile_name": profile_name,
            "summary": summary,
            "output_folder": str(latest_folder),
            "message": f"Scraping completed for {profile_name}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "status": "error",
            "error": f"Error checking scrape status: {str(e)}"
        }
