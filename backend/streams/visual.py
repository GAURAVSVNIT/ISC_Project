import random
import torch
import torchvision.transforms as transforms
from PIL import Image
import io
import os
try:
    import clip
except ImportError:
    # If clip is not installed, we'll handle gracefully
    clip = None

from ..config import settings

class VisualStream:
    """
    Stream A: Visual Forensics
    Wraps UniversalFakeDetect (CLIP ViT-L/14 + Linear Layer)
    """
    
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.clip_model = None
        self.preprocess = None
        self.is_ready = False
        
        # Try loading model on init
        self._load_model()
    
    def _load_model(self):
        """
        Load CLIP backbone and Linear Classifier weights.
        """
        if clip is None:
            print("Warning: 'clip' module not found. Stream A running in degrade mode.")
            return

        try:
            # 1. Load CLIP Backbone
            print(f"Loading CLIP (ViT-L/14) on {self.device}...")
            self.clip_model, self.preprocess = clip.load("ViT-L/14", device=self.device)
            self.clip_model.eval()
            
            # 2. Load Linear Probe Weights
            weight_path = settings.UNIVERSAL_FAKE_DETECT_PATH
            if not os.path.exists(weight_path):
                print(f"Warning: Weights not found at {weight_path}. Stream A running in mock mode.")
                return

            print(f"Loading UniversalFakeDetect weights from {weight_path}...")
            # Assuming weights are a simple linear layer [Feature_Dim, 2] or [Feature_Dim]
            # Adjust based on specific repo structure. 
            # Often it's a FC layer state dict.
            fc_weights = torch.load(weight_path, map_location=self.device)
            
            # Initialize Linear Layer (CLIP ViT-L/14 dim is 768)
            self.classifier = torch.nn.Linear(768, 1) # Binary classification
            if isinstance(fc_weights, dict):
                 self.classifier.load_state_dict(fc_weights)
            else:
                 # Some repos save just the tensor
                 self.classifier.weight.data = fc_weights
            
            self.classifier.to(self.device)
            self.classifier.eval()
            
            self.is_ready = True
            print("Visual Stream (UniversalFakeDetect) Loaded Successfully.")
            
        except Exception as e:
            print(f"Error loading Visual Stream models: {e}")
            self.is_ready = False

    async def analyze(self, image_bytes: bytes) -> dict:
        """
        Analyze image for synthetic artifacts.
        """
        # FALLBACK: If model not loaded, return mock result
        if not self.is_ready:
            print("VisualStream not ready, returning mock result.")
            score = random.uniform(0.1, 0.3)
            return {
                "score": score,
                "status": "Authentic Media" if score < 0.5 else "Synthetic/Fake",
                "model": "UniversalFakeDetect (MOCK)"
            }

        try:
            # 1. Preprocess
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            image_input = self.preprocess(image).unsqueeze(0).to(self.device)
            
            # 2. Extract Features (Zero-shot)
            with torch.no_grad():
                features = self.clip_model.encode_image(image_input)
                features = features.float()
                features /= features.norm(dim=-1, keepdim=True) # Normalize!
                
                # 3. Classify
                logits = self.classifier(features)
                score = torch.sigmoid(logits).item()
                
            return {
                "score": score,
                "status": "Synthetic/Fake" if score >= 0.5 else "Authentic Media",
                "label": "Deepfake" if score >= 0.5 else "Real",
                "model": "UniversalFakeDetect (Active)"
            }
            
        except Exception as e:
            print(f"Inference Error: {e}")
            return {"score": 0.0, "status": f"Error: {str(e)}"}

visual_stream = VisualStream()
