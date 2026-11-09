---
description: Architecture
---

# 🏗️ Project Veritas: Architecture Specification

## 1. High-Level Architecture
The system follows a **decoupled architecture**. The frontend (Next.js) handles user interaction and state, while the backend (FastAPI) serves as the orchestration layer for the heavy AI logic.

* **Frontend:** Next.js 14 (App Router) hosted on Vercel.
* **Backend:** FastAPI (Python 3.10+) hosted on a cloud instance (AWS EC2 / GCP VM / Ngrok for local dev).
* **Communication:** REST API (JSON) over HTTP.
* **AI Engine:** Modular "Tri-Stream" processing pipelines.

## 2. Backend Architecture (The Core)
FastAPI is chosen for its native asynchronous support (`asyncio`), which is critical when running multiple AI models in parallel.

### 2.1 The Core Pipeline (Async Logic)
The system uses an **Orchestrator Pattern**. When a request comes in, the backend spins up three parallel tasks.

**Workflow Logic:**
1.  **Input Handling:** Receive Image/Video + Text Claim + Defense Flag.
2.  **Defense Layer:** If `enable_defense` is True, pass image through ART (Adversarial Robustness Toolbox) for preprocessing (blur/compression) to neutralize adversarial noise.
3.  **Parallel Execution (Tri-Stream):**
    * **Stream A (Visual):** Detects synthetic manipulation.
    * **Stream B (Semantic):** Checks image-text consistency.
    * **Stream C (Contextual):** Performs reverse image search for grounding.
4.  **Aggregation:** Wait for all three streams to return data (`await asyncio.gather`).
5.  **Reasoning Core:** Feed the aggregated evidence into an LLM (GPT-4o) to synthesize a final verdict and explanation.
6.  **Response:** Return a unified JSON object to the frontend.

### 2.2 Folder Structure (Backend)
```bash
veritas-backend/
├── main.py              # Entry point, API routes, CORS config
├── config.py            # Environment variables (API keys)
├── core/
│   ├── orchestrator.py  # Manages the 3 streams async
│   └── llm_reasoner.py  # GPT-4o / Llama integration
├── streams/
│   ├── visual.py        # Stream A: SigLIP/Deepfake detection
│   ├── semantic.py      # Stream B: CLIP analysis
│   └── context.py       # Stream C: SerpApi Reverse Search
├── defense/
│   └── art_shield.py    # Image preprocessing/sanitization
├── schemas.py           # Pydantic models for request/response
└── utils/
    └── video_proc.py    # Frame extraction logic
```

## 3. Frontend Architecture
We use Next.js 14 for server-side rendering (better SEO/performance) and React Server Components.

veritas-frontend/
├── app/
│   ├── layout.tsx       # Global fonts, metadata, providers
│   ├── page.tsx         # Landing page + Upload Hero Section
│   ├── dashboard/       # Main analysis interface
│   │   └── page.tsx
│   └── globals.css      # Tailwind imports
├── components/
│   ├── ui/              # shadcn components (buttons, cards, progress)
│   ├── UploadZone.tsx   # Drag-and-drop area
│   ├── AnalysisCard.tsx # Displays individual stream results
│   ├── VerdictBadge.tsx # The final "Fake/Real" indicator
│   └── ShieldToggle.tsx # The "Adversarial Defense" switch
├── lib/
│   ├── api.ts           # Axios instance configuration
│   └── utils.ts         # Helper functions (class merging)
└── types/
    └── index.ts         # TypeScript interfaces for API responses

