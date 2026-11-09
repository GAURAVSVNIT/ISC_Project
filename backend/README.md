# 🕵️‍♂️ Project Veritas - Backend

The core intelligence layer of the Echelon/Veritas system. Built with **FastAPI** and **Tri-Stream Orchestration**.

## 🚀 Setup & Installation

1.  **Prerequisites:**
    *   Python 3.10+
    *   Git

2.  **Install Dependencies:**
    ```bash
    cd backend
    pip install -r requirements.txt
    ```

3.  **Configuration:**
    *   Create a `.env` file in `backend/` (see `config.py` for variables).
    *   Required Keys: `OPENAI_API_KEY`, `SERPAPI_API_KEY`.

## 🏃‍♂️ Running the Server

```bash
# From the project root
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```
Server will be live at: `http://localhost:8000`
Docs: `http://localhost:8000/docs`

## 🧪 Testing

Run the automated test suite (Pytest):
```bash
# From project root
python -m pytest backend/tests/
```

## 🏗️ Architecture to Date
-   **Orchestrator:** `backend/core/orchestrator.py` - Runs 3 streams in parallel.
-   **Stream A (Visual):** `backend/streams/visual.py` - Fake Image Detection (UniversalFakeDetect).
-   **Defense:** `backend/defense/art_shield.py` - Veritas Shield (Sanitization).
-   **API:** `/api/v1/analyze` - Unified endpoint.

## 👥 Contributors
-   **Dev 1 (Backend Lead):** Infrastructure, Visual Stream, Defense, Orchestrator.
-   **Dev 2 (ML Engineer):** Semantic Stream (XFacta).
-   **Dev 3 (Full Stack):** Context Stream (SerpApi).
