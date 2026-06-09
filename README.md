# ⚡ AI Lead Generation & Personalized Outreach Agent

An autonomous, end-to-end AI system designed to identify businesses with a weak online presence, research them, score their opportunity value, and generate hyper-personalized cold outreach emails.

---

## ✨ Key Features

- **🎯 Intelligent Discovery:** Automatically finds businesses without websites using the Google Places API, with dynamic neighborhood-level scanning for maximum coverage.
- **🔍 Deep Enrichment:** Uses **Firecrawl** to scour Yelp, social media (Facebook, Instagram, LinkedIn), and search results to find business owners, emails, and detailed descriptions.
- **🧠 AI-Powered Analysis:** Leverages **Google Gemini 3.1 Flash** (via OpenRouter failover) to analyze business gaps, score leads (1-10), and identify specific pain points a website can solve.
- **✉️ Hyper-Personalized Outreach:** Generates compelling, context-aware cold emails tailored to the business's specific situation and needs.
- **📊 Real-time Pipeline Tracking:** A modern Next.js dashboard that tracks the progress of the multi-agent pipeline in real-time via Server-Sent Events (SSE).
- **🚀 One-Click Outreach:** Review, edit, regenerate with different tones (Friendly, Professional, Casual), and send emails directly through the platform via Resend.

---

## 🏗️ Architecture & Tech Stack

The project follows a decoupled, async-first architecture:

### Backend (Python)
- **Framework:** [FastAPI](https://fastapi.tiangolo.com/) (Async/Await)
- **AI Orchestration:** Custom multi-agent system (Discovery, Scraper, Analyzer, Outreach).
- **LLM Service:** Multi-provider support (OpenRouter primary, Gemini direct failover).
- **Discovery:** Google Places API + Dynamic Neighborhood search (Nominatim).
- **Scraping:** Firecrawl API for structured web data extraction.
- **Database:** Supabase (PostgreSQL) with Row Level Security (RLS).
- **Email:** Resend.com for reliable email delivery.

### Frontend (TypeScript)
- **Framework:** [Next.js 16](https://nextjs.org/) (App Router)
- **Styling:** Tailwind CSS v4
- **Animations:** Framer Motion for interactive UI and staggered reveals.
- **Authentication:** Supabase Auth 
- **State Management:** React Hooks + Real-time SSE for pipeline updates.

---

## 🚀 Setup & Installation

### 1. Prerequisites
- Python 3.11+
- Node.js 18+
- API Keys: Google Gemini (or OpenRouter), Firecrawl, Google Places, Supabase, Resend.

### 2. Backend Setup
```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate | Unix: source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env # Update with your keys
uvicorn main:app --reload
```

### 3. Frontend Setup
```bash
cd frontend
npm install
# Create .env.local with NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

---

