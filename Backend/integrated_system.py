#!/usr/bin/env python3
"""
integrated_system.py

Integrated LinkedIn + Facebook Profile Extraction + Facial Recognition + Human Selection + Gemini summarization

Usage examples:
  python integrated_system.py linkedin --input ./linkedin_data --use-profile --user-data-dir "C:/Users/Gayatri/AppData/Local/Google/Chrome/User Data" --profile-dir "Default"
  python integrated_system.py face --image candidate.jpg --name "John Doe"
  python integrated_system.py full --input ./linkedin_data --image candidate.jpg --use-profile --user-data-dir "C:/Users/Gayatri/AppData/Local/Google/Chrome/User Data" --profile-dir "Default"
"""

import os
import re
import json
import time
import logging
import argparse
import requests
import hashlib
import cv2
import numpy as np
import shutil
from tqdm import tqdm
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from difflib import SequenceMatcher
from PIL import Image
from io import BytesIO
import sys

# Third-party imports (ensure installed)
try:
    import google.generativeai as genai
except Exception:
    genai = None

from bs4 import BeautifulSoup
from selenium import webdriver
from dotenv import load_dotenv
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from sklearn.metrics.pairwise import cosine_similarity

# insightface (optional but required for face embedding)
try:
    from insightface.app import FaceAnalysis
except Exception:
    FaceAnalysis = None

from requests.adapters import HTTPAdapter, Retry

# =========================================
# CONFIGURATION & SETUP
# =========================================
load_dotenv()

FACEBOOK_USER = os.getenv("FACEBOOK_EMAIL")
FACEBOOK_PASS = os.getenv("FACEBOOK_PASSWORD")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LINKEDIN_API_KEY = os.getenv("LINKEDIN_API_KEY", "")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "results")
TEMP_DIR = os.path.join(BASE_DIR, "temp_photos")
PROFILES_PATH = os.path.join(BASE_DIR, "profiles.json")  # optional LinkedIn export fallback

SIMILARITY_THRESHOLD = 0.35
DETECTION_SCORE_THRESHOLD = 0.5
MAX_WORKERS = 6

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)

if not FACEBOOK_USER or not FACEBOOK_PASS:
    logging.error("FACEBOOK_EMAIL and FACEBOOK_PASSWORD not found in .env — Facebook features will fail unless provided.")

if GEMINI_API_KEY and genai:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel("gemini-2.0-flash-exp")
    except Exception:
        gemini_model = None
else:
    gemini_model = None

# =========================================
# FACE RECOGNITION ENGINE
# =========================================
class FaceRecognitionEngine:
    """Face embedding and similarity utilities"""
    def __init__(self):
        self.app = None
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[500,502,503,504])
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def initialize(self):
        if self.app is not None:
            return
        if FaceAnalysis is None:
            logging.error("InsightFace not installed. Face functionality will be disabled.")
            return
        logging.info("Initializing InsightFace model...")
        try:
            # Use ctx_id=-1 if you want CPU only
            self.app = FaceAnalysis(name="buffalo_l")
            self.app.prepare(ctx_id=0, det_size=(640,640))
            logging.info("Face model prepared.")
        except Exception as e:
            logging.error(f"Failed to initialize face model: {e}")
            self.app = None

    def get_embedding(self, image_path: str) -> Optional[np.ndarray]:
        if self.app is None:
            self.initialize()
        if self.app is None:
            return None

        img = cv2.imread(image_path)
        if img is None:
            logging.debug(f"Cannot read image: {image_path}")
            return None
        faces = self.app.get(img)
        if not faces:
            logging.debug(f"No faces in image: {image_path}")
            return None
        faces = [f for f in faces if getattr(f, "det_score", 1.0) >= DETECTION_SCORE_THRESHOLD]
        if not faces:
            logging.debug(f"No high-quality faces in: {image_path}")
            return None
        if len(faces) > 1:
            faces.sort(key=lambda x: (x.bbox[2]-x.bbox[0])*(x.bbox[3]-x.bbox[1]), reverse=True)
        return faces[0].embedding

    def compute_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        try:
            return float(cosine_similarity([emb1], [emb2])[0][0])
        except Exception:
            return 0.0

    def download_image(self, url: str, save_path: str) -> bool:
        try:
            if not url:
                return False
            # some URLs are protocol-relative or start with //
            if url.startswith("//"):
                url = "https:" + url
            r = self.session.get(url, timeout=12, headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code == 200 and r.content:
                with open(save_path, "wb") as f:
                    f.write(r.content)
                return True
            return False
        except Exception as e:
            logging.debug(f"Download failed ({url}): {e}")
            return False

# =========================================
# LINKEDIN DATA HANDLER
# =========================================
class LinkedInDataHandler:
    @staticmethod
    def load_profiles(profiles_path: str = PROFILES_PATH) -> List[Dict[str, Any]]:
        if not os.path.exists(profiles_path):
            logging.warning(f"{profiles_path} not found")
            return []
        try:
            with open(profiles_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and "elements" in data:
                data = data["elements"]
            if not isinstance(data, list):
                logging.error("Invalid profiles.json format")
                return []
            logging.info(f"Loaded {len(data)} LinkedIn profiles from {profiles_path}")
            return data
        except Exception as e:
            logging.error(f"Failed to load profiles: {e}")
            return []

    @staticmethod
    def read_metadata(input_dir: str) -> Dict[str, Any]:
        linkedin_data = {"metadata": {}, "profile_text": "", "summary_text": ""}
        metadata_path = os.path.join(input_dir, "metadata.json")
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, "r", encoding="utf-8") as f:
                    linkedin_data["metadata"] = json.load(f)
            except Exception as e:
                logging.error(f"Failed to read metadata.json: {e}")

        profile_txt_path = os.path.join(input_dir, "profile.txt")
        if os.path.exists(profile_txt_path):
            try:
                with open(profile_txt_path, "r", encoding="utf-8") as f:
                    linkedin_data["profile_text"] = f.read()
            except Exception as e:
                logging.error(f"Failed to read profile.txt: {e}")

        summary_path = os.path.join(input_dir, "summary.json")
        if os.path.exists(summary_path):
            try:
                with open(summary_path, "r", encoding="utf-8") as f:
                    s = json.load(f)
                    linkedin_data["summary_text"] = json.dumps(s, indent=2)
            except Exception as e:
                logging.error(f"Failed to read summary.json: {e}")

        return linkedin_data

    @staticmethod
    def extract_person_details(linkedin_data: Dict[str, Any]) -> Dict[str, Any]:
        metadata = linkedin_data.get("metadata", {})
        profile_text = linkedin_data.get("profile_text", "")
        person = {
            "name": None,
            "location": None,
            "current_company": None,
            "headline": None,
            "education": [],
            "skills": [],
            "profile_summary": "",
            "photo_url": None
        }
        # name fields
        for field in ["name","full_name","localizedFirstName","Full Name","fullName"]:
            if field in metadata and metadata[field]:
                person["name"] = metadata[field]
                break
        # fallback from profile text
        if not person["name"] and profile_text:
            for line in profile_text.splitlines()[:6]:
                s = line.strip()
                if s and len(s.split())<=4 and len(s)>3:
                    person["name"] = s
                    break
        # location
        for field in ["location","Location","city","geo_location"]:
            if field in metadata and metadata[field]:
                person["location"] = metadata[field]
                break
        # current company
        for field in ["company","current_company","currentCompany","employer","headline"]:
            if field in metadata and metadata[field]:
                if not person["current_company"] and isinstance(metadata[field], str):
                    person["current_company"] = metadata[field]
        # headline
        for field in ["headline","title","job_title"]:
            if field in metadata and metadata[field]:
                person["headline"] = metadata[field]
                break
        # education
        if "education" in metadata and isinstance(metadata["education"], list):
            for edu in metadata["education"]:
                if isinstance(edu, dict):
                    school = edu.get("school", edu.get("schoolName",""))
                    if school:
                        person["education"].append(school)
        # skills
        if "skills" in metadata and isinstance(metadata["skills"], list):
            person["skills"] = [s for s in metadata["skills"] if isinstance(s,str)][:10]
        # photo url
        for field in ["photo_url","photoUrl","profilePicture","picture","avatar"]:
            if field in metadata and metadata[field]:
                person["photo_url"] = metadata[field]
                break
        if profile_text:
            person["profile_summary"] = profile_text[:500].strip()
        logging.info(f"Extracted person details: {person.get('name')} | {person.get('location')}")
        return person

# =========================================
# FACEBOOK SCRAPER
# =========================================
class FacebookScraper:
    def __init__(self, user_data_dir: str = None, profile_dir: str = None, use_profile: bool = False):
        self.driver = None
        self.use_profile = use_profile
        # default to user's Chrome path if none provided
        self.user_data_dir = user_data_dir or os.path.expanduser(r"C:\Users\Default\AppData\Local\Google\Chrome\User Data")
        self.profile_dir = profile_dir or "Default"

    def launch_browser(self):
        options = Options()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        if self.use_profile and self.user_data_dir:
            # sanitize and ensure path exists (we won't create arbitrary user profile dirs but allow user to pass existing path)
            options.add_argument(f"--user-data-dir={self.user_data_dir}")
            options.add_argument(f"--profile-directory={self.profile_dir}")
            logging.info(f"Using Chrome user profile: {self.user_data_dir} :: {self.profile_dir}")
        else:
            temp_profile = os.path.join(TEMP_DIR, f"chrome_profile_{int(time.time())}")
            os.makedirs(temp_profile, exist_ok=True)
            options.add_argument(f"--user-data-dir={temp_profile}")
            logging.info("Using temporary Chrome profile")

        # Try to be resilient to different ChromeDriver setups:
        try:
            service = Service()
            self.driver = webdriver.Chrome(service=service, options=options)
            # anti-detect JS
            try:
                self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                    "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
                })
            except Exception:
                pass
            logging.info("Browser launched")
            return self.driver
        except Exception as e:
            logging.error(f"Failed to launch Chrome: {e}")
            raise

    def login(self) -> bool:
        if self.driver is None:
            logging.error("Driver not initialized")
            return False
        try:
            # go to facebook and check if logged in by presence of search box or top nav
            self.driver.get("https://www.facebook.com")
            time.sleep(2)
            try:
                # common selectors for logged-in search
                self.driver.find_element(By.XPATH, "//input[contains(@placeholder,'Search') or @aria-label='Search Facebook' or @aria-label='Search']")
                logging.info("Already logged in")
                return True
            except Exception:
                pass

            # try login page
            self.driver.get("https://www.facebook.com/login")
            time.sleep(2)
            # cookie consent
            try:
                cookie_btn = WebDriverWait(self.driver, 4).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Allow all cookies') or contains(., 'Accept All') or contains(., 'Allow') or contains(., 'Accept')]"))
                )
                cookie_btn.click()
                time.sleep(1)
            except Exception:
                pass

            email_input = WebDriverWait(self.driver, 8).until(EC.presence_of_element_located((By.ID, "email")))
            email_input.clear()
            email_input.send_keys(FACEBOOK_USER)
            password_input = self.driver.find_element(By.ID, "pass")
            password_input.clear()
            password_input.send_keys(FACEBOOK_PASS)
            login_button = self.driver.find_element(By.NAME, "login")
            login_button.click()
            time.sleep(4)

            current_url = self.driver.current_url
            if "checkpoint" in current_url or "two_factor" in current_url:
                logging.warning("Two-factor login required. Please complete 2FA in the opened browser window.")
                # wait for manual completion
                for i in range(60):
                    time.sleep(2)
                    try:
                        self.driver.find_element(By.XPATH, "//input[contains(@placeholder,'Search') or @aria-label='Search Facebook' or @aria-label='Search']")
                        logging.info("2FA completed")
                        return True
                    except Exception:
                        continue
                logging.error("2FA timeout")
                return False

            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//input[contains(@placeholder,'Search') or @aria-label='Search Facebook' or @aria-label='Search']"))
            )
            logging.info("Successfully logged in")
            return True

        except Exception as e:
            logging.error(f"Login failed: {e}")
            try:
                self.driver.save_screenshot(os.path.join(OUTPUT_DIR, "fb_login_error.png"))
            except:
                pass
            return False

    def search_top_profiles(self, query: str, limit: int = 30) -> List[Dict[str,str]]:
        """Return up to `limit` candidate profiles (url + displayed name)."""
        candidates = []
        try:
            self.driver.get("https://www.facebook.com")
            time.sleep(2)
            search_bar = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//input[contains(@placeholder,'Search') or @aria-label='Search Facebook' or @aria-label='Search']"))
            )
            search_bar.clear()
            search_bar.send_keys(query)
            search_bar.send_keys(Keys.RETURN)
            time.sleep(3)
            # press People tab if available
            try:
                people_tab = WebDriverWait(self.driver, 4).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'People') or contains(@aria-label, 'People')]"))
                )
                people_tab.click()
                time.sleep(2)
            except Exception:
                pass

            # Scroll & collect anchors
            scrolls = 8
            seen = set()
            for _ in range(scrolls):
                anchors = self.driver.find_elements(By.XPATH, "//a[contains(@href,'facebook.com') and @role='link']")
                for a in anchors:
                    try:
                        href = a.get_attribute("href")
                    except Exception:
                        href = None
                    if not href:
                        continue
                    href = href.split("?")[0].rstrip("/")
                    if href in seen:
                        continue
                    # some exclude patterns
                    if any(p in href.lower() for p in ["/groups/","/events/","/marketplace/","/pages/"]):
                        continue
                    # try to get name
                    name = ""
                    try:
                        # many search anchors include a span or div with the visible name
                        name_el = a.find_element(By.XPATH, ".//span")
                        name = name_el.text.strip()
                    except Exception:
                        try:
                            name = a.text.strip()
                        except Exception:
                            name = ""
                    seen.add(href)
                    candidates.append({"url": href, "name": name})
                    if len(candidates) >= limit:
                        break
                if len(candidates) >= limit:
                    break
                # scroll down
                try:
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                except Exception:
                    pass
                time.sleep(2)
            logging.info(f"Found {len(candidates)} candidates for query '{query}'")
            return candidates[:limit]
        except Exception as e:
            logging.error(f"search_top_profiles error: {e}")
            return candidates

    def _expand_all_content(self):
        show_more_xpaths = [
            "//div[contains(., 'See more')]",
            "//span[contains(text(), 'See more')]",
            "//a[contains(text(), 'See more')]"
        ]
        for _ in range(10):
            clicked = False
            for xpath in show_more_xpaths:
                try:
                    elements = self.driver.find_elements(By.XPATH, xpath)
                    for el in elements[:5]:
                        try:
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", el)
                            time.sleep(0.2)
                            el.click()
                            clicked = True
                            time.sleep(0.4)
                        except Exception:
                            continue
                except Exception:
                    continue
            if not clicked:
                break

    def _scroll_to_bottom(self):
        try:
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            for _ in range(30):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1.2)
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
        except Exception:
            pass

    def _extract_images(self, soup, output_folder, limit=50):
        image_urls = set()
        for img in soup.find_all("img"):
            src = img.get("src")
            if src and ("scontent" in src or "profile" in src or "cdn" in src):
                image_urls.add(src)
        for div in soup.find_all("div", style=True):
            match = re.search(r'url\("([^"]+)"\)', div['style'])
            if match:
                image_urls.add(match.group(1))
        images_folder = os.path.join(output_folder, "facebook_images")
        os.makedirs(images_folder, exist_ok=True)
        for i, url in enumerate(list(image_urls)[:limit], 1):
            try:
                if not url:
                    continue
                if url.startswith("//"):
                    url = "https:" + url
                response = requests.get(url, stream=True, timeout=12, headers={"User-Agent": "Mozilla/5.0"})
                if response.status_code == 200:
                    ext = url.split("?")[0].split(".")[-1]
                    if len(ext) > 4 or "/" in ext:
                        ext = "jpg"
                    img_path = os.path.join(images_folder, f"image_{i}.{ext}")
                    with open(img_path, "wb") as f:
                        for chunk in response.iter_content(1024):
                            f.write(chunk)
            except Exception as e:
                logging.debug(f"Failed to download image {url}: {e}")

    def extract_profile(self, profile_url: str, person: Dict[str, Any]) -> Optional[str]:
        try:
            logging.info(f"Extracting profile: {profile_url}")
            self.driver.get(profile_url)
            time.sleep(4)
            safe_name = re.sub(r'[\\/*?:"<>|]', "", person.get("name") or "unknown")
            folder = os.path.join(OUTPUT_DIR, safe_name)
            os.makedirs(folder, exist_ok=True)
            self._expand_all_content()
            self._scroll_to_bottom()
            screenshot_path = os.path.join(folder, "facebook_profile.png")
            try:
                self.driver.save_screenshot(screenshot_path)
            except Exception:
                pass
            page_html = self.driver.page_source
            with open(os.path.join(folder, "facebook_page.html"), "w", encoding="utf-8") as f:
                f.write(page_html)
            soup = BeautifulSoup(page_html, "html.parser")
            text_content = soup.get_text(separator="\n", strip=True)
            with open(os.path.join(folder, "facebook_page.txt"), "w", encoding="utf-8") as f:
                f.write(text_content)
            self._extract_images(soup, folder, limit=50)
            metadata = {
                "profileUrl": profile_url,
                "actualUrl": self.driver.current_url,
                "searchedPerson": person,
                "extractedAt": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            with open(os.path.join(folder, "facebook_metadata.json"), "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            logging.info(f"Profile extracted to {folder}")
            return folder
        except Exception as e:
            logging.error(f"extract_profile error: {e}")
            return None

    def close(self):
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            logging.info("Browser closed")

# =========================================
# AI SUMMARIZER
# =========================================
class ProfileSummarizer:
    @staticmethod
    def summarize(linkedin_data: Dict, person: Dict, fb_text: str) -> str:
        if not gemini_model:
            logging.warning("Gemini not configured or unavailable. Skipping summarization.")
            return "Summarization unavailable - no API key / gemini_model"

        linkedin_summary = linkedin_data.get("summary_text", "")
        linkedin_profile = linkedin_data.get("profile_text", "")[:3000]

        prompt = f"""
Analyze this person's combined LinkedIn and Facebook profiles for identity verification.

LinkedIn:
Name: {person.get('name')}
Location: {person.get('location')}
Company: {person.get('current_company')}
Headline: {person.get('headline')}
Education: {', '.join(person.get('education', []))}

LinkedIn Summary: {linkedin_summary[:2000]}
LinkedIn Profile: {linkedin_profile}

Facebook Profile Text:
{fb_text[:8000]}

Generate pure JSON with these fields:
1. identity_verification
2. professional_profile
3. personal_information
4. facebook_activity
5. cross_platform_insights
6. summary
"""
        try:
            response = gemini_model.generate_content(prompt)
            summary = response.text.strip()
            # remove markdown fences if any
            summary = re.sub(r'^```json\s*', '', summary)
            summary = re.sub(r'```$', '', summary)
            logging.info("Gemini summary generated")
            return summary
        except Exception as e:
            logging.error(f"Gemini generation error: {e}")
            return f"Error: {e}"

    @staticmethod
    def save_summary(output_folder: str, summary_text: str):
        try:
            match = re.search(r'\{.*\}', summary_text, re.DOTALL)
            if match:
                summary_json = json.loads(match.group(0))
            else:
                summary_json = {"raw_summary": summary_text}
            path = os.path.join(output_folder, "ai_summary.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(summary_json, f, indent=2, ensure_ascii=False)
            logging.info(f"Summary saved to {path}")
        except Exception as e:
            logging.error(f"Failed to save summary: {e}")

# =========================================
# FACIAL MATCHER & SCORER
# =========================================
class FacialMatcher:
    def __init__(self, face_engine: FaceRecognitionEngine, facebook_scraper: FacebookScraper):
        self.face_engine = face_engine
        self.facebook_scraper = facebook_scraper

    @staticmethod
    def fuzzy_ratio(a: str, b: str) -> float:
        if not a or not b:
            return 0.0
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()

    def score_profiles(self, profiles: List[Dict[str,str]], linkedin_person: Dict[str,Any]) -> List[Dict[str,Any]]:
        """
        Score each profile with:
         - Name similarity (20)
         - Location match (20)
         - Company match (10)
         - Face similarity (50)
        """
        scored = []
        ln_name = (linkedin_person.get("name") or "").lower()
        ln_loc = (linkedin_person.get("location") or "").lower()
        ln_comp = (linkedin_person.get("current_company") or "").lower()
        ln_photo = linkedin_person.get("photo_url")

        # Prepare LinkedIn embedding
        linkedin_emb = None
        if ln_photo:
            temp_ln = os.path.join(TEMP_DIR, "linkedin_photo.jpg")
            try:
                ok = self.face_engine.download_image(ln_photo, temp_ln)
                if ok:
                    linkedin_emb = self.face_engine.get_embedding(temp_ln)
                else:
                    logging.debug("Failed to download linkedin photo from URL.")
                    linkedin_emb = None
            except Exception:
                linkedin_emb = None

        # We'll iterate profiles (limit thread concurrency for page loads)
        for p in tqdm(profiles, desc="Scoring profiles", unit="profile"):
            url = p.get("url")
            display_name = p.get("name") or ""
            score = 0.0
            # Name similarity (20)
            name_ratio = self.fuzzy_ratio(ln_name, display_name)
            score += name_ratio * 20

            # Visit page to inspect textual content and profile image
            fb_page_text = ""
            profile_img_url = None
            try:
                try:
                    self.facebook_scraper.driver.get(url)
                except Exception as e:
                    logging.debug(f"Failed to load URL {url}: {e}")
                    continue
                time.sleep(2.5)
                fb_page_text = self.facebook_scraper.driver.page_source.lower()
                # try to find profile image
                try:
                    img_el = self.facebook_scraper.driver.find_element(By.XPATH, "//img[contains(@src,'profile') or contains(@src,'scontent') or contains(@src,'cdn')]")
                    profile_img_url = img_el.get_attribute("src")
                except Exception:
                    profile_img_url = None
            except Exception:
                fb_page_text = ""

            # Location match (20)
            try:
                if ln_loc:
                    # simple token match of first city token
                    token = ln_loc.split(",")[0].strip()
                    if token and token in fb_page_text:
                        score += 20
            except Exception:
                pass

            # Company match (10)
            try:
                if ln_comp and ln_comp in fb_page_text:
                    score += 10
            except Exception:
                pass

            # Face similarity (50)
            face_score = 0.0
            if linkedin_emb is not None and profile_img_url:
                try:
                    temp_fb = os.path.join(TEMP_DIR, f"fb_{hashlib.sha256(url.encode()).hexdigest()[:8]}.jpg")
                    ok = self.face_engine.download_image(profile_img_url, temp_fb)
                    if ok:
                        fb_emb = self.face_engine.get_embedding(temp_fb)
                        if fb_emb is not None:
                            sim = self.face_engine.compute_similarity(linkedin_emb, fb_emb)
                            face_score = sim * 50
                            score += face_score
                except Exception:
                    pass

            scored.append({
                "url": url,
                "name": display_name,
                "score": round(score, 2),
                "name_ratio": round(name_ratio, 3),
                "face_score": round(face_score, 3),
                "profile_img": profile_img_url or ""
            })
        # sort
        scored = sorted(scored, key=lambda x: x["score"], reverse=True)
        return scored

# =========================================
# ORCHESTRATOR: Full pipeline
# =========================================
class ProfileVerificationSystem:
    def __init__(self, use_chrome_profile: bool = False, user_data_dir: Optional[str] = None, profile_dir: Optional[str] = None):
        self.face_engine = FaceRecognitionEngine()
        self.linkedin_handler = LinkedInDataHandler()
        # Pass user profile info into FacebookScraper
        self.facebook_scraper = FacebookScraper(user_data_dir=user_data_dir, profile_dir=profile_dir, use_profile=use_chrome_profile)
        self.summarizer = ProfileSummarizer()
        self.facial_matcher = FacialMatcher(self.face_engine, self.facebook_scraper)
        self.use_chrome_profile = use_chrome_profile
        self.user_data_dir = user_data_dir
        self.profile_dir = profile_dir

    def verify_from_linkedin_data(self, linkedin_dir: str) -> Dict[str,Any]:
        results = {"success": False, "person": {}, "facebook_profile": None, "output_folder": None, "summary": None, "errors": []}
        try:
            logging.info("STEP 1: Loading LinkedIn Data")
            linkedin_data = self.linkedin_handler.read_metadata(linkedin_dir)
            person = self.linkedin_handler.extract_person_details(linkedin_data)
            if not person.get("name"):
                results["errors"].append("No name found in LinkedIn data")
                logging.error("Cannot proceed without name")
                return results
            results["person"] = person
            logging.info(f"Target: {person['name']}")

            logging.info("STEP 2: Launching browser and logging into Facebook")
            self.facebook_scraper.launch_browser()
            login_ok = self.facebook_scraper.login()
            if not login_ok:
                results["errors"].append("Facebook login failed")
                return results

            # STEP 3: Search and retrieve up to 30 candidates
            logging.info("STEP 3: Searching Facebook (retrieve top 30)")
            search_queries = []
            # build queries with preference: name+company, name+location, just name
            if person.get("current_company"):
                search_queries.append(f"{person['name']} {person['current_company']}")
            if person.get("location"):
                search_queries.append(f"{person['name']} {person['location'].split(',')[0]}")
            search_queries.append(person['name'])

            # gather candidates (deduplicating by url)
            candidates = []
            seen = set()
            for q in search_queries:
                if len(candidates) >= 30:
                    break
                try:
                    found = self.facebook_scraper.search_top_profiles(q, limit=30)
                    for f in found:
                        url = f.get("url")
                        if url and url not in seen:
                            seen.add(url)
                            candidates.append(f)
                            if len(candidates) >= 30:
                                break
                except Exception as e:
                    logging.debug(f"search query {q} failed: {e}")
                    continue

            if not candidates:
                results["errors"].append("No Facebook candidates found")
                logging.warning("No candidates")
                return results

            logging.info(f"Collected {len(candidates)} candidate profiles")

            # STEP 4: Score candidates
            logging.info("STEP 4: Scoring candidates (name/location/company/face)")
            # initialize face engine (if available)
            self.face_engine.initialize()
            scored = self.facial_matcher.score_profiles(candidates, person)

            # STEP 5: Display scored list for human selection
            print("\n" + "="*60)
            print("CANDIDATE FACEBOOK PROFILES (sorted by score)")
            print("="*60)
            for i, s in enumerate(scored, 1):
                print(f"{i:2d}. Score: {s['score']:6.2f} | Name: {s['name'] or 'N/A'} | FaceScore: {s['face_score']} | {s['url']}")
            print("\nEnter the number of the profile to scrape (1 - {}), or 0 to abort:".format(len(scored)))

            while True:
                try:
                    choice = int(input("Selection: ").strip())
                    if choice == 0:
                        logging.info("User aborted selection")
                        results["errors"].append("User aborted selection")
                        return results
                    if 1 <= choice <= len(scored):
                        chosen = scored[choice-1]
                        profile_url = chosen["url"]
                        logging.info(f"User selected: {profile_url}")
                        break
                    else:
                        print("Invalid number. Try again.")
                except Exception:
                    print("Enter a number between 1 and {}".format(len(scored)))

            results["facebook_profile"] = profile_url

            # STEP 6: Scrape selected profile fully
            logging.info("STEP 6: Extracting selected profile")
            output_folder = self.facebook_scraper.extract_profile(profile_url, person)
            if not output_folder:
                results["errors"].append("Failed to extract Facebook profile")
                return results
            results["output_folder"] = output_folder

            # Read extracted text for summarization
            fb_text_path = os.path.join(output_folder, "facebook_page.txt")
            fb_text = ""
            if os.path.exists(fb_text_path):
                with open(fb_text_path, "r", encoding="utf-8") as f:
                    fb_text = f.read()

            # STEP 7: Generate Gemini summary (if available)
            if gemini_model:
                logging.info("STEP 7: Generating AI summary with Gemini")
                summary = self.summarizer.summarize(linkedin_data, person, fb_text)
                self.summarizer.save_summary(output_folder, summary)
                results["summary"] = summary
            else:
                logging.info("Gemini unavailable - skipping summarization")
                results["summary"] = "Gemini unavailable or not configured."

            results["success"] = True
            logging.info("Verification complete")
            logging.info(f"Results saved to: {output_folder}")
            return results

        except Exception as e:
            logging.error(f"System error: {e}")
            import traceback
            traceback.print_exc()
            results["errors"].append(str(e))
            return results
        finally:
            try:
                self.facebook_scraper.close()
            except Exception:
                pass

    def verify_with_facial_recognition(self, candidate_image: str, candidate_name: str = None) -> Dict[str,Any]:
        results = {"success": False, "candidate_image": candidate_image, "candidate_name": candidate_name, "matches": [], "errors": []}
        try:
            profiles = self.linkedin_handler.load_profiles()
            if not profiles:
                results["errors"].append("No LinkedIn profiles found (profiles.json)")
                return results
            self.face_engine.initialize()
            # convert profiles into expected format (localizedFirstName / localizedLastName keys)
            matched = []
            for p in profiles:
                # try to extract name and publicProfileUrl
                name = ""
                if isinstance(p, dict):
                    fn = p.get("localizedFirstName","") or p.get("firstName","")
                    ln = p.get("localizedLastName","") or p.get("lastName","")
                    name = f"{fn} {ln}".strip()
                matched.append({"name": name, "profile": p})
            # compute candidate embedding
            query_emb = self.face_engine.get_embedding(candidate_image)
            if query_emb is None:
                results["errors"].append("No face found in candidate image")
                return results
            # compare
            out = []
            for item in matched:
                profile = item["profile"]
                # try to get profile picture url
                img_url = ""
                try:
                    pic_data = profile.get("profilePicture", {}).get("displayImage~", {}).get("elements", []) if isinstance(profile, dict) else []
                    img_url = pic_data[0].get("identifiers", [{}])[0].get("identifier","")
                except Exception:
                    img_url = ""
                if not img_url:
                    continue
                temp_img = os.path.join(TEMP_DIR, f"pr_{hashlib.sha256(img_url.encode()).hexdigest()[:8]}.jpg")
                ok = self.face_engine.download_image(img_url, temp_img)
                if not ok:
                    continue
                emb = self.face_engine.get_embedding(temp_img)
                if emb is None:
                    continue
                sim = self.face_engine.compute_similarity(query_emb, emb)
                out.append({
                    "name": item["name"],
                    "profile_url": profile.get("publicProfileUrl",""),
                    "similarity": round(sim, 4)
                })
            out = sorted(out, key=lambda x: x["similarity"], reverse=True)
            results["matches"] = out[:10]
            results["success"] = len(out) > 0
            # save
            opath = os.path.join(OUTPUT_DIR, "facial_recognition_results.json")
            with open(opath, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            logging.info(f"Facial recognition results saved to: {opath}")
            return results
        except Exception as e:
            logging.error(f"Facial recognition failed: {e}")
            results["errors"].append(str(e))
            import traceback
            traceback.print_exc()
            return results
        finally:
            # cleanup
            try:
                shutil.rmtree(TEMP_DIR, ignore_errors=True)
                os.makedirs(TEMP_DIR, exist_ok=True)
            except Exception:
                pass

    def full_verification_pipeline(self, linkedin_dir: str, candidate_image: str = None) -> Dict[str,Any]:
        results = {"linkedin_facebook_verification": {}, "facial_recognition": {}, "overall_success": False}
        results["linkedin_facebook_verification"] = self.verify_from_linkedin_data(linkedin_dir)
        if candidate_image and os.path.exists(candidate_image):
            person_name = results["linkedin_facebook_verification"].get("person",{}).get("name")
            results["facial_recognition"] = self.verify_with_facial_recognition(candidate_image, person_name)
        results["overall_success"] = (results["linkedin_facebook_verification"].get("success",False) or results["facial_recognition"].get("success",False))
        return results

# =========================================
# CLI
# =========================================
def main():
    parser = argparse.ArgumentParser(description="Integrated Profile Verification System")
    subparsers = parser.add_subparsers(dest="mode")

    linkedin_parser = subparsers.add_parser("linkedin", help="LinkedIn -> Facebook verification (selection + scrape)")
    linkedin_parser.add_argument("--input", required=True, help="LinkedIn data directory (metadata.json, profile.txt)")
    linkedin_parser.add_argument("--use-profile", action="store_true", help="Use existing Chrome profile")
    linkedin_parser.add_argument("--user-data-dir", help="Path to Chrome user data dir")
    linkedin_parser.add_argument("--profile-dir", help="Specific Chrome profile directory (e.g., Default)")

    face_parser = subparsers.add_parser("face", help="Facial recognition only")
    face_parser.add_argument("--image", required=True, help="Candidate image path")
    face_parser.add_argument("--name", help="Candidate name (optional)")

    full_parser = subparsers.add_parser("full", help="Full pipeline")
    full_parser.add_argument("--input", required=True, help="LinkedIn data directory")
    full_parser.add_argument("--image", help="Candidate image path (optional)")
    full_parser.add_argument("--use-profile", action="store_true", help="Use existing Chrome profile")
    full_parser.add_argument("--user-data-dir", help="Path to Chrome user data dir")
    full_parser.add_argument("--profile-dir", help="Specific Chrome profile (e.g., Default)")

    args = parser.parse_args()
    if not args.mode:
        parser.print_help()
        return

    # create system with profile options if provided
    system = ProfileVerificationSystem(
        use_chrome_profile=getattr(args, "use_profile", False),
        user_data_dir=getattr(args, "user_data_dir", None),
        profile_dir=getattr(args, "profile_dir", None)
    )

    try:
        if args.mode == "linkedin":
            # update system's facebook scraper in case CLI provided user-data-dir/profile-dir (ensures runtime override)
            if getattr(args, "user_data_dir", None) or getattr(args, "profile_dir", None) or getattr(args, "use_profile", False):
                system.facebook_scraper.user_data_dir = getattr(args, "user_data_dir", system.facebook_scraper.user_data_dir)
                system.facebook_scraper.profile_dir = getattr(args, "profile_dir", system.facebook_scraper.profile_dir)
                system.facebook_scraper.use_profile = getattr(args, "use_profile", system.facebook_scraper.use_profile)

            res = system.verify_from_linkedin_data(args.input)
            print_summary(res)

        elif args.mode == "face":
            res = system.verify_with_facial_recognition(args.image, args.name)
            print_summary(res)

        elif args.mode == "full":
            if getattr(args, "user_data_dir", None) or getattr(args, "profile_dir", None) or getattr(args, "use_profile", False):
                system.facebook_scraper.user_data_dir = getattr(args, "user_data_dir", system.facebook_scraper.user_data_dir)
                system.facebook_scraper.profile_dir = getattr(args, "profile_dir", system.facebook_scraper.profile_dir)
                system.facebook_scraper.use_profile = getattr(args, "use_profile", system.facebook_scraper.use_profile)

            res = system.full_verification_pipeline(args.input, args.image)
            print_summary(res)

    except KeyboardInterrupt:
        logging.info("Interrupted by user")
    except Exception as e:
        logging.error(f"Critical error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            system.facebook_scraper.close()
        except Exception:
            pass

def print_summary(results: Dict[str,Any]):
    print("\n" + "="*60)
    if not isinstance(results, dict):
        print("No results")
        return
    # decide how to print
    if "overall_success" in results:
        status = "✅ SUCCESS" if results["overall_success"] else "⚠️ PARTIAL/FAILED"
        print(f"Status: {status}")
        if results.get("linkedin_facebook_verification"):
            print("LinkedIn/Facebook verification:")
            lf = results["linkedin_facebook_verification"]
            print(f"  - success: {lf.get('success')}")
            if lf.get("facebook_profile"):
                print(f"  - Profile: {lf.get('facebook_profile')}")
            if lf.get("output_folder"):
                print(f"  - Output: {lf.get('output_folder')}")
            if lf.get("errors"):
                print("  - Errors:")
                for e in lf.get("errors"):
                    print(f"     * {e}")
        if results.get("facial_recognition"):
            fr = results["facial_recognition"]
            print("Facial recognition:")
            print(f"  - success: {fr.get('success')}")
            if fr.get("matches"):
                print("  - Top matches:")
                for m in fr.get("matches")[:5]:
                    print(f"     {m['name']} | {m['similarity']} | {m.get('profile_url')}")
    else:
        status = "✅ SUCCESS" if results.get("success") else "❌ FAILED"
        print(f"Status: {status}")
        if results.get("person"):
            print(f"Person: {results['person'].get('name')}")
        if results.get("facebook_profile"):
            print(f"Profile: {results.get('facebook_profile')}")
        if results.get("output_folder"):
            print(f"Output folder: {results.get('output_folder')}")
        if results.get("errors"):
            print("Errors:")
            for e in results.get("errors"):
                print(f" - {e}")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()