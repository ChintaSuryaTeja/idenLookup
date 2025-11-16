#  Identity_Lookup  
### AI-Powered LinkedIn Identity Matching System

Identity_Lookup is a production-grade AI system that identifies probable LinkedIn profiles from a single face image.  
It uses state-of-the-art facial recognition (InsightFace), cosine similarity scoring, fuzzy name matching, and a modern React dashboard to deliver fast and accurate identity suggestions.

## ⭐ Core Features

### 🧠 Advanced Facial Recognition  
- Uses **InsightFace buffalo_l** model  
- Generates 512-dimensional facial embeddings  
- High accuracy even with variations in lighting, angle, or quality  

### 🔗 LinkedIn Profile Matching Engine  
- Loads LinkedIn profiles from `profiles.json`  
- Downloads each profile's display picture  
- Generates embeddings for all profiles  
- Computes cosine similarity  
- Produces the **Top-4 most probable matches**  

### 🧩 Smart Fuzzy Name Matching  
- Automatically extracts probable name from the uploaded image filename  
- Uses fuzzy string matching to reduce search scope  
- Speeds up matching + improves accuracy  

### ⚡ Optimized Processing  
- Multithreaded download system  
- Retry-enabled HTTP sessions  
- Temp photo caching  
- Automatic cleanup after execution  

### 🖥️ Modern React Dashboard  
- Built using **React + Vite + Tailwind**  
- Clean upload interface  
- Interactive results display  
- One-click LinkedIn redirection  

### 🔄 Continuous Integration  
A production-ready GitHub Actions workflow ensures:  
- Python backend installs without errors  
- Frontend builds successfully  
- Project is always deploy-ready  

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
## ⚙️ Frontend Setup (React)

### 1️⃣ Navigate to the Frontend directory
```bash
cd frontend
npm i
npm run dev
```
After this step, click on your local port link available in the terminal to access the website

## 🔐 Environment Variables

Create a `.env` file inside the **Backend** folder with the following keys:
```
LINKEDIN_EMAIL=your-email@example.com
LINKEDIN_PASSWORD=your-password
ALLOW_AUTOMATED_LOGIN=True
GOOGLE_API_KEY=your-google-api-key
```



## Usage
- To get to upload page, Just type localhost:you_port_number/upload.
- Select an image and start the data retrieval process.
- After some time the results will be avaialable in dashboard page.



