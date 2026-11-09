---
description: Team Workflow - 12 Hour Sprint Plan
---
# 🚀 Project Veritas: 12-Hour Sprint Plan (Team of 4)

**Start Time:** 13:00 IST | **Deadline:** 01:00 IST (+1 day)
**Current Status:** Phase 4 (Polish & Testing) - Ahead of Schedule

---

## Team Roles & Branch Assignments

| Member | Role | Branch Name | Focus Area |
|--------|------|-------------|------------|
| **Dev 1** | Backend Lead | `feature/stream-a-visual` | Stream A: Genesis (ConvNeXt) + Video Pipeline |
| **Dev 2** | ML Engineer | `feature/stream-b-xfacta` | Stream B: Semantic (CLIP) + Robust Image Handling |
| **Dev 3** | Full-Stack | `feature/stream-c-context` | Stream C: SerpApi + Reasoning Core (LLM) |
| **Dev 4** | Frontend Lead | `feature/frontend-ui` | Next.js Dashboard + Multimodal Support |

---

## Phase 1: Setup & Infrastructure (Hours 0-2) [COMPLETED]

**Time: 13:00 - 15:00 IST**

### Dev 1 (Backend Lead)

- [x] Initialize FastAPI project structure
- [x] Create `config.py` with environment variables
- [x] Set up CORS and basic `/health` endpoint
- [x] Create Pydantic schemas (`schemas.py`)

### Dev 2 (ML Engineer)

- [x] Clone UniversalFakeDetect repo
- [x] Clone XFacta repo
- [x] Download pretrained weights (Genesis / CLIP)
- [x] Set up conda environment with all dependencies

### Dev 3 (Full-Stack)

- [x] Get SerpApi API key
- [x] Get OpenAI API key
- [x] Create `.env.example` template
- [x] Test API connections

### Dev 4 (Frontend Lead)

- [x] Initialize Next.js 14 project with TypeScript
- [x] Install shadcn/ui, Tailwind, Axios
- [x] Create basic layout and routing structure
- [x] Set up API client (`lib/api.ts`)

---

## Phase 2: Core Development (Hours 2-6) [COMPLETED]

**Time: 15:00 - 19:00 IST**

### Dev 1 (Backend Lead)

- [x] Implement `streams/genesis.py` (Genesis Model integration)
- [x] Implement `defense/art_shield.py` (preprocessing)
- [x] Create `/api/v1/analyze` endpoint skeleton
- [x] **New:** Implement `video_processor.py` (Disk-Based Frame Extraction)

### Dev 2 (ML Engineer)

- [x] Implement `streams/semantic.py` (CLIP integration)
- [x] Set up evidence retrieval pipeline
- [x] Configure reasoning approach
- [x] **Fix:** Robust image loading for Semantic stream

### Dev 3 (Full-Stack)

- [x] Implement `streams/context.py` (SerpApi wrapper)
- [x] Implement `core/llm_reasoner.py` (LLM integration)
- [x] Design system prompt for explanation generation
- [x] Test end-to-end reasoning pipeline

### Dev 4 (Frontend Lead)

- [x] Build `UploadZone.tsx` (Drag & Drop + Image Preview)
- [x] Build `AnalysisDashboard.tsx` (Visual/Semantic/Context Cards)
- [x] Build `VerdictBadge.tsx` (Fake/Real indicator)
- [x] Style with premium dark theme

---

## Phase 3: Integration & Orchestration (Hours 6-9) [COMPLETED]

**Time: 19:00 - 22:00 IST**

### Dev 1 (Backend Lead)

- [x] Implement `core/orchestrator.py` (Async Parallel Streams)
- [x] Connect all 3 streams with `asyncio.gather`
- [x] Add error handling and timeouts
- [x] **Refactor:** Redesign Video Pipeline to use disk-based temp files (Fixes `BytesIO` corruption)

### Dev 2 (ML Engineer)

- [x] Optimize inference speed
- [x] Add confidence score normalization
- [x] **Debug:** Fix `Genesis` SyntaxError and duplicate code

### Dev 3 (Full-Stack)

- [x] Integrate reasoner with stream outputs
- [x] Add structured JSON output parsing
- [x] Test complete backend pipeline (Restored Video/Audio support)

### Dev 4 (Frontend Lead)

- [x] Connect frontend to backend API
- [x] Add loading states and progress indicators
- [x] Build `ShieldToggle.tsx` (Adversarial Defense)
- [x] Add real-time status updates via custom Hook

---

## Phase 4: Polish & Testing (Hours 9-11) [IN PROGRESS]

**Time: 22:00 - 00:00 IST**

### All Team Members

- [x] Merge all PRs to `main` (Resolved `git stash` conflicts)
- [ ] Fix any remaining integration bugs (Video Verification ongoing)
- [ ] Run end-to-end tests

### Dev 1 + Dev 2

- [ ] Prepare 3 demo test cases:
  1. Deepfake image (Genesis catches)
  2. Out-of-context image (SerpApi/Context catches)
  3. Mismatched caption (CLIP/Semantic catches)

### Dev 3 + Dev 4

- [x] Polish UI animations
- [ ] Add confidence gauges
- [x] Test adversarial defense toggle

---

## Success Criteria Checklist

✅ All 3 streams functional (Genesis, Semantic, Context)
✅ Frontend shows verdict + explanation
✅ Adversarial defense toggle works
✅ Video Upload & Analysis (Disk-based pipeline active)
✅ Audio Forensics (Restored)
⬜ 3 demo scenarios verified
⬜ System deployed
