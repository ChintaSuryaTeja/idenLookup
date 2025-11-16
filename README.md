#  Identity_Lookup  
### AI-Powered LinkedIn Identity Matching System

Identity_Lookup is a production-grade AI system that identifies probable LinkedIn profiles from a single face image.  
It uses state-of-the-art facial recognition (InsightFace), cosine similarity scoring, fuzzy name matching, and a modern React dashboard to deliver fast and accurate identity suggestions.

## ⭐ Core Features

### AI-Powered Face Recognition  
Leverages state-of-the-art InsightFace (buffalo_l model) to generate high-precision 512-dimensional facial embeddings.  
Ensures reliable identity similarity even with challenging lighting, angles, or image quality.

### Intelligent LinkedIn Profile Matching  
Automatically identifies the most probable LinkedIn profiles by:
- Loading and parsing a structured LinkedIn dataset.
- Downloading profile photos securely and efficiently.
- Generating embeddings for each profile image.
- Ranking profiles using cosine similarity scoring.

The system autonomously returns the **Top-4 highest matching identities**.

### Smart Fuzzy Name Detection  
If the uploaded image contains a filename resembling a person's name (e.g., *vamsi.jpg*), the system:
- Extracts the probable name.
- Applies fuzzy string comparison.
- Narrows down the potential search pool.
- Significantly speeds up and improves matching accuracy.

### High-Performance Processing Pipeline  
Built for efficiency with:
- Multithreaded image downloading (ThreadPoolExecutor).
- Retry-safe HTTP sessions for reliable external image fetching.
- Temporary image caching and automatic cleanup.
- Fully optimized embedding and similarity computation.

### Modern User Interface (React + Vite)  
A clean, intuitive web interface that allows users to:
- Upload a face image instantly.
- Trigger the identity lookup process.
- View similarity results and LinkedIn profile links.
- Navigate through a simple and responsive dashboard.

Designed for a smooth, professional user experience.

### Backend API (FastAPI + Uvicorn)  
A scalable backend service that:
- Handles incoming image data efficiently.
- Integrates InsightFace for on-the-fly embedding generation.
- Performs identity computation and returns structured JSON results.
- Logs and stores outputs in `top_matches.json` for reuse or analysis.

### Continuous Integration (CI) with GitHub Actions  
A production-ready CI pipeline that ensures:
- Backend dependencies install correctly.
- Frontend builds cleanly without errors.
- Automatic validation on every push and pull request.
- Consistent, deployment-ready code quality across the project.

### Secure Environment Configuration  
Sensitive credentials (e.g., LinkedIn session data, API keys) are:
- Stored in a `.env` file.
- Ignored from version control.
- Loaded securely by the backend at runtime.

Ensures data safety and protects user credentials.

## 🚀 Getting Started  
Follow these steps to set up and run the Identity_Lookup project locally.

---

## 📋 Prerequisites
Ensure you have the following installed on your system:

- **Python 3.10+**
- **Node.js (Version 18 or higher)**
- **npm** (or **yarn**)
- **InsightFace model weights** (automatically downloaded on first run)

No database is required — the system works using JSON datasets. (For now)

## 📦 Installation
Post cloning the repository, follow the upcoming steps to run the project

## ⚙️ Backend Setup (Python)

### 1️⃣ Navigate to the Backend directory
```bash
cd Backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

This should get your backend server ready.

## 🔐 Environment Variables

Create a `.env` file inside the **Backend** folder with the following keys:
```
LINKEDIN_EMAIL=your-email@example.com
LINKEDIN_PASSWORD=your-password
ALLOW_AUTOMATED_LOGIN=True
GOOGLE_API_KEY=your-google-api-key
```


## ⚙️ Frontend Setup (React)

### 1️⃣ Navigate to the Frontend directory
```bash
cd frontend
npm i
npm run dev
```
After this step, click on your local port link available in the terminal to access the website



## Usage
- To get to upload page, Just type localhost:you_port_number/upload.
- Select an image and start the data retrieval process.
- After some time the results will be avaialable in dashboard page.



