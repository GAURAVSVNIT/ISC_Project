# 🧠 Explainability Upgrade: Response Format
**Date:** Feb 1, 2026

## Overview
The `LLMReasoner` now acts as an "Expert Witness" rather than a raw data logger. The output is structured to be jury-friendly and educational.

## Output Structure (Markdown)
The API will now return a markdown string with the following sections:

### 1. The Heading
> **Verdict**: Authentic (Confidence: 98%)

### 2. The evidence
> **The Smoking Gun**: No significant manipulation traces found.

### 3. The Breakdown
> **Forensic Breakdown**:
> * **Visuals**: The media lacks the tell-tale signs of generation (Score: 0.02). The noise patterns appear organic...
> * **Context**: Analysis consistent with declared claim...

## Frontend Implementation Guide
*   **Do not** try to parse JSON from the explanation. It is pure Markdown.
*   **Render** directly using `ReactMarkdown` or similar.
*   **Styling**:
    *   **Verdict**: Render in Red (Fake) or Green (Real).
    *   **Smoking Gun**: Render in bold/ambient glow.
