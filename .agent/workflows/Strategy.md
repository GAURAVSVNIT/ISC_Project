---
description: Strategic Execution
---

# 🎯 Project Veritas: Strategic Execution

## 1. The "Tri-Stream" Narrative
We are not building "just another classifier." We are building a **Forensic Suite**.
* **Strategy:** Position the tool as a holistic system. Single models fail; a suite of models checking orthogonal vectors (Visual, Semantic, Contextual) is robust. This directly addresses the "Robustness" requirement.

## 2. The "Human-in-the-Loop" Approach
* **Strategy:** Emphasize that the AI is an **analyst**, not a dictator. The "Reasoning Core" (LLM) acts as a synthesizer that presents evidence to the user. This fulfills the "Explainability" deliverable perfectly.

## 3. Demo Strategy (The "Golden Path")
For the hackathon demo, we will not rely on random inputs. We will walk the judges through **three specific, pre-tested scenarios** that show off each stream:
1.  **Scenario A (The Tech Fake):** Upload a high-quality Midjourney image. Show Stream A spiking to 99% Fake.
2.  **Scenario B (The Narrative Fake):** Upload a real, old photo with a breaking news caption. Show Stream C flagging the date mismatch.
3.  **Scenario C (The Attack):**
    * *Step 1:* Upload an "Adversarial Image" that confuses the model (optional).
    * *Step 2:* Turn on "Veritas Shield".
    * *Step 3:* Show the model correctly identifying it. (This proves Robustness).

## 4. API Contract & Data Flow
**Request Endpoint:** `POST /api/v1/analyze`
**Request Body:**
```json
{
  "claim": "Massive protests in Paris started today",
  "media_file": "(Binary File)",
  "enable_defense": true
}
```

**Response Body:**
```json
{
  "verdict": "Misleading",
  "confidence_score": 0.89,
  "explanation": "This image is real but used out of context. Reverse search identifies this image originating from a 2018 event, contradicting the claim that it happened 'today'.",
  "streams": {
    "visual": { "score": 0.12, "status": "Authentic Media" },
    "semantic": { "score": 0.75, "status": "Consistent" },
    "contextual": { "found": true, "earliest_date": "2018-11-24", "origin_label": "Yellow Vest Protests" }
  }
}
```