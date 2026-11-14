
import unittest
from unittest.mock import patch, AsyncMock

# Import the real modules (no sys.modules stubs: replacing modules globally leaks
# into every other test file that runs in the same session).
import backend.streams.audio  # noqa: F401  (must be imported so it can be patched below)
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
            self.assertIn("security_warning", result["metadata"])
            self.assertEqual(result["metadata"]["security_warning"], "Steganography Detected (Trailing Data)")

    async def test_video_rejects_unreadable_upload(self):
        """
        The video pipeline must refuse bytes that are not a video instead of
        producing a verdict. (Video-specific behaviour is covered in
        test_video_pipeline.py; the old single-frame + ArtShield path is gone.)
        """
        from backend.utils.video_processor import VideoError

        orch = Orchestrator()
        with self.assertRaises(VideoError):
            await orch.process_video_request(b"fake_video_bytes" * 100, "claim")


if __name__ == "__main__":
    unittest.main()
