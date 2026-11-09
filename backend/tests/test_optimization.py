
import asyncio
import unittest
from unittest.mock import MagicMock, patch

# Mock dependencies before import
import sys
sys.modules['backend.streams.genesis'] = MagicMock()
sys.modules['backend.streams.semantic'] = MagicMock()
sys.modules['backend.streams.context_xfacta'] = MagicMock()
sys.modules['backend.defense.art_shield'] = MagicMock()

# Now import Orchestrator
from backend.core.orchestrator import Orchestrator

class TestOptimization(unittest.IsolatedAsyncioTestCase):
    async def test_short_circuit(self):
        """Verify that AI Metadata triggers Short Circuit and SKIPS heavy streams."""
        orch = Orchestrator()
        
        # Mock Metadata Filter to return "AI DETECTED"
        with patch('backend.utils.metadata_filter.metadata_filter.check') as mock_meta:
            mock_meta.return_value = {
                "should_short_circuit": True,
                "ai_tags": ["Midjourney"]
            }
            
            # Mock the heavy stream
            from backend.streams.genesis import genesis_stream
            genesis_stream.analyze = MagicMock()
            
            # Execute Process Check
            # pass ANY bytes, doesn't matter, mock controls result
            result = await orch.process_request(b"fake_clean_bytes", "test claim", raw_bytes=b"fake_raw_bytes")
            
            # ASSERTIONS
            print("\nTest Result Verdict:", result.get("verdict"))
            print("Cost Optimized Flag:", result.get("cost_optimized"))
            
            # 1. Start Circuit should be TRUE
            self.assertTrue(result.get("cost_optimized"))
            self.assertEqual(result.get("visual", {}).get("status"), "AI-Generated (Metadata)")
            
            # 2. Heavy Model should NOT be called
            genesis_stream.analyze.assert_not_called()
            print("✅ Verified: Heavy Model was NOT called.")

if __name__ == "__main__":
    unittest.main()
