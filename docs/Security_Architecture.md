# 🔐 Echelon System Security Architecture
**Version:** 1.0.0
**Date:** Feb 1, 2026

## 1. Security Philosophy: "Defense in Depth"
Echelon employs a multi-layered security approach, assuming that any single layer may be bypassed. We secure the **Infrastructure**, **API**, **Application Logic**, and **Data Persistence** mechanisms independently.

---

## 2. Architecture Overview

### Layer 1: Network & Infrastructure 🛡️
*   **DDoS Protection (Streaming)**:
    *   **Mechanism**: File uploads are handled via `SpooledTemporaryFile`. Large files (>10MB) are spilled to disk, preventing RAM exhaustion attacks (OOM).
    *   **Limit**: Max upload size is hard-capped at 100MB via `Length` header checks.
*   **Rate Limiting (SlowAPI)**:
    *   **Policy**: 10 requests / minute / IP.
    *   **Storage**: In-memory (MVP) / Redis (Production).
    *   **Effect**: Mitigates brute-force attacks and API cost draining.

### Layer 2: API Security (FastAPI) 🚧
*   **Input Validation (Pydantic)**:
    *   Strict typing for all request bodies.
    *   Rejection of malformed JSON payloads.
*   **CORS Policy**:
    *   Restricted to trusted origins (`localhost:3000` in dev).
    *   Prevents browser-based cross-origin attacks.

### Layer 3: Application Logic (The "Veritas" Core) 🧠
*   **Adversarial Defense (ArtShield)**:
    *   **Attack Vector**: Adversarial Examples (Noise).
    *   **Defense**:
        1.  **Gaussian Blur**: Removes high-frequency noise.
        2.  **Re-Encoding**: Destroys fragile pixel perturbations.
        3.  **Resizing**: Breaks grid-based attacks.
*   **Steganography Detection**:
    *   **Attack Vector**: Polyglot files (e.g., JPEG + ZIP).
    *   **Defense**: Checks for "Trailing Bytes" after the EOF marker. Flags suspicious payloads in Metadata.
*   **Prompt Injection Defense**:
    *   **Attack Vector**: "Ignore previous instructions".
    *   **Defense**: `LLMReasoner` uses a strict Regex Allowlist (`[a-zA-Z0-9.,?!]`) for user claims. All other characters are stripped.

### Layer 4: Data Integrity (Blockchain) 🔗
*   **Immutable Audit Trail**:
    *   Every analysis result is hashed (SHA-256) and linked to the previous block.
    *   **Genesis Block**: Hardcoded trust anchor.
    *   **Tamper Evidence**: Any modification to `ledger.json` invalidates all subsequent blocks.

---

## 3. Vulnerability Management

| Vulnerability ID | Description | Status | Mitigation |
| :--- | :--- | :--- | :--- |
| **VULN-001** | Denial of Service (RAM Exhaustion) | ✅ Fixed | Streaming Uploads implemented. |
| **VULN-002** | API Abuse / Cost Draining | ✅ Fixed | SlowAPI Rate Limiting (10/min). |
| **VULN-003** | Prompt Injection (Jailbreak) | ✅ Fixed | Regex Sanitization + System Prompt Hardening. |
| **VULN-004** | Steganography (Data Exfiltration) | ✅ Fixed | Trailing Byte Detection. |
| **VULN-005** | Cross-Site Scripting (XSS) | ✅ Verified | React escapes by default. No `dangerouslySetInnerHTML` found. |

---

## 4. Future Roadmap (Level 4 Security)
1.  **Authentication**: Implement OAuth2 (Google/GitHub) for user tracking.
2.  **Secret Management**: Move `.env` vars to AWS Secrets Manager / Vault.
3.  **Container Security**: Run as non-root user in Docker (Distroless images).
