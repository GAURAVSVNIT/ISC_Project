---
description: Tech Stack
---


# 🛠️ Project Veritas: Technology Stack

## 1. Frontend (User Interface)
* **Framework:** Next.js 14 (App Router) - chosen for React Server Components and Vercel optimization.
* **Language:** TypeScript (Strict mode).
* **Styling:** Tailwind CSS + shadcn/ui (for pre-built, professional components like Cards, Badges, and Progress bars).
* **State Management:** React Hooks (`useState`, `useTransition`).
* **HTTP Client:** Axios (for typed API requests and error handling).
* **Icons:** Lucide-React.
* **File Upload:** `react-dropzone`.

## 2. Backend (Core Intelligence)
* **Framework:** FastAPI + Uvicorn (High-performance Async Python web framework).
* **Language:** Python 3.10+.
* **Machine Learning Libraries:**
    * `PyTorch`: For running deep learning models.
    * `Transformers` (Hugging Face): For loading SigLIP and CLIP.
    * `OpenCV`: For video frame extraction and image resizing.
* **Adversarial Defense:** `Adversarial Robustness Toolbox (ART)` or custom `Pillow` filters (Gaussian Blur, JPEG compression).
* **External APIs:**
    * **OpenAI API (GPT-4o):** For the "Reasoning Core" (Generating explanations).
    * **SerpApi:** For programmatic access to Google Reverse Image Search.

## 3. Infrastructure & Deployment
* **Frontend Hosting:** Vercel (Zero-config deployment for Next.js).
* **Backend Hosting:** AWS EC2 (g4dn.xlarge recommended for GPU) OR Google Colab/Ngrok tunnel for hackathon demos.
* **Version Control:** Git / GitHub.