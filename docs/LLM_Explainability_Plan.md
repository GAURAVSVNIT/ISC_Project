# 🧠 LLM Explainability Upgrade Plan

## Goal
Transform the LLM from a "Verdict Generator" into a "Forensic Teacher". The output should explain *why* something is fake using clear, non-technical analogies.

## Proposed Changes to `backend/core/llm_reasoner.py`

### 1. System Prompt Overhaul
*   **Role**: Elevate from "Analyst" to "Expert Witness".
*   **Tone**: Authoritative but educational. "Explain like you are talking to a jury."
*   **Structure Requirement**:
    *   **The Verdict**: One separate bold line.
    *   **The Evidence**: Bullet points contrasting the streams.
    *   **The Explanation**: A simplified analogy (e.g., "Think of this like a digital fingerprint...").

### 2. Data Injection Upgrade (`_construct_prompt`)
*   **Metadata**: Pass specific tag names (e.g., "Software: Adobe Photoshop").
*   **Context**: Pass the actual summary snippet from SerpApi, not just a boolean.
*   **Visual**: Pass the specific model name ("ConvNeXt").

### 3. Example Prompt Template
```text
You are Echelon's Chief Forensic AI.
Your goal is to explain complex deepfake detection results to a non-technical user.

STRUCTURE YOUR RESPONSE AS FOLLOWS:
1.  **Verdict**: [Real/Fake/Suspicious] (Confidence Level)
2.  **Key Evidence**:
    *   [Visual] ...
    *   [Metadata] ...
3.  **Forensic Analysis**:
    (Explain *why* the evidence matters using an analogy. E.g., "The pixel consistency score is low, which is like finding brushstrokes in a photograph.")
```
