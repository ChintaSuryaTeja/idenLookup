import os
import json
import shutil
import subprocess
import sys
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

TEMP_INPUT = "uploaded_input.jpg"
OUTPUT_JSON = "top_matches.json"

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
