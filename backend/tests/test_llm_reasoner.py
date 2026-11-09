
import unittest
from backend.core.llm_reasoner import LLMReasoner

class TestLLMReasoner(unittest.TestCase):
    def test_prompt_construction(self):
        """Verify that forensic data is correctly mapped to the XML prompt."""
        reasoner = LLMReasoner()
        
        # Mock Input Data
        results = {
            "visual": {
                "score": 0.99, 
                "status": "Fake", 
                "model": "ConvNeXt-Large",
                "heatmap": "available"
            },
            "semantic": {"score": 0.15, "status": "Inconsistent"},
            "metadata": {
                "verdict": "FAKE",
                "ai_tags": ["Stable Diffusion", "Automatic1111"],
                "security_warning": "Stego-Detected"
            },
            "contextual": {
                "evidence_found": False,
                "summary": "No matching news reports found for 'Alien Invasion in NYC'."
            }
        }
        claim = "This shows an alien invasion."
        
        # Generate Prompt
        prompt = reasoner._construct_prompt(results, claim)
        
        print("\n=== Generated Prompt Preview ===")
        print(prompt)
        print("================================")
        
        # Assertions
        self.assertIn("<claim_investigated>This shows an alien invasion.</claim_investigated>", prompt)
        self.assertIn("<model_used>ConvNeXt-Large</model_used>", prompt)
        self.assertIn("<detected_signatures>Stable Diffusion, Automatic1111</detected_signatures>", prompt)
        self.assertIn("<warning>Stego-Detected</warning>", prompt)
        self.assertIn("<web_search_summary>No matching news reports", prompt)
        
    def test_fallback_structure(self):
        """Verify fallback returns the new structured format."""
        reasoner = LLMReasoner()
        results = {"visual": {"score": 0.88, "status": "Fake"}}
        
        fallback = reasoner._fallback_explanation(results)
        self.assertIn("**Verdict**: Manipulated", fallback)
        self.assertIn("**The Smoking Gun**", fallback)
        self.assertIn("digital 'brushstrokes'", fallback)

if __name__ == "__main__":
    unittest.main()
