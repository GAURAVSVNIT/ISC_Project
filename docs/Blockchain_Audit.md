# 🔗 Blockchain Audit Trail

## Overview
The Blockchain Audit Trail is a "Truth Layer" integrated into Echelon. It provides an immutable, tamper-evident record of every analysis performed by the system. By linking analysis results using cryptographic hashes (SHA-256), we create a "Chain of Custody" that proves:
1.  **When** an analysis took place (Timestamp).
2.  **What** the verdict was (Data integrity).
3.  **Order** of events (Sequential linking).

## Architecture

### 1. Data Structure (`Block`)
Each record is a "Block" containing:
*   `index`: Sequential ID (0, 1, 2...).
*   `timestamp`: Unix timestamp of the analysis.
*   `data`: The payload (Verdict, Confidence Score, Claim, Image Hash).
*   `previous_hash`: The SHA-256 signature of the *previous* block.
*   `hash`: The SHA-256 signature of *this* block (locking it to the previous one).

### 2. The Chain (Local Ledger)
The ledger is stored locally in `s:/Echelon/ledger.json`.
*   **Genesis Block**: The first block (Block #0) created automatically on system start.
*   **Tamper Evidence**: If an attacker modifies Block #5, the hash of Block #5 changes. Since Block #6 includes `previous_hash` of Block #5, its hash also changes. This domino effect invalidates the entire chain from the point of tampering onwards.

### 3. Integration
*   The `BlockchainLogger` class (`backend/core/blockchain.py`) manages the chain.
*   It is invokved automatically by:
    *   **HTTP API**: `/api/v1/analyze`
    *   **WebSocket API**: `/ws/analyze`
*   **Frontend**: The Dashboard receives a `{ verification: { ... } }` object and displays a `BLOCK #ID` badge.

## Security Levels

### Level 1: Local Tamper-Evident (Current Implementation) 🛡️
*   **Mechanism**: SHA-256 Hash Chaining stored in `ledger.json`.
*   **Security**: Prevents undetected modification of old records.
*   **Trust Model**: "Trust but Verify". The admin controls the file, but cannot alter history without breaking the chain's math.
*   **Status**: **LIVE** ✅

### Level 2: Digital Signatures (Planned) ✍️
*   **Mechanism**: Server signs each block with a private key (RSA/ECDSA).
*   **Security**: Proves *authenticity* of the source (Echelon Server) in addition to integrity.

### Level 3: Public Anchor (Enterprise) ⚓
*   **Mechanism**: Periodically broadcasting the latest Block Hash to a public blockchain (Ethereum/Sepolia/Polygon).
*   **Security**: **Absolute Immutability**. Even the server admin cannot rewrite history because the "Checkpoint" exists on thousands of decentralized nodes.
*   **Implementation**: A simulation script (`backend/scripts/anchor_simulator.py`) demonstrates this workflow.

## Enterprise Feasibility (Merkle Anchoring)
For high-volume enterprise usage (e.g., Social Media platforms), we use **Merkle Root Anchoring**:
1.  Process millions of verifications locally (Level 1).
2.  Aggregate all hashes into a single Merkle Tree Root.
3.  Broadcast *only the Root Hash* to Ethereum once per hour ($0.50/day cost).
4.  **Result**: Users get Ethereum-grade proof for fractions of a cent.

## Usage Guide

### Simulation
To simulate the "Level 3" anchoring process:
```bash
python backend/scripts/anchor_simulator.py
```
This reads your local ledger and simulates a transaction to the Sepolia Testnet.

### Manual Verification
Open `ledger.json`.
1.  Take the `hash` of Block N-1.
2.  Ensure it matches `previous_hash` of Block N.
3.  Re-calculate the SHA-256 of Block N's `json.dumps({index, timestamp, data, previous_hash})`.
4.  It must match `hash`.
