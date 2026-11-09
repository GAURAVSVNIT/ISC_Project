---
description: Feature Specification
---

# ✨ Project Veritas: Feature Specification

## 1. MVP Features (Must-Haves)
These features satisfy the core "Mandatory Deliverables" of the problem statement.

* **Multi-Modal Input:** Supports Drag-and-Drop for Images (`.jpg`, `.png`) and Videos (`.mp4`).
* **Tri-Stream Analysis:**
    * **Visual Forensics:** Detects pixel-level artifacts indicative of AI generation (Deepfakes).
    * **Semantic Consistency:** Calculates a mathematical score (0-1) representing how well the text caption matches the image content using CLIP.
    * **Contextual Grounding:** Performs automated Reverse Image Search to find the image's origin, earliest publication date, and original context.
* **Explainable AI (XAI):** Does not just say "Fake". Generates a natural language paragraph citing specific evidence (e.g., "Flagged as Misleading because the image dates back to 2018, contradicting the user's claim of 'Today'.").
* **Verdict Dashboard:** clear visualization of the "Truth Score" and individual stream metrics.

## 2. WOW Features (Differentiators)
These features go beyond the basics to impress judges.

* **🛡️ Veritas Shield (Adversarial Defense):** A toggle switch that enables an active defense layer. It preprocesses inputs (Gaussian blur, compression) to neutralize "adversarial perturbations" that hackers use to fool AI models.
* **Real-Time Progress Steps:** Visual feedback showing the user exactly what the AI is doing at every second (e.g., "Accessing Knowledge Graph...", "Analyzing Pixel Frequency...").
* **Confidence Gauges:** Granular progress bars showing the raw confidence of *each* stream, not just the final verdict.