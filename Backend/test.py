# latest.py 
"""
Integrated version of summary_final_refactored_improved.py with full posts extraction logic from the improved posts module.
"""

import os
import sys
import json
import time
import logging
import random
import re
import signal
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Tuple, List, Optional, Union, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# ---- AI client (Gemini) ----
import google.generativeai as genai

# ---- Pydantic schema import (from your file) ----
try:
    from final_summary_schema import FinalSummarySchema  # type: ignore
    _HAS_SCHEMA = True
except Exception:
    FinalSummarySchema = None  # type: ignore
    _HAS_SCHEMA = False

# -------------------------------
# CONFIG (centralized)
# -------------------------------
load_dotenv()

GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_PREFERRED = os.getenv("GEMINI_PREFERRED", "models/gemini-2.5-pro")
BASE_OUTPUT_DIR = Path(os.getenv("BASE_OUTPUT_DIR", "")) or Path.cwd() / "output"
CHROMEDRIVER_PATH = os.getenv("CHROMEDRIVER_PATH", "")
COOKIES_PATH = Path.home() / ".linkedin_cookies.json"  # avoids Desktop permissions issues
PREFER_USER_DATA_DIR = os.getenv("PREFER_USER_DATA_DIR", "True").lower() in ("1", "true", "yes")
USER_DATA_DIR = os.getenv("USER_DATA_DIR", "")
MAX_SUMMARIZE_WORKERS = int(os.getenv("MAX_SUMMARIZE_WORKERS", "2"))
ALLOW_AUTOMATED_LOGIN = os.getenv("ALLOW_AUTOMATED_LOGIN", "False").lower() in ("1", "true", "yes")
SUMMARY_CHUNK_MAX = int(os.getenv("SUMMARY_CHUNK_MAX", "40000"))

COOKIES_PATH.parent.mkdir(parents=True, exist_ok=True)

def expand_path(p: Union[str, Path]) -> Path:
    p = Path(p) if p else Path()
    return p.expanduser().resolve() if str(p) else p

BASE_OUTPUT_DIR = expand_path(BASE_OUTPUT_DIR)
COOKIES_PATH = expand_path(COOKIES_PATH)
if CHROMEDRIVER_PATH:
    CHROMEDRIVER_PATH = expand_path(CHROMEDRIVER_PATH)
else:
    CHROMEDRIVER_PATH = None

# -------------------------------
# Logging: console + rotating file
# -------------------------------
LOG_DIR = BASE_OUTPUT_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
logger = logging.getLogger("summary_refactor_improved")
logger.setLevel(logging.INFO)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(ch)

try:
    from logging.handlers import RotatingFileHandler
    fh = RotatingFileHandler(LOG_DIR / "summary_refactor.log", maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8")
    fh.setLevel(logging.INFO)
    fh.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(fh)
except Exception:
    logger.debug("RotatingFileHandler not available; continuing with console-only logging.")

# -------------------------------
# Validate Gemini client & configure
# -------------------------------
if not GEMINI_API_KEY:
    logger.error("GOOGLE_API_KEY missing in environment (.env). Aborting.")
    raise RuntimeError("GOOGLE_API_KEY missing in environment (.env)")

try:
    genai.configure(api_key=GEMINI_API_KEY)
except Exception as e:
    logger.exception("Failed to configure google.generativeai client: %s", e)

# -------------------------------
# Utility functions
# -------------------------------
def set_file_permissions_owner_only(path: Path):
    try:
        if os.name == "posix":
            path.chmod(0o600)
        else:
            path.chmod(path.stat().st_mode & ~0o222)
    except Exception:
        logger.debug("Could not set strict file permissions for %s", path)

def validate_profile_url(url: str) -> bool:
    if not isinstance(url, str) or not url.strip():
        return False
    url = url.strip()
    pattern = r"^https://([a-z]{2,3}\.)?linkedin\.com/in/[A-Za-z0-9\-_]+/?$"
    return re.match(pattern, url) is not None

NOISE_KEYWORDS = [
    "About", "Accessibility", "Talent Solutions", "Careers", "Marketing Solutions",
    "Privacy & Terms", "Ad Choices", "Advertising", "Sales Solutions", "Mobile",
    "Small Business", "Safety Center", "Questions?", "People also viewed", "Visit our Help Center",
    "Manage your account and privacy", "Recommendation transparency", "messaging overlay",
    "See more", "Show more", "People also viewed"
]

def preprocess_text(text: str) -> str:
    text = re.sub(r'\r', '\n', text)
    lines = [ln.strip() for ln in text.splitlines() if len(ln.strip()) > 3]
    lines = [ln for ln in lines if not any(k.lower() in ln.lower() for k in NOISE_KEYWORDS)]
    seen = set()
    filtered = []
    for ln in lines:
        if ln not in seen:
            filtered.append(ln)
            seen.add(ln)
    logger.info("Preprocessed text -> %d lines.", len(filtered))
    return "\n".join(filtered)

def chunk_text(text: str, max_chars: int = SUMMARY_CHUNK_MAX) -> List[str]:
    if len(text) <= max_chars:
        return [text]
    chunks = []
    cur = ""
    for line in text.split("\n"):
        if len(cur) + len(line) + 1 < max_chars:
            cur += line + "\n"
        else:
            chunks.append(cur)
            cur = line + "\n"
    if cur:
        chunks.append(cur)
    logger.info("Split text into %d chunks.", len(chunks))
    return chunks

# -------------------------------
# Gemini model selection & robust summarization
# -------------------------------
def choose_gemini_model(preferred: str = GEMINI_PREFERRED) -> str:
    try:
        models = genai.list_models()
        generate_models = [m.name for m in models if "generateContent" in (m.supported_generation_methods or [])]
        if preferred in generate_models:
            logger.info("Using preferred Gemini model: %s", preferred)
            return preferred
        for candidate in (
            "models/gemini-pro-latest",
            "models/gemini-flash-latest",
            "models/gemini-2.5-flash",
            "models/gemini-2.5-pro",
        ):
            if candidate in generate_models:
                logger.info("Falling back to available model: %s", candidate)
                return candidate
        if generate_models:
            logger.info("No preferred found; using %s", generate_models[0])
            return generate_models[0]
    except Exception:
        logger.exception("Could not list Gemini models; falling back to configured preferred model.")
    return preferred

GEMINI_MODEL = choose_gemini_model()

def summarize_chunk_with_gemini(text: str, model_name: str = GEMINI_MODEL, retries: int = 5) -> Dict[str, str]:
    prompt = f"""
Summarize the following LinkedIn profile text into structured JSON
with dynamic sections including relevant professional info such as 'personal_info', 'experience', 'education', 'skills', 'projects', and 'activity'.
Respond ALWAYS with valid JSON (object or array) when possible. Do NOT invent facts not present in the text.

Profile text:
<<<
{text}
>>>
"""
    attempt = 0
    while attempt < retries:
        attempt += 1
        try:
            if not hasattr(genai, "GenerativeModel"):
                raise RuntimeError("google.generativeai client missing GenerativeModel. Check package.")
            model = genai.GenerativeModel(model_name)
            resp = model.generate_content(prompt)
            summary_text = getattr(resp, "text", str(resp)).strip()
            if not summary_text:
                raise ValueError("Empty response from Gemini.")
            return {"summary_text": summary_text}
        except Exception as e:
            backoff = min(30, (2 ** attempt) + random.random())
            logger.warning("Gemini attempt %d/%d failed: %s — retrying in %.1fs", attempt, retries, e, backoff)
            time.sleep(backoff)
    logger.error("Gemini summarization failed after %d attempts.", retries)
    return {"error": "Gemini summarization failed after retries"}

def clean_and_parse_jsonish(text: str) -> Union[dict, list]:
    cleaned = re.sub(r"```json|```", "", text).strip()
    try:
        return json.loads(cleaned)
    except Exception:
        m = re.search(r"(\{[\s\S]*\})", cleaned)
        if m:
            try:
                return json.loads(m.group(1))
            except Exception:
                pass
    return {"summary_raw": cleaned}

# -------------------------------
# Selenium driver & helpers
# -------------------------------
def make_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-infobars")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.7444.60 Safari/537.36"
    )

    try:
        service = Service(CHROMEDRIVER_PATH) if CHROMEDRIVER_PATH else Service()
        driver = webdriver.Chrome(service=service, options=options)
    except WebDriverException as e:
        logger.exception("Chrome WebDriver initialization failed: %s", e)
        raise
    try:
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument",
                               {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"})
    except Exception:
        pass
    logger.info("Chrome WebDriver initialized.")
    return driver

def load_cookies(driver: webdriver.Chrome) -> bool:
    if not COOKIES_PATH.exists():
        logger.info("No cookies file found at %s", COOKIES_PATH)
        return False
    try:
        driver.get("https://www.linkedin.com")
        with COOKIES_PATH.open("r", encoding="utf-8") as f:
            cookies = json.load(f)
        for c in cookies:
            try:
                cookie = {"name": c.get("name"), "value": c.get("value"), "path": c.get("path", "/")}
                if ".linkedin.com" in c.get("domain", ""):
                    cookie["domain"] = ".linkedin.com"
                driver.add_cookie(cookie)
            except Exception:
                continue
        logger.info("Cookies loaded.")
        return True
    except Exception as e:
        logger.warning("Failed to load cookies: %s", e)
        return False

def save_cookies(driver: webdriver.Chrome, path: Path = COOKIES_PATH) -> None:
    try:
        cookies = driver.get_cookies()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(cookies, f, indent=2)
        set_file_permissions_owner_only(path)
        logger.info("Cookies saved to %s", path)
    except Exception as e:
        logger.warning("Could not save cookies: %s", e)

# -------------------------------
# Human-like scrolling
# -------------------------------
def human_scroll_and_clicks(driver: webdriver.Chrome, scrolls: int = 6):
    for _ in range(scrolls):
        driver.execute_script("window.scrollBy(0, window.innerHeight * 0.3);")
        time.sleep(0.4 + random.random() * 0.6)
    try:
        buttons = driver.find_elements(By.XPATH, "//button[contains(., 'See more') or contains(., 'Show more')]")
        for b in buttons:
            try:
                driver.execute_script("arguments[0].scrollIntoView(true);", b)
                time.sleep(0.2 + random.random() * 0.3)
                driver.execute_script("arguments[0].click();", b)
                time.sleep(0.3)
            except Exception:
                continue
    except Exception:
        pass

def human_scroll(driver: webdriver.Chrome, scrolls: int = 10):
    for _ in range(scrolls):
        driver.execute_script("window.scrollBy(0, window.innerHeight * 0.8);")
        time.sleep(0.6 + random.random())

def safe_filename(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", name).strip("_") or "Unknown"

# -------------------------------
# Extract profile content
# -------------------------------
def extract_profile(driver: webdriver.Chrome, url: str) -> Tuple[Path, str, str]:
    driver.get(url)
    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "main")))
    time.sleep(2)
    human_scroll(driver, 10)
    name = driver.find_element(By.TAG_NAME, "h1").text.strip()
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator="\n", strip=True)

    folder = BASE_OUTPUT_DIR / f"{safe_filename(name)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    folder.mkdir(parents=True, exist_ok=True)
    with open(folder / "page.html", "w", encoding="utf-8") as f:
        f.write(html)
    logger.info("Profile extracted: %s", name)
    return folder, name, text

# -------------------------------
# Gemini summarization wrapper
# -------------------------------
def summarize_with_gemini(text: str) -> dict:
    summary_raw = summarize_chunk_with_gemini(text)
    if "summary_text" in summary_raw:
        parsed = clean_and_parse_jsonish(summary_raw["summary_text"])
        return parsed
    return summary_raw
    

# -------------------------------
# ================================
# Extract posts (full code from posts module)
# ================================
def extract_posts(driver, profile_url, folder, max_scrolls=30, scroll_pause=1.5):
    """
    Extract LinkedIn posts with improved mention/hashtag/media detection, repost handling,
    and automatic filling of empty fields.
    """
    from bs4 import BeautifulSoup
    import re, json, os, time, random, logging

    posts_url = profile_url.rstrip("/") + "/recent-activity/all/"
    logging.info(f"🔍 Fetching posts from: {posts_url}")
    driver.get(posts_url)
    time.sleep(3)

    # Scroll dynamically to load all posts
    last_height = driver.execute_script("return document.body.scrollHeight")
    scrolls = 0
    while scrolls < max_scrolls:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause + random.random() * 0.5)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
        scrolls += 1

    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    posts = []
    seen_texts = set()  # prevent duplicates

    post_divs = soup.find_all("div", class_=lambda c: c and "update-components-text" in c)

    for div in post_divs:
        try:
            post_text = div.get_text(" ", strip=True)
            if not post_text or post_text in seen_texts:
                continue
            seen_texts.add(post_text)

            # 🔹 Post link
            link_tag = div.find_parent("a", href=True)
            post_link = None
            if link_tag:
                href = link_tag["href"]
                post_link = href if href.startswith("http") else f"https://www.linkedin.com{href}"

            # 🔹 Repost detection
            repost_container = div.find_parent("div", class_=lambda c: c and "feed-shared-reshared-update" in c)
            is_repost = bool(repost_container)
            reposted_from = None
            original_author = "Unknown"
            if is_repost:
                author_tag = repost_container.find("span", class_=lambda c: c and "feed-shared-actor__name" in c)
                if author_tag:
                    original_author = author_tag.text.strip()
                    reposted_from = original_author

            # 🔹 Posted date
            date_elem = div.find_previous("span", string=re.compile(r"ago|day|month|year", re.I))
            posted_date = date_elem.get_text(strip=True) if date_elem else ""

            # 🔹 Hashtags
            hashtags = []
            hashtags += re.findall(r"#(\w+)", post_text)  # normal hashtags
            hashtags += re.findall(r"hashtag\s+#\s*(\w+)", post_text, flags=re.I)  # 'hashtag # DevOps'
            hashtags = list(set(hashtags))

            # 🔹 Mentions (handles @tags + name-like patterns)
            mentions = []
            mentions += re.findall(r"@([\w.-]+)", post_text)
            tail_text = post_text[-150:]
            name_mentions = re.findall(r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+){0,2})\b", tail_text)
            stopwords = {"The", "This", "That", "With", "And", "For", "To", "A", "An", "It", "By", "Stay", "All"}
            mentions += [m for m in name_mentions if m not in stopwords]
            mentions = list(set(mentions))

            # 🔹 Media URLs
            media_links = [img["src"] for img in soup.find_all("img") if img.get("src")]
            media_links += [vid["src"] for vid in soup.find_all("video") if vid.get("src")]

            # 🔹 Engagement counts
            likes = comments = reposts_count = 0
            engagement_block = div.find_parent("div", class_=lambda c: c and "social-details-social-counts" in c)
            if engagement_block:
                text = engagement_block.get_text(" ", strip=True)
                likes_match = re.search(r"(\d[\d,]*)\s+like", text, re.I)
                comments_match = re.search(r"(\d[\d,]*)\s+comment", text, re.I)
                reposts_match = re.search(r"(\d[\d,]*)\s+repost", text, re.I)
                likes = int(likes_match.group(1).replace(",", "")) if likes_match else 0
                comments = int(comments_match.group(1).replace(",", "")) if comments_match else 0
                reposts_count = int(reposts_match.group(1).replace(",", "")) if reposts_match else 0

            # 🔹 Fill missing or empty fields
            if not posted_date:
                posted_date = "Unknown"
            if not media_links:
                media_links = ["No media attached"]
            if not post_link:
                post_link = posts_url
            if not hashtags:
                hashtags = ["None"]
            if not mentions:
                mentions = ["None"]
            if likes is None:
                likes = 0
            if comments is None:
                comments = 0
            if reposts_count is None:
                reposts_count = 0
            if not original_author:
                original_author = "Unknown"
            if reposted_from is None and is_repost:
                reposted_from = "Original post unavailable"

            posts.append({
                "post_text": post_text,
                "posted_date": posted_date,
                "is_repost": is_repost,
                "original_author": original_author,
                "reposted_from": reposted_from,
                "hashtags": hashtags,
                "mentions": mentions,
                "media_links": media_links,
                "likes": likes,
                "comments": comments,
                "reposts": reposts_count,
                "link": post_link
            })

        except Exception as e:
            logging.warning(f"Failed to parse post: {e}")
            continue

    # ✅ Save to file
    with open(os.path.join(folder, "activity_posts.json"), "w", encoding="utf-8") as f:
        json.dump(posts, f, indent=2, ensure_ascii=False)

    logging.info(f"✅ Extracted {len(posts)} unique posts.")
    return posts

# -------------------------------
# MAIN function
# -------------------------------
def main(profile_url: str):
    """Main orchestration: login → extract profile → Gemini summarization → posts → final_summary.json"""
    if not validate_profile_url(profile_url):
        raise ValueError("Provided profile_url is not a recognized LinkedIn /in/ URL.")
    BASE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # -----------------------------
    # Local helper: safe signal exit
    # -----------------------------
    def _setup_signal_handlers(driver_container):
        def handle_sigint(sig, frame):
            print("\nGracefully shutting down WebDriver...")
            driver = driver_container.get("driver")
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass
            sys.exit(0)
        signal.signal(signal.SIGINT, handle_sigint)

    # -----------------------------
    # Local helper: manual login wait
    # -----------------------------
    def wait_for_manual_login(driver, timeout=300):
        """Wait up to timeout seconds for user to complete login manually."""
        import time
        start = time.time()
        while time.time() - start < timeout:
            if "feed" in driver.current_url.lower():
                print("✅ Manual login detected, saving cookies...")
                save_cookies(driver)
                return
            time.sleep(3)
        raise TimeoutError("Manual login timeout reached — please log in manually in Chrome window.")

    # -----------------------------
    # Local helper: create final Gemini summary
    # -----------------------------
    def create_summary(folder: Path, cleaned_text: str):
        """Combine all text into one Gemini summary JSON and validate if schema exists."""
        logger.info("Creating final Gemini summary...")
        summary_raw = summarize_with_gemini(cleaned_text)
        if not summary_raw:
            return {"error": "Gemini summary failed"}

        parsed = summary_raw if isinstance(summary_raw, dict) else {"summary_raw": str(summary_raw)}
        if _HAS_SCHEMA and FinalSummarySchema:
            try:
                validated = FinalSummarySchema(**parsed)
                with open(folder / "final_summary_validated.json", "w", encoding="utf-8") as f:
                    f.write(validated.model_dump_json(indent=2))
                logger.info("Validated final_summary.json via Pydantic schema.")
                return validated.model_dump()
            except Exception as e:
                logger.warning("Validation failed: %s", e)
        return parsed

    # -----------------------------
    # Start pipeline
    # -----------------------------
    driver = None
    driver_container = {"driver": None}

    try:
        driver = make_driver()
        driver_container["driver"] = driver
        _setup_signal_handlers(driver_container)

        # -------------------------
        # Session restoration / login
        # -------------------------
        logged_in = False
        if load_cookies(driver):
            driver.get("https://www.linkedin.com/feed/")
            time.sleep(2)
            try:
                driver.find_element(By.XPATH, "//a[contains(@href, '/in/')]")
                logged_in = True
            except NoSuchElementException:
                logged_in = False

        if not logged_in:
            LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL")
            LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")
            if ALLOW_AUTOMATED_LOGIN and LINKEDIN_EMAIL and LINKEDIN_PASSWORD:
                try:
                    logger.info("Attempting automated login via credentials in .env ...")
                    driver.get("https://www.linkedin.com/login")
                    driver.find_element(By.ID, "username").send_keys(LINKEDIN_EMAIL)
                    driver.find_element(By.ID, "password").send_keys(LINKEDIN_PASSWORD)
                    driver.find_element(By.XPATH, "//button[@type='submit']").click()
                    time.sleep(5)
                    save_cookies(driver)
                    logged_in = True
                except Exception as e:
                    logger.warning("Automated login failed: %s", e)
            if not logged_in:
                logger.info("Waiting for manual login...")
                wait_for_manual_login(driver)
                logged_in = True

        # -------------------------
        # Extract profile
        # -------------------------
        folder, name, raw_text = extract_profile(driver, profile_url)

        # -------------------------
        # Text cleaning + chunk summarization
        # -------------------------
        cleaned_text = preprocess_text(raw_text)
        chunks = chunk_text(cleaned_text)

        logger.info("Generating Gemini summaries for %d chunks...", len(chunks))
        for i, chunk in enumerate(chunks, start=1):
            try:
                summary_chunk = summarize_with_gemini(chunk)
                chunk_file = folder / f"chunk_{i}_summary.txt"
                with open(chunk_file, "w", encoding="utf-8") as f:
                    # Save only Gemini’s structured summary, not raw chunk text
                    if isinstance(summary_chunk, dict):
                        f.write(summary_chunk.get("summary_text") or json.dumps(summary_chunk, indent=2))
                    else:
                        f.write(str(summary_chunk))
                logger.info("Saved Gemini summary → %s", chunk_file.name)
            except Exception as e:
                logger.warning("Chunk %d summarization failed: %s", i, e)

        # -------------------------
        # Create final summary + extract posts
        # -------------------------
        parsed_summary = create_summary(folder, cleaned_text)
        posts = extract_posts(driver, profile_url, folder)

        # -------------------------
        # Merge posts + save final_summary.json
        # -------------------------
        try:
            if isinstance(parsed_summary, list):
                parsed_summary_to_save = parsed_summary[0] if parsed_summary and isinstance(parsed_summary[0], dict) else {}
            elif isinstance(parsed_summary, dict):
                parsed_summary_to_save = parsed_summary
            else:
                parsed_summary_to_save = {}

            # parsed_summary_to_save["activity"] = posts

            final_path = folder / "final_summary.json"
            if final_path.exists():
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                alt_path = folder / f"final_summary_{ts}.json"
                with open(alt_path, "w", encoding="utf-8") as f:
                    json.dump(parsed_summary_to_save, f, indent=2, ensure_ascii=False)
                logger.info("Existing summary detected; saved new file to %s", alt_path)
            else:
                with open(final_path, "w", encoding="utf-8") as f:
                    json.dump(parsed_summary_to_save, f, indent=2, ensure_ascii=False)
                logger.info("Saved → %s", final_path)
        except Exception as e:
            logger.warning("Failed to attach posts to summary: %s", e)
            with open(folder / "activity_posts.json", "w", encoding="utf-8") as f:
                json.dump(posts, f, indent=2, ensure_ascii=False)

        logger.info("✅ Completed successfully. All outputs saved in: %s", folder)

    finally:
        try:
            if driver:
                driver.quit()
        except Exception:
            logger.debug("Driver quit error ignored during cleanup.")

# -------------------------------
# ENTRY POINT
# -------------------------------
if __name__ == "__main__":
    test_profile = "https://www.linkedin.com/in/pradeeprajagopal/"
    main(test_profile)
