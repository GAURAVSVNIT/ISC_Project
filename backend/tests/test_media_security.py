
import asyncio
import unittest
from unittest.mock import MagicMock, patch, mock_open, AsyncMock

# Mock modules
import sys
sys.modules['backend.streams.genesis'] = MagicMock()
sys.modules['backend.streams.semantic'] = MagicMock()
sys.modules['backend.streams.audio'] = MagicMock()
sys.modules['backend.defense.art_shield'] = MagicMock()
sys.modules['backend.utils.video_processor'] = MagicMock()

from backend.core.orchestrator import Orchestrator

class TestMediaSecurity(unittest.IsolatedAsyncioTestCase):
    
    async def test_audio_security_stego(self):
        """Verify Audio pipeline detects steganography"""
        orch = Orchestrator()
        
        # Mock _run_context_stream (Async) to avoid API calls
        orch._run_context_stream = AsyncMock(return_value={"found": False})
        
        # Mock dependencies
        with patch('backend.utils.metadata_filter.metadata_filter.check') as mock_meta, \
             patch('backend.defense.art_shield.shield.detect_trailing_bytes') as mock_stego, \
             patch('backend.streams.audio.audio_stream.analyze', new_callable=AsyncMock) as mock_analyze:
             
            # Setup Mocks
            mock_meta.return_value = {"should_short_circuit": False, "ai_tags": []}
            mock_stego.return_value = True # Stego DETECTED
            mock_analyze.return_value = {"score": 0.1, "status": "Real"}
            
            # Execute
            result = await orch.process_audio_request(b"fake_audio_bytes", "claim")
            
            # Assert
            print("\nAudio Test Result:", result)
            self.assertIn("security_warning", result["metadata"])
            self.assertEqual(result["metadata"]["security_warning"], "Steganography Detected (Trailing Data)")
            print("✅ Verified: Audio Stego Check worked.")

    async def test_video_security_shield(self):
        """Verify Video pipeline sanitizes extracted frames"""
        orch = Orchestrator()
        
        # Mock extracted file path
        fake_image_path = "temp_frame.jpg"
        
        # PATCH where it is USED, not where it is defined
        with patch('backend.utils.metadata_filter.metadata_filter.check') as mock_meta, \
             patch('backend.core.orchestrator.extract_components', new_callable=AsyncMock) as mock_extract, \
             patch('backend.defense.art_shield.shield.sanitize') as mock_sanitize, \
             patch('os.path.exists') as mock_exists, \
             patch('builtins.open', new_callable=mock_open, read_data=b"raw_frame_bytes") as mock_file, \
             patch('os.remove'): # mute cleanup
            
            # Setup Mocks
            mock_meta.return_value = {"should_short_circuit": False} # Container is clean
            mock_extract.return_value = {"image_path": fake_image_path, "audio_path": None}
            mock_exists.return_value = True
            mock_sanitize.return_value = b"sanitized_frame_bytes"
            
            # Mock recursive process_request call to avoid calling real pipeline
            orch.process_request = AsyncMock()
            orch.process_request.return_value = {"visual": {"score": 0.1}}
            
            # Execute
            await orch.process_video_request(b"fake_video_bytes", "claim")
            
            # Assert
            # 1. Check Metadata was called on CONTAINER bytes
            mock_meta.assert_called_with(b"fake_video_bytes")
            
            # 2. Check Shield was called on FRAME bytes
            mock_sanitize.assert_called_with(b"raw_frame_bytes")
            
            # 3. Check process_request received SANITIZED bytes
            orch.process_request.assert_called_with(
                b"sanitized_frame_bytes", 
                "claim", 
                raw_bytes=b"raw_frame_bytes"
            )
            print("✅ Verified: Video Frame was Sanitized before Analysis.")

if __name__ == "__main__":
    unittest.main()
