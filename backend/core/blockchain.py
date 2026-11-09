import hashlib
import json
import time
import os
from typing import Dict, Any, List
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class Block:
    index: int
    timestamp: float
    data: Dict[str, Any]
    previous_hash: str
    hash: str

class BlockchainLogger:
    """
    A persistent, immutable ledger for analysis results.
    Uses SHA-256 to link blocks, ensuring tamper evidence.
    """
    
    def __init__(self, ledger_file: str = "ledger.json"):
        self.ledger_file = ledger_file
        self.chain: List[Block] = []
        self._load_chain()

    def _create_genesis_block(self):
        """Creates the first block in the chain."""
        genesis_block = Block(
            index=0,
            timestamp=time.time(),
            data={"event": "Genesis Block", "system": "Echelon AI"},
            previous_hash="0",
            hash="0" # Genesis hash overrides
        )
        genesis_block.hash = self._calculate_hash(genesis_block)
        self.chain.append(genesis_block)
        self._save_chain()

    def _calculate_hash(self, block: Block) -> str:
        """SHA-256 hash of block contents."""
        block_string = json.dumps({
            "index": block.index,
            "timestamp": block.timestamp,
            "data": block.data,
            "previous_hash": block.previous_hash
        }, sort_keys=True)
        
        return hashlib.sha256(block_string.encode()).hexdigest()

    def add_block(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Logs a new analysis result to the blockchain.
        Returns: {index, hash, timestamp}
        """
        last_block = self.chain[-1]
        
        new_block = Block(
            index=last_block.index + 1,
            timestamp=time.time(),
            data=analysis_data,
            previous_hash=last_block.hash,
            hash=""
        )
        new_block.hash = self._calculate_hash(new_block)
        
        self.chain.append(new_block)
        self._save_chain()
        
        logger.info(f"Block #{new_block.index} added to ledger. Hash: {new_block.hash[:8]}...")
        
        return {
            "block_index": new_block.index,
            "block_hash": new_block.hash,
            "timestamp": new_block.timestamp
        }

    def verify_integrity(self) -> bool:
        """Checks if the chain has been tampered with."""
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i-1]
            
            if current.hash != self._calculate_hash(current):
                return False
            if current.previous_hash != previous.hash:
                return False
        return True

    def _save_chain(self):
        """Persists chain to disk."""
        try:
            with open(self.ledger_file, 'w') as f:
                # Convert dataclasses to dicts
                chain_data = [asdict(b) for b in self.chain]
                json.dump(chain_data, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save ledger: {e}")

    def _load_chain(self):
        """Loads chain from disk or initializes genesis."""
        if not os.path.exists(self.ledger_file):
            self._create_genesis_block()
            return

        try:
            with open(self.ledger_file, 'r') as f:
                data = json.load(f)
                self.chain = [Block(**b) for b in data]
        except Exception as e:
            logger.error(f"Failed to load ledger: {e}. Re-initializing.")
            self.chain = []
            self._create_genesis_block()

# Singleton instance
ledger = BlockchainLogger()
