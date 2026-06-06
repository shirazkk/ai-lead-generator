# ⚡ AI Lead Generation & Personalized Outreach Agent

An autonomous, AI-powered system designed to identify businesses with a weak online presence, research them, score their opportunity value, and generate hyper-personalized cold outreach emails.

---

## 🏗️ Architecture Overview

This project utilizes a decoupled architecture to ensure scalability and maintainability:

*   **Frontend:** [Next.js 16](https://nextjs.org/) (App Router), TypeScript, Tailwind CSS v4, and Framer Motion for a modern, responsive UI.
*   **Backend:** [FastAPI](https://fastapi.tiangolo.com/) (Python) for robust, async-first API handling.
*   **AI Brain:** Google Gemini 2.0 Flash via the `google-generativeai` SDK.
*   **Services:** Serper.dev (Search), Playwright (Scraping), Supabase (PostgreSQL), and Resend.com (Email).

---

## 🛠️ Prerequisites

Before you begin, ensure you have the following installed on your machine:

*   **Python:** 3.11+
*   **Node.js:** 18+
*   **Environment Variables:** You will need API keys for:
    *   `GEMINI_API_KEY`
    *   `SERPER_API_KEY`
    *   `SUPABASE_URL` / `SUPABASE_KEY`
    *   `RESEND_API_KEY`

---

## 🚀 Setup & Installation

### 1. Project Cloning

```bash
git clone <repository-url>
cd ai_lead_generator
```

### 2. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# Unix/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Configuration:
# Copy the example env file and update with your credentials
cp .env.example .env

# Run the backend
python main.py
```

### 3. Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install

# Configuration:
# Create a .env.local file with your backend URL
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Run the development server
npm run dev
```

The application will be accessible at:
*   **Frontend:** `http://localhost:3000`
*   **Backend API:** `http://localhost:8000`
*   **API Documentation (Swagger):** `http://localhost:8000/docs`

---

## 📘 Documentation & References

For in-depth technical details, architecture decisions, and development guidelines, refer to the following files:

| File | Description |
| :--- | :--- |
| [`GEMINI.md`](./GEMINI.md) | **Core Architecture, Conventions, and Workflow.** |
| [`AI_Lead_Agent_PRD.md`](./AI_Lead_Agent_PRD.md) | Full Project Requirements & Specifications. |
| [`BACKEND_TESTING_GUIDE.md`](./BACKEND_TESTING_GUIDE.md) | Comprehensive backend testing procedures. |

---

## 🧪 Testing

For a complete list of test cases and manual testing curls, please refer to `BACKEND_TESTING_GUIDE.md`.

*   **Health Check:** `GET http://localhost:8000/health`
*   **Pipeline Test:** `POST http://localhost:8000/api/search`
