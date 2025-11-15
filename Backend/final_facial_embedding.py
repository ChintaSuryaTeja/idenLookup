import os
import json
import cv2
import numpy as np
import sys
import time
import logging
import requests
import re
from tqdm import tqdm
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from difflib import SequenceMatcher
from sklearn.metrics.pairwise import cosine_similarity
from insightface.app import FaceAnalysis
from requests.adapters import HTTPAdapter, Retry
import shutil

# =========================================
# CONFIGURATION
# =========================================

# IMPORTANT: Use dynamic working directory so FastAPI subprocess works
BASE_DIR = os.getcwd()
print("MODEL BASE_DIR =", BASE_DIR) 

PROFILES_PATH = os.path.join(BASE_DIR, "profiles.json")
COOKIES_PATH = os.path.join(BASE_DIR, "cookies.json")
OUTPUT_JSON = os.path.join(BASE_DIR, "top_matches.json")
TEMP_DIR = os.path.join(BASE_DIR, "temp_photos")

SIMILARITY_THRESHOLD = 0.35
DETECTION_SCORE_THRESHOLD = 0.5
MAX_WORKERS = 5

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)

# =========================================
# UTILS
# =========================================
def load_profiles() -> List[Dict[str, Any]]:
    if not os.path.exists(PROFILES_PATH):
        logging.error("❌ profiles.json not found.")
        return []

    try:
        with open(PROFILES_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict) and "elements" in data:
            data = data["elements"]
            with open(PROFILES_PATH, "w", encoding="utf-8") as f2:
                json.dump(data, f2, indent=2)

        return data
    except:
        logging.error("❌ Failed to load profiles.json")
        return []


def create_session() -> requests.Session:
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1)
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


# =========================================
# FACE MODEL
# =========================================
def init_face_model() -> FaceAnalysis:
    app = FaceAnalysis(name="buffalo_l")
    app.prepare(ctx_id=-1, det_size=(640, 640))  # CPU MODE (important fix)
    return app


def get_face_embedding(app: FaceAnalysis, image_path: str) -> Optional[np.ndarray]:
    img = cv2.imread(image_path)
    if img is None:
        logging.error(f"[ERROR] Cannot read image: {image_path}")
        return None

    faces = app.get(img)
    if not faces:
        logging.warning(f"⚠ No face detected in {image_path}")
        return None

    faces = [f for f in faces if getattr(f, "det_score", 1.0) >= DETECTION_SCORE_THRESHOLD]
    if not faces:
        logging.warning(f"⚠ No high-quality face detected in {image_path}")
        return None

    faces.sort(key=lambda x: (x.bbox[2]-x.bbox[0])*(x.bbox[3]-x.bbox[1]), reverse=True)
    return faces[0].embedding


def compute_similarity(emb1: np.ndarray, emb2: np.ndarray) -> float:
    sim = cosine_similarity([emb1], [emb2])[0][0]
    return float(sim) if not np.isnan(sim) else 0.0


# =========================================
# MAIN PIPELINE
# =========================================
def main() -> None:
    logging.info("🚀 Face Matching Started")

    # Read image path
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        image_path = input("Enter the path of the candidate image: ").strip()

    logging.info(f"📸 Processing image: {image_path}")

    if not os.path.exists(image_path):
        logging.error(f"❌ Image does NOT exist: {image_path}")
        return

    profiles = load_profiles()
    if not profiles:
        logging.error("❌ No profiles found.")
        return

    # Init model
    app = init_face_model()
    query_emb = get_face_embedding(app, image_path)
    if query_emb is None:
        logging.error("❌ No face embedding extracted from input image.")
        return

    os.makedirs(TEMP_DIR, exist_ok=True)
    session = create_session()
    results = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_map = {}

        for p in profiles:
            pic_data = p.get("profilePicture", {}).get("displayImage~", {}).get("elements", [])
            if not pic_data:
                continue

            img_url = pic_data[0].get("identifiers", [{}])[0].get("identifier")
            if not img_url:
                continue

            save_path = os.path.join(TEMP_DIR, f"{p.get('localizedFirstName','unknown')}.jpg")
            future_map[executor.submit(download_compare, session, app, query_emb, img_url, save_path, p)] = p

        for future in tqdm(as_completed(future_map), total=len(future_map), desc="🔎 Matching"):
            result = future.result()
            if result:
                results.append(result)

    results = sorted(results, key=lambda x: x["similarity"], reverse=True)
    results = [r for r in results if r["similarity"] >= SIMILARITY_THRESHOLD][:4]

    logging.info(f"📝 Final Matches: {results}")

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    logging.info(f"💾 Saved to {OUTPUT_JSON}")

    shutil.rmtree(TEMP_DIR, ignore_errors=True)
    logging.info("🧹 Temp cleaned")


def download_compare(session, app, query_emb, url, save_path, profile):
    try:
        r = session.get(url, timeout=10)
        if r.status_code != 200:
            return None

        with open(save_path, "wb") as f:
            f.write(r.content)

        emb = get_face_embedding(app, save_path)
        if emb is None:
            return None

        sim = compute_similarity(query_emb, emb)

        return {
            "name": f"{profile.get('localizedFirstName','')} {profile.get('localizedLastName','')}".strip(),
            "profile": profile.get("publicProfileUrl", ""),
            "similarity": round(sim, 4)
        }

    except:
        return None


print(" PYTHON SCRIPT STARTED ")
print("Received sys.argv =", sys.argv)

main()
